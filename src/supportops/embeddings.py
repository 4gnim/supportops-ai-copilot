from functools import lru_cache

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from supportops.config import settings


class E5Embeddings(Embeddings):
    """Multilingual E5 embeddings with the required query/passsage prefixes."""

    def __init__(self, model_name: str) -> None:
        self.model = SentenceTransformer(model_name, device="cpu")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prepared = [f"passage: {text}" for text in texts]
        vectors = self.model.encode(
            prepared,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self.model.encode(
            f"query: {text}",
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vector.tolist()


@lru_cache(maxsize=1)
def get_embeddings() -> E5Embeddings:
    """Load the embedding model once per application process."""
    return E5Embeddings(settings.embedding_model)
