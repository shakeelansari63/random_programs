import json
from pathlib import Path
from typing import Dict, List

from langchain.agents import create_agent
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, SecretStr

# Using Ollama with OpenAI API Spec
LLM_BASE_URL = "http://localhost:11434/v1"
LLM_API_KEY = SecretStr("ollama")
LLM_MODEL = "gemma4:31b-cloud"  # "gpt-oss:20b-cloud"

# Local Files
KNOWLEDGE_FILE = Path(__file__).parent / "understanding-mutual-funds.pdf"

# LLM and Embedding Models
llm = ChatOpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    model=LLM_MODEL,
    temperature=0,
)

# Read PDF Files
loader = PyPDFLoader(KNOWLEDGE_FILE)
documents = loader.load()
page_db: Dict[int, str] = {i + 1: page.page_content for i, page in enumerate(documents)}


# Define Schema for PageIndex Node
class PageIndexNode(BaseModel):
    node_id: str = Field(
        description="Unique identifier for the node, e.g., '0001', '0002'"
    )
    title: str = Field(
        description="Human-readable title or label of the section/chapter"
    )
    start_page: int = Field(description="The starting page number of this section")
    end_page: int = Field(description="The ending page number of this section")
    summary: str = Field(
        description="A detailed summary of what is discussed in this segment."
    )
    sub_nodes: List["PageIndexNode"] = Field(
        default=[], description="Nested child sub-nodes"
    )


# This is needed as we have PageIndexNode references within PageIndexNode
PageIndexNode.model_rebuild()


# Method to Build leaf nodes of page index
def build_leaf_nodes(pages_data: Dict[int, str], chunk_size: int = 5) -> List[dict]:
    """
    Step 1: Loop through the document sequentially in small page blocks.
    This protects the context window from blowing up.
    """
    leaf_nodes = []
    total_pages = len(pages_data)

    leaf_prompt = ChatPromptTemplate.from_template("""
    You are a document analyzer. Summarize the structural and informational content of pages {start_page} to {end_page}.
    Identify the main chapter names, sections, or topics covered here.

    Raw Content:
    {text_content}

    Return a comprehensive summary of this specific page range. Include key headings or tables found.
    """)

    leaf_chain = leaf_prompt | llm

    # Process pages in blocks of `chunk_size`
    for start in range(1, total_pages + 1, chunk_size):
        end = min(start + chunk_size - 1, total_pages)

        # Combine text for the current chunk
        chunk_text = ""
        for p in range(start, end + 1):
            chunk_text += f"--- PAGE {p} ---\n{pages_data[p]}\n\n"

        print(f"   ↳ Summarizing pages {start} to {end}...")
        summary_response = leaf_chain.invoke(
            {"start_page": start, "end_page": end, "text_content": chunk_text}
        )

        # Append as a basic primitive node
        leaf_nodes.append(
            {"start_page": start, "end_page": end, "summary": summary_response.content}
        )

    return leaf_nodes


# Build a PageIndex Tree from leaf nodes
def merge_leaves_into_tree(leaf_nodes: List[dict]) -> str:
    """
    Step 2: Take the compiled micro-summaries and recursively merge them
    into a structured hierarchical JSON tree.
    """
    merge_prompt = ChatPromptTemplate.from_template("""
    You are an expert document architect. Your task is to take a flat list of localized page range summaries and organize them into a clean, hierarchical, recursive PageIndex Tree.

    Combine adjacent ranges that belong to the same logical topics/chapters into parent nodes, and nest individual sections inside them as sub_nodes.
    When Generating the PageIndexNode Parent by combining 2 or more adjacent leaf nodes, make sure to appropriately update summary, title, start page and end page range values on parent node.

    Flat List of Page Summaries:
    {leaf_nodes_json}

    Produce a complete root-level PageIndexNode JSON object mapping to the requested schema layout.
    Respond with only the JSON object, no additional text.
    No explanation, no additional commentary, no extra words.
    Do not surround the JSON object in markdown code blocks or quotes.

    Sample Output:
    {{
        "node_id": "001",
        "title": "...",
        "start_page": xx,
        "end_page": yy,
        "summary": "...",
        "sub_nodes": [
            {{
                "node_id": "002",
                "title": "...",
                "start_page": xxx,
                "end_page": yyy,
                "summary": "... ...",
                "sub_nodes": [ ... ]
            }},
            ...
        ]
    }}
    """)

    structured_llm = llm.with_structured_output(PageIndexNode)
    merge_chain = merge_prompt | structured_llm

    # Convert our list of leaves to JSON strings for the LLM to process
    result = merge_chain.invoke({"leaf_nodes_json": json.dumps(leaf_nodes, indent=2)})

    final_pageindex_tree = json.dumps(result.model_dump(), indent=2)
    print(f"PageIndex Tree: {final_pageindex_tree}\n")
    return final_pageindex_tree


# Build the PageIndex Tree
flat_leaf_data = build_leaf_nodes(page_db, chunk_size=5)
dynamic_tree_context = merge_leaves_into_tree(flat_leaf_data)
print("✅ Iterative PageIndex Tree built successfully!")


# Now Create a tool for fetching pages content by starting and ending page numbers
@tool
def fetch_pages_content(start_page: int, end_page: int) -> str:
    """
    Use this tool to pull the raw text of specific pages after evaluating summaries in the PageIndex tree structure.
    """
    output = []
    start = max(1, start_page)
    end = min(len(page_db), end_page)

    for page_num in range(start, end + 1):
        content = page_db.get(page_num, "Page not found.")
        output.append(f"--- CONTENT OF PAGE {page_num} ---\n{content}\n")
    return "\n".join(output)


# Setup Agent system prompt embedding the dynamically built index tree
system_prompt = f"""You are an advanced reasoning-based RAG assistant operating on a PageIndex platform.
You do not use vector embeddings or semantic similarity matching. Instead, you dynamically evaluate a hierarchical document structure.

Below is the dynamically generated, JSON-based Table of Contents (PageIndex tree) for this document. It contains node IDs, hierarchical child sub-nodes, page boundaries, and recursive summaries.

{dynamic_tree_context}

Your Workflow Strategy:
1. Examine the user's question and map it conceptually against the 'summary' properties within the hierarchical nodes and sub_nodes above.
2. Trace the index tree to isolate which node or child sub_node is uniquely positioned to hold the ground truth.
3. Call the `fetch_pages_content` tool for the specific `start_page` and `end_page` coordinates assigned to that node.
4. If the raw content you read instructs you to seek context elsewhere (e.g., 'see statistical breakdowns on page 24'), cross-reference it back to your PageIndex tree to locate that page range, and fetch those pages recursively.
5. Provide a definitive answer quoting the precise node paths and page numbers utilized.
"""

# Initialize the Agent Executor loop
tools = [fetch_pages_content]
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
)

# Run the RAG
if __name__ == "__main__":
    print("Vectorless RAG — Interactive QnA (type 'exit' to quit)\n")
    while True:
        query = input("You: ")
        if query.lower() in ("exit", "quit"):
            break
        result = agent.invoke({"messages": [{"role": "user", "content": query}]})
        print(f"RAG: {result['messages'][-1].content}\n")
