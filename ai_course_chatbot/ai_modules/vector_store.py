"""
Vector Store Module
Manages document embeddings and vector storage using ChromaDB.
"""
import os
import hashlib
import time
import re
import gensim
from importlib_metadata import metadata
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from typing import List, Tuple
from pathlib import Path

# Disable LangChain/Chroma telemetry at import time to keep the CLI offline-only.
os.environ.setdefault("LANGCHAIN_TELEMETRY", "false")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")


class VectorStore:
    """Manages vector storage for document embeddings."""

    def __init__(self, collection_name: str = "pdf_documents",
                 persist_directory: str = "./chroma_db",
                 embedding_model: str = "nomic-embed-text",
                 normalize_lower: bool = False,
                 default_lang: str = "en"):
        """
        Initialize the vector store.

        Args:
            collection_name: Name of the collection in ChromaDB
            persist_directory: Directory to persist the database
            embedding_model: Ollama embedding model to use
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.embedding_model_version = embedding_model
        self.normalize_lower = normalize_lower
        self.default_lang = default_lang

        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize Ollama embeddings
        embeddings = OllamaEmbeddings(model=embedding_model)

        # Initialize ChromaDB vector store
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=embeddings,
            persist_directory=self.persist_directory
        )

    def add_documents(self, documents: List) -> None:
        """
        Add documents to the vector store.

        Args:
            documents: List of document chunks to add
        """
        if not documents:
            print("Warning: Empty document list provided, no documents will be added")
            return

        normalized_docs, candidate_ids = self._prepare_documents(documents)

        existing_ids = self._get_existing_ids(candidate_ids)
        filtered_docs = []
        filtered_ids = []
        skipped = 0
        seen_ids = set()

        for doc_id, doc in zip(candidate_ids, normalized_docs):
            if doc_id in existing_ids or doc_id in seen_ids:
                skipped += 1
                continue
            seen_ids.add(doc_id)
            filtered_ids.append(doc_id)
            filtered_docs.append(doc)

        if not filtered_docs:
            print("All provided documents already exist in the vector store; nothing to add.")
            return

        batch_size = 64
        for i in range(0, len(filtered_docs), batch_size):
            batch_docs = filtered_docs[i: i + batch_size]
            batch_ids = filtered_ids[i: i + batch_size]
            start = time.time()
            new_ids = self.vectorstore.add_documents(batch_docs, ids=batch_ids)
            end = time.time()
            print(f"Processed {i + len(batch_docs)} / {len(documents)} documents; in {end - start:.2f} seconds")

        self._persist_vectorstore()

        if skipped:
            print(f"Skipped {skipped} duplicate documents based on deterministic IDs.")
        print(f"Added {len(filtered_docs)} new documents to vector store")


    def similarity_search(self, query: str, k: int = 4) -> List:
        """
        Search for similar documents.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of similar documents
        """
        results = self.vectorstore.similarity_search(query, k=k)
        return results

    def get_retriever(self, k: int = 2):
        """
        Get a retriever for the vector store.

        Args:
            k: Number of documents to retrieve (default: 2 for optimal performance)

        Returns:
            Retriever object
        """
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def document_count(self) -> int:
        """Return the number of stored documents in the active collection."""
        try:
            collection = getattr(self.vectorstore, "_collection", None)
            if collection is not None:
                return int(collection.count())
        except Exception:
            pass

        return 0

    def has_documents(self) -> bool:
        """Check whether the collection contains at least one document."""
        return self.document_count() > 0

    def _prepare_documents(self, documents: List) -> Tuple[List, List[str]]:
        """Normalize metadata and generate stable IDs for each document."""
        normalized_docs = []
        doc_ids = []
        for doc in documents:
            # Delegate normalization and metadata enrichment to helper
            doc_id = self._normalize_document(doc)
            normalized_docs.append(doc)
            doc_ids.append(doc_id)

        return normalized_docs, doc_ids

    def _get_existing_ids(self, candidate_ids: List[str]) -> set:
        """Retrieve the subset of candidate IDs that already exist in the store."""
        if self.vectorstore is None:
            return set()

        try:
            response = self.vectorstore.get(ids=candidate_ids, include=[])
            return set(response.get("ids", []))
        except Exception:
            return set()

    def _normalize_text(self, text: str) -> str:
        """Lightweight normalization: collapse whitespace and strip control characters.

        This function intentionally keeps punctuation and headings intact while
        reducing noisy whitespace and PDF artifacts (formfeeds, repeated spaces).
        """
        if not text:
            return ""
        # remove common PDF formfeed markers
        text = text.replace("\x0c", " ")
        # collapse all whitespace (including newlines) to single spaces
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _normalize_document(self, doc) -> str:
        """Normalize a single document's metadata and content and return a deterministic doc id.

        This consolidates all normalization/enrichment steps so other callers can reuse it.
        """
        metadata = getattr(doc, "metadata", None)
        if not isinstance(metadata, dict):
            metadata = {}
            setattr(doc, "metadata", metadata)

        # Normalize source and derive title
        source = metadata.get("source")
        if isinstance(source, str) and source:
            path = Path(source)
            if path.is_absolute() or path.name != source:
                metadata["source"] = path.stem

        normalized_source = metadata.get("source", "unknown")

        # Normalize content: collapse whitespace, strip control chars
        content = getattr(doc, "page_content", "") or ""
        normalized_content = self._normalize_text(content)
        if self.normalize_lower:
            normalized_content = normalized_content.lower()
        # Replace the document content with normalized content
        setattr(doc, "page_content", normalized_content)

        # Deterministic content hash on normalized content
        content_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()
        metadata["content_hash"] = content_hash
        metadata["keywords"] = ','.join(gensim.utils.simple_preprocess(normalized_content, deacc=True, min_len=3, max_len=20))
        # Enrich metadata fields to help retrieval/filtering
        metadata.setdefault("title", normalized_source)
        metadata.setdefault("section", metadata.get("section", None))
        metadata.setdefault("page", metadata.get("page", 0))
        metadata.setdefault("lang", metadata.get("lang", self.default_lang))
        metadata.setdefault("source_type", metadata.get("source_type", "pdf"))
        # Record the embedding model used so we can re-embed/track versions later
        metadata.setdefault("embedding_model", self.embedding_model)
        metadata.setdefault("embedding_model_version", self.embedding_model_version)

        page = metadata.get("page", 0)
        doc_id = f"{normalized_source}:{page}:{content_hash[:16]}"
        return doc_id

    def _persist_vectorstore(self) -> None:
        """Persist the vector store safely if the backend supports it."""
        try:
            if hasattr(self.vectorstore, "persist"):
                self.vectorstore.persist()
        except Exception:
            pass
