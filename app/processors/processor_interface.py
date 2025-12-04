from langchain_core.documents import Document

from abc import ABC, abstractmethod

class ProcessorInterface(ABC):
    @abstractmethod
    def process(self, file_path: str) -> list[Document]:
        pass