######################################################
# Copyright: Tefeno, all rights reserved             #
# License: MIT                                       #
######################################################

from abc import ABC
from core.caching_strategy import CachingStrategy
from core.answer_strategy import AnswerStrategy
from core.models import Document


class IRSystem(ABC):

    def __init__(self,
                 caching_strategy: CachingStrategy,
                 answer_strategy: AnswerStrategy):
        self.caching_strategy = caching_strategy
        self.answer_strategy = answer_strategy

    def index_document(self, document: Document, *args, **kwargs):
        self.caching_strategy.cache(document)

    def find(self, doc_id: str, query: str, metadata: dict = None, formulate_answer=True, *args, **kwargs) -> dict:
        entries = self.caching_strategy.find(doc_id, query, metadata)
        return {
            "resources": entries,
            "query": query,
            "answer": self.answer_strategy.formulate_answer(query, entries) if formulate_answer else None
        }


class BookIRSystem(IRSystem):

    def __init__(self, caching_strategy, answer_strategy):
        super().__init__(caching_strategy, answer_strategy)
