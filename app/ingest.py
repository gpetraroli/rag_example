import os
import sys
import argparse
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_postgres import PGVector

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
DB_CONNECTION = os.getenv("DB_CONNECTION")

def process_document(file_path):
    print(f"> PROCESSING: {file_path}")

    # 1. Load the document
    print(f"> Loading document...")
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    loader = UnstructuredMarkdownLoader(file_path)
    docs = loader.load()
    print(f"> Loaded {len(docs)} documents.")

    # 2. Split the document into chunks
    print(f"> Splitting document into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    print(f"> Split into {len(splits)} chunks.")

    # 3. Embend
    print("> Generating vectors...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_URL)

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="documents",
        connection=DB_CONNECTION,
        use_jsonb=True,
    )
    print(f"> Generated {len(splits)} vectors.")

    # 4. Store the vectors
    vector_store.add_documents(splits)
    print(f"> Stored {len(splits)} vectors.")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG CLI Tool: Ingest a file and store it in the vector database.")

    parser.add_argument("file", help="Path to the markdown file")

    args = parser.parse_args()

    process_document(args.file)
