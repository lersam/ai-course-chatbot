"""
Vector Store Module
Manages document embeddings and vector storage using ChromaDB.
"""
import os
import hashlib
import time
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
                 embedding_model: str = "qwen3-embedding:4b"):
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

        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize Ollama embeddings
        self.embeddings = OllamaEmbeddings(model=embedding_model)

        # Initialize ChromaDB vector store
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
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
            print(f"Added batch of {len(batch_docs)} documents with IDs: {new_ids} in {end - start:.2f} seconds")

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
        if self.vectorstore is None:
            print("Warning: Vector store not initialized. Please load documents first.")
            return []

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
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Please load documents first using add_documents().")

        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    def document_count(self) -> int:
        """Return the number of stored documents in the active collection."""
        if self.vectorstore is None:
            return 0

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

    def clear_collection(self) -> None:
        """
        Clear all documents from the collection.
        
        This completely removes all documents from the ChromaDB collection,
        effectively rebuilding it from scratch. Use this when you want to
        start fresh rather than append/deduplicate.
        """
        if self.vectorstore is None:
            print("Warning: Vector store not initialized.")
            return
        
        try:
            # Get the underlying ChromaDB client and delete the collection
            client = self.vectorstore._client
            try:
                client.delete_collection(name=self.collection_name)
                print(f"Cleared collection '{self.collection_name}'")
            except Exception:
                # Collection might not exist, which is fine
                pass
            
            # Recreate the collection with the same settings
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"Recreated empty collection '{self.collection_name}'")
        except Exception as e:
            print(f"Warning: Error clearing collection: {e}")
            raise

    def _prepare_documents(self, documents: List) -> Tuple[List, List[str]]:
        """Normalize metadata and generate stable IDs for each document."""
        normalized_docs = []
        doc_ids = []
        for doc in documents:
            metadata = getattr(doc, "metadata", None)
            if not isinstance(metadata, dict):
                metadata = {}
                setattr(doc, "metadata", metadata)

            source = metadata.get("source")
            if isinstance(source, str) and source:
                path = Path(source)
                if path.is_absolute() or path.name != source:
                    metadata["source"] = path.stem

            content = getattr(doc, "page_content", "") or ""
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            metadata["content_hash"] = content_hash

            page = metadata.get("page", 0)
            normalized_source = metadata.get("source", "unknown")
            doc_id = f"{normalized_source}:{page}:{content_hash[:16]}"

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

    def _persist_vectorstore(self) -> None:
        """Persist the vector store safely if the backend supports it."""
        try:
            if hasattr(self.vectorstore, "persist"):
                self.vectorstore.persist()
        except Exception:
            pass
