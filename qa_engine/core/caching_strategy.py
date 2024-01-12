from abc import ABC, abstractmethod
from qa_engine.core.models import TextEntry, EmbeddingEntry, Document
from qa_engine.core.embedding_operator import EmbeddingOperator
from qa_engine.core.embedding_factory import EmbeddingFactory
from qa_engine.core.document_factory import DocumentFactory, generate_id
from qa_engine.core.document_operator import DocumentOperator
from typing import List
import pandas as pd
from qa_engine.utils.chunk import chunk_corpus


class CachingStrategy(ABC):
    """
    CachingStrategy is an abstract class that defines the interface for caching strategies.

    Responsibilities:
        - Manipulates the document and converts into a list of TextEntry and EmbeddingEntry objects.
        - Utilises the factories to store the entries.
        - Utilises the operators to parse the documents and embed the text.
        - finding relevant documents given a query in accordance with the way the entries returning the list of ids.

    """

    def __init__(self,
                 embedding_factory: EmbeddingFactory,
                 document_factory: DocumentFactory,
                 embedding_operator: EmbeddingOperator,
                 document_operator: DocumentOperator):
        self.embedding_factory = embedding_factory
        self.document_factory = document_factory
        self.embedding_operator = embedding_operator
        self.document_operator = document_operator

    """
    Takes in and parses a document and indexes it
    """

    def cache(self, document: Document):
        # Parse the document
        parsed_obj = self.document_operator.parse(document)
        text_entries = self._parsed_obj_to_entries(parsed_obj)
        embedding_entries = self._text2embedding_entries(text_entries)
        # Store them
        self._store_text(document.id, text_entries)
        self._store_embeddings(document.id, embedding_entries)

    def find(self, doc_id: str, query: str, metadata=None):
        query_embedding = \
            self.embedding_operator.embed([TextEntry(generate_id(), text=query, metadata={})])[
                0].embedding
        entries = self.embedding_factory.retrieve(doc_id, query_embedding, metadata)
        return self._embedding2text_entries(doc_id, entries)

    def remove_by_ids(self, doc_id: str, entry_ids: List[str], *args, **kwargs) -> bool:
        self.embedding_factory.remove_by_ids(doc_id, entry_ids, *args, **kwargs)
        return self.document_factory.remove_by_ids(doc_id, entry_ids, *args, **kwargs)

    @abstractmethod
    def _parsed_obj_to_entries(self, parsed_obj) -> List[TextEntry]:
        pass

    def _text2embedding_entries(self, text_entries: List[TextEntry]) -> List[EmbeddingEntry]:
        return self.embedding_operator.embed(text_entries)

    def _embedding2text_entries(self, doc_id, embedding_entries: List[EmbeddingEntry]) -> List[
        TextEntry]:
        ids = [embedding_entry.id for embedding_entry in embedding_entries]
        text_entries = self.document_factory.retrieve(doc_id, ids)
        return text_entries

    def _store_embeddings(self, doc_id, entries: List[EmbeddingEntry], *args, **kwargs):
        self.embedding_factory.store(doc_id, entries, *args, **kwargs)

    def _store_text(self, doc_id, entries: List[TextEntry], *args, **kwargs):
        self.document_factory.store(doc_id, entries, *args, **kwargs)


class BasicJSONCachingStrategy(CachingStrategy):

    def __init__(self,
                 embedding_factory: EmbeddingFactory,
                 document_factory: DocumentFactory,
                 embedding_operator: EmbeddingOperator,
                 document_operator: DocumentOperator,
                 text_keys: List[str],
                 id_key: str):
        super().__init__(embedding_factory, document_factory, embedding_operator, document_operator)
        self.text_keys = text_keys
        self.id_key = id_key

    def _parsed_obj_to_entries(self, parsed_obj: List[dict]) -> List[TextEntry]:
        text_entries = []
        for obj in parsed_obj:
            obj_id = obj[self.id_key]
            text = ""
            for key in self.text_keys:
                text += f"{key}: {obj[key]}\n"
            text_entries.append(TextEntry(id=obj_id, text=text, metadata=obj))
        return text_entries


class ChunkingCachingStrategy(CachingStrategy):
    """
    Caching strategy that chunks the document into smaller chunks and caches each chunk separately.
    :parameter chunk_size: The number of sentences per chunk.
    :parameter sentence_word_count: The minimum and maximum word count of a sentence in the document.
    """

    def __init__(self,
                 embedding_factory: EmbeddingFactory,
                 document_factory: DocumentFactory,
                 embedding_operator: EmbeddingOperator,
                 document_operator: DocumentOperator,
                 chunk_size=8,
                 sentence_word_count=(15, 100)):
        super().__init__(embedding_factory, document_factory, embedding_operator,
                         document_operator)
        self.chunk_size = chunk_size
        self.sentence_word_count = sentence_word_count

    def _chunk_corpus(self, corpus: str) -> List[TextEntry]:

        chunks = chunk_corpus(corpus, self.chunk_size, self.sentence_word_count)

        text_entry_chunks = []
        for chunk in chunks:
            chunk_id = generate_id()
            for sentence in chunk:
                txt_entry_id = generate_id()
                text_entry_chunks.append(TextEntry(id=txt_entry_id, text=sentence, metadata={
                    "chunk_id": chunk_id
                }))

        return text_entry_chunks

    def find(self, doc_id: str, query: str, metadata=None):
        text_entries = super().find(doc_id, query, metadata)
        # convert to pandas and group by chunk_id
        df = pd.DataFrame([text_entry.to_dict() for text_entry in text_entries])
        df["chunk_id"] = df["metadata"].apply(lambda x: x["chunk_id"])
        df = df.drop(columns=["metadata"])
        df = df.groupby("chunk_id").agg(lambda x: " ".join(x))
        # convert back to list of TextEntry
        text_entries = [
            TextEntry(id=chunk_id, text=text, metadata={"chunk_id": chunk_id})
            for chunk_id, text in df["text"].items()
        ]
        return text_entries


class JSONChunkingCachingStrategy(ChunkingCachingStrategy):

    def __init__(self,
                 embedding_factory: EmbeddingFactory,
                 document_factory: DocumentFactory,
                 embedding_operator: EmbeddingOperator,
                 document_operator: DocumentOperator,
                 text_keys: List[str],
                 id_key: str,
                 chunk_size=8,
                 sentence_word_count=(15, 100)):
        super().__init__(
            embedding_factory,
            document_factory,
            embedding_operator,
            document_operator,
            chunk_size,
            sentence_word_count,
        )
        self.text_keys = text_keys
        self.id_key = id_key

    def cache(self, document: Document):
        json_objs: List[dict] = document.data
        ids = [json_obj[self.id_key] for json_obj in json_objs]
        existing_text_entries = self.document_factory.retrieve(document.id, ids)
        id_black_list = [text_entry.id for text_entry in existing_text_entries]
        white_objects = list(filter(lambda x: x[self.id_key] not in id_black_list, json_objs))
        new_doc = Document(document.id, data=white_objects)
        super().cache(new_doc)

    def _parsed_obj_to_entries(self, parsed_obj: List[dict]) -> List[TextEntry]:
        text_entries = []
        # For every object in the parsed object
        for obj in parsed_obj:
            obj_id = obj[self.id_key]
            # For every text key in the object
            for key in self.text_keys:
                # Chunk the text and append the text entries
                obj_key_text = obj[key]
                obj_key_text_entries = self._chunk_corpus(obj_key_text)
                for text_entry in obj_key_text_entries:
                    text_entry.metadata["obj_id"] = obj_id
                    text_entry.metadata["obj_key"] = key
                text_entries += obj_key_text_entries
        return text_entries


class PDFChunkingCachingStrategy(ChunkingCachingStrategy):
    def _parsed_obj_to_entries(self, parsed_obj: [str]) -> List[TextEntry]:
        return self._chunk_corpus(
            "\n ========================= PAGE END ========================= \n".join(parsed_obj))
