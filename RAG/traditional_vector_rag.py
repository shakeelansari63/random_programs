from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import SecretStr

# Using Ollama with OpenAI API Spec
LLM_BASE_URL = "http://localhost:11434/v1"
LLM_API_KEY = SecretStr("ollama")
LLM_MODEL = "gemma4:31b-cloud"
EMBEDDING_MODEL = "embeddinggemma:latest"

# Local Files
KNOWLEDGE_FILE = Path(__file__).parent / "understanding-mutual-funds.pdf"
CHROME_STORE = Path(__file__).parent / "chroma_db"

# LLM and Embedding Models
llm = ChatOpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    model=LLM_MODEL,
    temperature=0,
)

embeddings = OpenAIEmbeddings(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    model=EMBEDDING_MODEL,
    check_embedding_ctx_length=False,
)

# Read PDF Files
loader = PyPDFLoader(KNOWLEDGE_FILE)
documents = loader.load()

# Split Documents into Chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
chunks = text_splitter.split_documents(documents)

# Create Chroma DB Vector Store
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=str(CHROME_STORE),
)

# Create Retriever for vector search
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# Create Prompt Template
prompt = ChatPromptTemplate.from_template("""
Answer the question based on the context below.
Note: Provide a definitive answer quoting the precise page numbers utilized to answer question.
Context: {context}
Question: {input}
Answer:
""")


# Join function to combine retrieved documents
def join_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | join_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Run the RAG
if __name__ == "__main__":
    print("Traditional Vector RAG — Interactive QnA (type 'exit' to quit)\n")
    while True:
        query = input("You: ")
        if query.lower() in ("exit", "quit"):
            break
        result = rag_chain.invoke(query)
        print(f"RAG: {result}\n")
