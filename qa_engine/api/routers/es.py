from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from qa_engine.api.config import get_settings, Settings
from qa_engine.core.document_factory import ESDocumentFactory
from qa_engine.core.embedding_factory import ESEmbeddingFactory
from qa_engine.core.caching_strategy import JSONChunkingCachingStrategy
from qa_engine.core.embedding_operator import OpenAIEmbeddingOperator
from qa_engine.core.document_operator import BasicDocumentOperator
from qa_engine.core.answer_strategy import OpenAIAnswerStrategy
from qa_engine.core.ir_system import IRSystem
from qa_engine.core.models import Document
from pydantic import BaseModel
from qa_engine.api.utils import create_response

settings = get_settings()

router = APIRouter(
    prefix="/es",
    tags=["elasticsearch"],
    responses={404: {"description": "Not found"}},
)


class IndexDocumentsRequest(BaseModel):
    documents: Any = []
    association_id: str
    embedding_provider = "openai"
    text_keys: List[str]
    id_key: str


def configure_ir_system(index_name: str, config: Settings, text_keys=["description"], id_key="id"):
    es_client_params = {
        "cloud_id": config.es_cloud_id,
        "http_auth": (config.es_username, config.es_password),
    }
    json_strategy = JSONChunkingCachingStrategy(
        document_factory=ESDocumentFactory(es_client_params, index_name+"$docs"),
        embedding_factory=ESEmbeddingFactory(es_client_params, index_name+"$embs", embedding_size=1536),
        embedding_operator=OpenAIEmbeddingOperator("text-embedding-ada-002", config.openai_key, config.openai_org),
        document_operator=BasicDocumentOperator(),
        text_keys=text_keys,
        id_key=id_key,
    )
    answer_strategy = OpenAIAnswerStrategy("gpt-3.5-turbo-16k", config.openai_key, config.openai_org)
    ir_system = IRSystem(caching_strategy=json_strategy, answer_strategy=answer_strategy)
    return ir_system


@router.put("/index/{index_name}/json")
def index_documents(
        request: IndexDocumentsRequest,
        index_name: str,
        config: Settings = Depends(get_settings)):
    ir_system = configure_ir_system(index_name, config, request.text_keys)
    ir_system.index_document(
        Document(request.association_id, data=request.documents),
    )
    return create_response(f"Indexed {len(request.documents)} documents in {index_name}")


@router.get("/index/{index_name}/json")
def search_documents(
        index_name: str,
        q: str,
        association_id: str,
        formulate_answer: bool = True,
        filters: Dict=None,
        config: Settings = Depends(get_settings)) -> dict:
    ir_system = configure_ir_system(index_name, config)
    return ir_system.find(association_id, q, filters, formulate_answer=formulate_answer)
