"""
Vector Store Module
Manages document embeddings and vector storage using ChromaDB.
"""
import os
import hashlib
import logging
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

from typing import List, Tuple
from pathlib import Path

from ai_course_chatbot.config import get_settings

os.environ.setdefault("LANGCHAIN_TELEMETRY", "false")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages vector storage for document embeddings."""

    def __init__(self, collection_name: str | None = None,
                 persist_directory: str | None = None,
                 embedding_model: str | None = None,
                 normalize_lower: bool = False,
                 default_lang: str = "en"):
        settings = get_settings()

        self.collection_name = collection_name or settings.chroma_collection
        self.persist_directory = persist_directory or settings.chroma_persist_dir
        self.embedding_model = embedding_model or settings.embedding_model
        self.embedding_model_version = self.embedding_model
        self.normalize_lower = normalize_lower
        self.default_lang = default_lang

        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        embeddings = OllamaEmbeddings(model=self.embedding_model)

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=embeddings,
            persist_directory=self.persist_directory
        )

    def add_documents(self, documents: List) -> None:
        if not documents:
            logger.warning("Empty document list provided, no documents will be added")
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
            logger.info("All provided documents already exist in the vector store; nothing to add.")
            return

        batch_size = 128
        batches = [
            (filtered_docs[i: i + batch_size], filtered_ids[i: i + batch_size])
            for i in range(0, len(filtered_docs), batch_size)
        ]

        processed = 0
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            for idx, (batch_docs, batch_ids) in enumerate(batches):
                future = executor.submit(self._add_batch, batch_docs, batch_ids)
                futures[future] = (idx, len(batch_docs))

            for future in as_completed(futures):
                idx, count = futures[future]
                elapsed = future.result()
                processed += count
                logger.info(
                    "Processed %d / %d documents; in %.2f seconds",
                    processed, len(documents), elapsed,
                )

        self._persist_vectorstore()

        if skipped:
            logger.info("Skipped %d duplicate documents based on deterministic IDs.", skipped)
        logger.info("Added %d new documents to vector store", len(filtered_docs))

    def _add_batch(self, batch_docs: List, batch_ids: List[str]) -> float:
        start = time.time()
        self.vectorstore.add_documents(batch_docs, ids=batch_ids)
        return time.time() - start

    def similarity_search(self, query: str, k: int = 4) -> List:
        results = self.vectorstore.similarity_search(query, k=k)
        return results

    def get_retriever(self, k: int = 2):
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def document_count(self) -> int:
        try:
            collection = getattr(self.vectorstore, "_collection", None)
            if collection is not None:
                return int(collection.count())
        except Exception:
            pass
        return 0

    def has_documents(self) -> bool:
        return self.document_count() > 0

    def _prepare_documents(self, documents: List) -> Tuple[List, List[str]]:
        normalized_docs = []
        doc_ids = []
        for doc in documents:
            doc_id = self._normalize_document(doc)
            normalized_docs.append(doc)
            doc_ids.append(doc_id)
        return normalized_docs, doc_ids

    def _get_existing_ids(self, candidate_ids: List[str]) -> set:
        if self.vectorstore is None:
            return set()
        try:
            response = self.vectorstore.get(ids=candidate_ids, include=[])
            return set(response.get("ids", []))
        except Exception:
            return set()

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\x0c", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _normalize_document(self, doc) -> str:
        metadata = getattr(doc, "metadata", None)
        if not isinstance(metadata, dict):
            metadata = {}
            setattr(doc, "metadata", metadata)

        source = metadata.get("source")
        if isinstance(source, str) and source:
            path = Path(source)
            if path.is_absolute() or path.name != source:
                metadata["source"] = path.stem

        normalized_source = metadata.get("source", "unknown")

        content = getattr(doc, "page_content", "") or ""
        normalized_content = self._normalize_text(content)
        if self.normalize_lower:
            normalized_content = normalized_content.lower()
        setattr(doc, "page_content", normalized_content)

        content_hash = hashlib.sha256(normalized_content.encode("utf-8")).hexdigest()

        page = metadata.get("page", 0)
        doc_id = f"{normalized_source}:p{page}:{content_hash[:16]}"

        metadata.setdefault("title", normalized_source)
        metadata.setdefault("page", page)
        metadata.setdefault("lang", self.default_lang)
        metadata.setdefault("source_type", "pdf")
        metadata.setdefault("embedding_model", self.embedding_model_version)

        return doc_id

    def _persist_vectorstore(self):
        pass
