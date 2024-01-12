from abc import ABC, abstractmethod
from qa_engine.core.models import TextEntry
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import uuid
from typing import List


def generate_id() -> str:
    return str(uuid.uuid4())


class DocumentFactory(ABC):

    @abstractmethod
    def store(self, doc_id, entries: List[TextEntry], *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def remove_by_ids(self, doc_id, entry_ids: List[str], *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def retrieve(self, doc_id, document_ids: List[str]=None, metadata: dict = None, *args, **kwargs) -> List[TextEntry]:
        pass

    def remove(self, doc_id, entries: List[TextEntry], *args, **kwargs) -> bool:
        return self.remove_by_ids(doc_id, [entry.id for entry in entries], *args, **kwargs)


class ESDocumentFactory(DocumentFactory):

    def __init__(self, es_client_params: dict, index_name="doc_text_entries"):
        self.es_client = Elasticsearch(**es_client_params)
        self.index_name = index_name
        self.__create_index_if_not_exists()

    def destruct(self):
        self.es_client.indices.delete(index=self.index_name)

    def clear(self):
        self.destruct()
        self.__create_index_if_not_exists()

    def __create_index_if_not_exists(self):
        if self.es_client.indices.exists(index=self.index_name):
            return
        self.es_client.indices.create(index=self.index_name)
        self.es_client.indices.put_mapping(index=self.index_name, body={
            "properties": {
                "parent_doc_id": {"type": "keyword"},
                "id": {"type": "keyword"},
                "text": {"type": "text"},
                "metadata": {"type": "object"},
            },
        })

    def store(self, doc_id, entries: List[TextEntry], refresh=False, *args, **kwargs) -> bool:
        actions = [
            {
                "_index": self.index_name,
                "_id": f"{doc_id}_{entry.id}",
                "_source": {
                    "parent_doc_id": doc_id,
                    "id": entry.id,
                    "text": entry.text,
                    "metadata": entry.metadata,
                }
            }
            for entry in entries
        ]
        bulk(self.es_client, actions, refresh=refresh)
        return True

    def retrieve(self, doc_id, document_ids: List[str] = None, metadata: dict = None, *args,
                 **kwargs) -> [TextEntry]:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"parent_doc_id": doc_id}},
                    ],
                },
            },
        }
        if document_ids:
            query["query"]["bool"]["must"].append({"terms": {"id": document_ids}})
        if metadata is not None:
            # match all the keys of metadata query
            for key, value in metadata.items():
                if isinstance(value, str):
                    query["query"]["bool"]["must"].append({"term": {f"metadata.{key}": value}})
                elif isinstance(value, list):
                    query["query"]["bool"]["must"].append({"terms": {f"metadata.{key}.keyword": value}})
        response = self.es_client.search(index=self.index_name, body=query)
        entries = [
            TextEntry(
                id=hit["_source"]["id"],
                text=hit["_source"]["text"],
                metadata=hit["_source"]["metadata"],
            )
            for hit in response["hits"]["hits"]
        ]
        return entries

    def remove_by_ids(self, doc_id, entry_ids: List[str], *args, **kwargs) -> bool:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"parent_doc_id": doc_id}},
                        {"terms": {"id": entry_ids}},
                    ],
                },
            },
        }
        self.es_client.delete_by_query(index=self.index_name, body=query)
        return True
