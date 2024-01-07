from dataclasses import dataclass


@dataclass
class Document:
    id: str
    data: str


@dataclass
class TextEntry:
    id: str
    text: str
    metadata: dict

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'metadata': self.metadata
        }


@dataclass
class EmbeddingEntry:
    id: str
    embedding: list
    metadata: dict
