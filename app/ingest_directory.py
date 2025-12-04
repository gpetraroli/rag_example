import argparse
from os import walk, path
from ingest_document import process_document


def process_directory(directory_path: str) -> None:
    print(f"> PROCESSING DIRECTORY: {directory_path}")

    for root, _, files in walk(directory_path):
        for file in files:
            process_document(path.join(root, file))
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG CLI Tool: Ingest a file and store it in the vector database.")

    parser.add_argument("directory", help="Path to the directory")

    args = parser.parse_args()

    process_directory(args.directory)