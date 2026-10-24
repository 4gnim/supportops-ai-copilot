import shutil
from collections import defaultdict
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from supportops.config import settings
from supportops.embeddings import get_embeddings

SUPPORTED_EXTENSIONS = {".md", ".txt"}


def load_source_documents(directory: Path | None = None) -> list[Document]:
    """Read supported local knowledge files and preserve their source names."""
    source_dir = directory or settings.knowledge_dir
    if not source_dir.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {source_dir}")

    documents: list[Document] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        content = path.read_text(encoding="utf-8").strip()
        if content:
            documents.append(
                Document(
                    page_content=content,
                    metadata={"source": path.name, "document_id": path.stem},
                )
            )

    if not documents:
        raise ValueError(f"No non-empty .md or .txt files found in {source_dir}")
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """Chunk documents while keeping source and per-source chunk identifiers."""
    if settings.chunk_overlap >= settings.chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    source_counts: defaultdict[str, int] = defaultdict(int)
    for chunk in chunks:
        source = str(chunk.metadata.get("source", "unknown"))
        index = source_counts[source]
        source_counts[source] += 1
        chunk.metadata["chunk_id"] = f"{Path(source).stem}::chunk-{index:03d}"
    return chunks


def get_vector_store() -> Chroma:
    """Open the persistent local Chroma collection."""
    settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.vector_store_dir),
        collection_metadata={"hnsw:space": "cosine"},
    )


def rebuild_knowledge_index() -> dict[str, int]:
    """Rebuild the local index from source files to avoid accidental duplicate chunks."""
    documents = load_source_documents()
    chunks = split_documents(documents)

    # This directory is dedicated to this project's derived vector index.
    if settings.vector_store_dir.exists():
        shutil.rmtree(settings.vector_store_dir)
    settings.vector_store_dir.mkdir(parents=True, exist_ok=True)

    store = get_vector_store()
    store.add_documents(chunks)
    return {"documents": len(documents), "chunks": len(chunks)}
