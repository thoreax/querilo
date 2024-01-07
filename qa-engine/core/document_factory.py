from abc import ABC, abstractmethod
from core.models import TextEntry
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import uuid


def generate_id() -> str:
    return str(uuid.uuid4())


class DocumentFactory(ABC):

    @abstractmethod
    def store(self, doc_id, entries: [TextEntry], *args, **kwargs) -> bool:
        pass

    @abstractmethod
    def retrieve(self, doc_id, document_ids: [str], metadata: dict = None, *args, **kwargs) -> [
        TextEntry]:
        pass


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

    def store(self, doc_id, entries: [TextEntry], refresh=False, *args, **kwargs) -> bool:
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

    def retrieve(self, doc_id, document_ids: [str] = None, metadata: dict = None, *args,
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
                query["query"]["bool"]["must"].append({"term": {f"metadata.{key}": value}})
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
