from abc import ABC, abstractmethod
from typing import List

import elasticsearch.helpers

from qa_engine.core.models import EmbeddingEntry
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


class EmbeddingFactory(ABC):

    @abstractmethod
    def store(self, doc_id: str, embeddings: List[EmbeddingEntry], *args, **kwargs):
        pass

    @abstractmethod
    def remove(self, doc_id: str, embeddings: List[EmbeddingEntry], *args, **kwargs):
        pass

    @abstractmethod
    def remove_by_ids(self, doc_id: str, embedding_ids: List[str], *args, **kwargs):
        pass

    @abstractmethod
    def retrieve(self, doc_id: str, embedding: List[float], metadata: dict, *args, **kwargs) -> List[EmbeddingEntry]:
        pass


class ESEmbeddingFactory(EmbeddingFactory):

    def __init__(self,
                 es_client_params: dict,
                 index_name,
                 embedding_size):
        self.es_client = Elasticsearch(**es_client_params)
        self.index_name = index_name
        self.embedding_size = embedding_size
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
                "id": {
                    "type": "keyword",
                },
                "parent_doc_id": {
                    "type": "keyword",
                },
                "embedding": {
                    "type": "dense_vector",
                    "dims": self.embedding_size,
                    "similarity": "cosine",
                    "index": True,
                },
                "metadata": {
                    "type": "object",
                },
            },
        })

    def store(self, doc_id: str, embeddings: List[EmbeddingEntry], refresh=False, *args, **kwargs):
        actions = [
            {
                "_index": self.index_name,
                "_id": embedding_entry.id,
                "_source": {
                    "embedding": embedding_entry.embedding,
                    "metadata": embedding_entry.metadata,
                    "parent_doc_id": doc_id,
                },
            }
            for embedding_entry in embeddings]
        try:
            bulk(self.es_client, actions, refresh=refresh)
        except elasticsearch.helpers.BulkIndexError as e:
            # Print reaosons
            for item in e.errors:
                # print reason
                print(item['index']['error'])

    def retrieve(self, doc_id, embedding: List[float], metadata: dict = None, *args, **kwargs) -> [
        EmbeddingEntry]:
        # fast retrieval and sort by score
        query = {
            "query": {
                "script_score": {
                    "query": {
                        "match": {
                            "parent_doc_id": doc_id,
                        },
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {
                            "query_vector": embedding,
                        },
                    },
                },
            },
            "size": 10,
        }
        if metadata is not None:
            query["query"]["script_score"]["query"]["match"]["metadata"] = metadata

        response = self.es_client.search(index=self.index_name, body=query)
        return [
            EmbeddingEntry(
                hit["_id"],
                hit["_source"]["embedding"],
                hit["_source"]["metadata"],
            )
            for hit in response["hits"]["hits"]
        ]

    def remove(self, doc_id: str, embeddings: List[EmbeddingEntry], refresh=False, *args, **kwargs):
        actions = [
            {
                "_op_type": "delete",
                "_index": self.index_name,
                "_id": embedding_entry.id,
            }
            for embedding_entry in embeddings]
        try:
            bulk(self.es_client, actions, refresh=refresh)
        except elasticsearch.helpers.BulkIndexError as e:
            # Print reaosons
            for item in e.errors:
                # print reason
                print(item['index']['error'])

    def remove_by_ids(self, doc_id: str, embedding_ids: List[str], refresh=False, *args, **kwargs):
        actions = [
            {
                "_op_type": "delete",
                "_index": self.index_name,
                "_id": embedding_id,
            }
            for embedding_id in embedding_ids]
        try:
            bulk(self.es_client, actions, refresh=refresh)
        except elasticsearch.helpers.BulkIndexError as e:
            # Print reaosons
            for item in e.errors:
                # print reason
                print(item['index']['error'])
