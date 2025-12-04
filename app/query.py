import argparse
import os
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_postgres import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


load_dotenv()


OLLAMA_URL = os.getenv("OLLAMA_URL")
DB_CONNECTION = os.getenv("DB_CONNECTION")


def query_agent(query):
    # 1. Connect to DB
    print(f"> Connecting to DB...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_URL)
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="documents",
        connection=DB_CONNECTION,
        use_jsonb=True,
    )
    retriever = vector_store.as_retriever()
    print(f"> Connected to DB.")

    # 2. Prepare LLM
    print(f"> Preparing LLM...")
    llm = ChatOllama(model="mistral", base_url=OLLAMA_URL)

    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    # 3. Run Chain
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    print(f"> Thinking...")
    response = rag_chain.invoke(query)
    print(f"> Response: {response}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG CLI Tool: Query the agent.")

    parser.add_argument("query", help="The query to ask the agent.")

    args = parser.parse_args()

    query_agent(args.query)
