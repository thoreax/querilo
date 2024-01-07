from abc import ABC, abstractmethod
from tqdm import tqdm
from PyPDF2 import PdfReader
from qa_engine.core.models import Document


class DocumentOperator(ABC):
    @abstractmethod
    def parse(self, document, *args, **kwargs) -> any:
        pass


class PDFDocumentOperator(DocumentOperator):
    def parse(self, document, *args, **kwargs) -> any:
        path = document.data
        # print(path)
        reader = PdfReader(path)  # path / ../'Project plan.pdf'
        text = [page.extract_text() for page in tqdm(reader.pages)]
        return text


class BasicDocumentOperator(DocumentOperator):
    def parse(self, document: Document, *args, **kwargs) -> any:
        return document.data
