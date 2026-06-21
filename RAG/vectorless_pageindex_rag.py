import json
import os
from typing import Dict, List, Optional

from langchain.agents import create_agent
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# 1. Setup the Model
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
# We need a strong reasoning model (like gpt-4o) to handle tree generation and execution
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 2. Load the PDF
loader = PyPDFLoader("understanding-mutual-funds.pdf")
pages = loader.load()
page_db: Dict[int, str] = {i + 1: page.page_content for i, page in enumerate(pages)}

# -------------------------------------------------------------
# STAGE 1: Dynamic & Recursive PageIndex Tree Construction
# -------------------------------------------------------------


# Define the exact recursive schema for PageIndex nodes using Pydantic
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
        description="A comprehensive, detailed structural summary of what is discussed in this page range to aid future reasoning."
    )
    sub_nodes: List["PageIndexNode"] = Field(
        default=[],
        description="Array of child sub-nodes for nested sub-sections (recursive structure)",
    )


# This updates Pydantic to allow the recursive definition referencing itself
PageIndexNode.model_rebuild()


class PageIndexTree(BaseModel):
    root: PageIndexNode


def generate_page_index_tree(pages_data: Dict[int, str]) -> str:
    """
    Rounds up the document layout and uses an LLM to evaluate the text structural data,
    recursively mapping out the document hierarchy into a true PageIndex Tree.
    """
    print("🤖 Analyzing document structure to build dynamic PageIndex Tree...")

    # Create a lightweight metadata layout representation for the LLM to inspect first
    document_layout_overview = ""
    for page_num, content in pages_data.items():
        # First 300 characters usually contain headings, titles, or section context
        document_layout_overview += (
            f"--- Page {page_num} Header Snippet ---\n{content[:300].strip()}\n\n"
        )

    indexing_prompt = ChatPromptTemplate.from_template("""
    You are a structural document indexing engine. Your job is to transform a document's layout into a hierarchical, recursive PageIndex Tree.

    Here are the top heading snippets across all pages of the document:
    {layout_overview}

    Analyze how this document is organized. Group pages into parent sections (Chapters/Major Sections) and nested child sub_nodes (Sub-sections or standalone important tables/appendices).
    For each node, write a clear, reasoning-focused 'summary' highlighting what knowledge is contained there.

    Return the output precisely matching the requested JSON schema structure.
    """)

    # Force the LLM to output structured JSON mapping strictly to our Pydantic PageIndex model
    structured_llm = llm.with_structured_output(PageIndexTree)
    indexing_chain = indexing_prompt | structured_llm

    result = indexing_chain.invoke({"layout_overview": document_layout_overview})

    # Return it as a clean JSON string to place into the RAG environment's context window
    return json.dumps(result.model_dump(), indent=2)


# Generate our dynamic index
dynamic_tree_context = generate_page_index_tree(page_db)
print("✅ PageIndex Tree generated dynamically!")


# -------------------------------------------------------------
# STAGE 2: Reasoning-Based RAG Execution Loop
# -------------------------------------------------------------


# Create the page content retrieval tool
class FetchPageInput(BaseModel):
    start_page: int = Field(
        description="The starting page number of the node segment to fetch."
    )
    end_page: int = Field(
        description="The ending page number of the node segment to fetch."
    )


def fetch_pages_content(start_page: int, end_page: int) -> str:
    """Retrieves raw text content across a span of pages mapping to an index node."""
    output = []
    start = max(1, start_page)
    end = min(len(page_db), end_page)

    for page_num in range(start, end + 1):
        content = page_db.get(page_num, "Page not found.")
        output.append(f"--- CONTENT OF PAGE {page_num} ---\n{content}\n")
    return "\n".join(output)


fetch_tool = StructuredTool.from_function(
    func=fetch_pages_content,
    name="fetch_pages_content",
    description="Use this tool to pull the raw text of specific pages after evaluating summaries in the PageIndex tree structure.",
    args_schema=FetchPageInput,
)

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

agent = create_agent(
    model=llm,
    tools=[fetch_tool],
    system_prompt=system_prompt,
    debug=True,
)


# -------------------------------------------------------------
# STAGE 3: Run the RAG Query
# -------------------------------------------------------------
if __name__ == "__main__":
    print("Vectorless PageIndex RAG — Interactive QnA (type 'exit' to quit)\n")
    while True:
        query = input("You: ")
        if query.lower() in ("exit", "quit"):
            break
        response = agent.invoke({"messages": [HumanMessage(content=query)]})
        print(f"RAG: {response['messages'][-1].content}\n")
