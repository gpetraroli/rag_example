import os
import sys
import argparse
import base64
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_postgres import PGVector
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.messages import HumanMessage


load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL")
DB_CONNECTION = os.getenv("DB_CONNECTION")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

def split_markdown_document(file_path: str) -> list[Document]:
    """ Split a markdown document into chunks """

    loader = TextLoader(file_path)
    docs = loader.load()

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""],
    )

    splits = []

    for doc in docs:
        md_header_splits = markdown_splitter.split_text(doc.page_content)

        chunk_splits = text_splitter.split_documents(md_header_splits)

        # Preserve the original document metadata
        for chunk in chunk_splits:
            chunk.metadata.update(doc.metadata)

        splits.extend(chunk_splits)

    return splits

def split_text_document(file_path: str) -> list[Document]:
    """ Split a text document into chunks """

    loader = TextLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    splits = text_splitter.split_documents(docs)

    return splits

def split_pdf_document(file_path: str) -> list[Document]:
    """ Split a pdf document into chunks """

    loader = PyPDFLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    splits = text_splitter.split_documents(docs)

    return splits

def split_image(file_path: str) -> list[Document]:
    """ Transform an image into a text and split it into chunks """
    
    llm = ChatOllama(model="llava", base_url=OLLAMA_URL)

    base64_image = base64.b64encode(open(file_path, "rb").read()).decode("utf-8")

    message = HumanMessage(
        content=[
            {"type": "text", "text": "Describe this image in extreme detail. Include text found in the image, visual layout, and key objects."},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"},
        ]
    )

    response = llm.invoke([message])
    description = response.content

    doc = Document(
        page_content=description,
        metadata={
            "source": file_path,
            "type": "image",
            "original_content": "image_data"
        }
    )

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    
    splits = text_splitter.split_documents([doc])
    
    return splits

def process_document(file_path):
    print(f"> PROCESSING: {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print("> Splitting document into chunks...")
    if file_path.endswith(".md"):
        splits = split_markdown_document(file_path)
    elif file_path.endswith(".pdf"):
        splits = split_pdf_document(file_path)
    elif file_path.endswith((".png", ".jpg", ".jpeg")):
        splits = split_image(file_path)
    else:
        splits = split_text_document(file_path)
    print(f"> Split into {len(splits)} chunks.")

    if len(splits) == 0:
        print("> Error: No text found in the document.")
        sys.exit(1)

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
