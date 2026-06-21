import os

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-openai-api-key")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

loader = PyPDFLoader("understanding-mutual-funds.pdf")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)

vector_store = Chroma.from_documents(
    documents=chunks, embedding=embeddings, persist_directory="./chroma_db"
)

retriever = vector_store.as_retriever(search_kwargs={"k": 3})

prompt = ChatPromptTemplate.from_template("""
Answer the question based on the context below.
Context: {context}
Question: {input}
Answer:
""")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


rag_chain = (
    {"context": retriever | format_docs, "input": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

if __name__ == "__main__":
    print("Traditional Vector RAG — Interactive QnA (type 'exit' to quit)\n")
    while True:
        query = input("You: ")
        if query.lower() in ("exit", "quit"):
            break
        result = rag_chain.invoke(query)
        print(f"RAG: {result}\n")
