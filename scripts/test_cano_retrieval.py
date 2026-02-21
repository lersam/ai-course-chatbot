import os
import re
import sys
import types


def make_dummy_modules():
    """Inject lightweight dummy modules so importing rag_chatbot doesn't require heavy deps."""
    # Dummy ai_course_chatbot.ai_modules.vector_store
    mod_vs = types.ModuleType("ai_course_chatbot.ai_modules.vector_store")
    class DummyVectorStore:
        def __init__(self, *args, **kwargs):
            pass
        def get_retriever(self, k=2):
            return None
    mod_vs.VectorStore = DummyVectorStore
    sys.modules["ai_course_chatbot.ai_modules.vector_store"] = mod_vs
    # Prevent package-level imports from running by inserting a placeholder package module
    pkg_mod = types.ModuleType("ai_course_chatbot.ai_modules")
    # Mark as package to satisfy import system
    pkg_mod.__path__ = []
    sys.modules["ai_course_chatbot.ai_modules"] = pkg_mod

    # Dummy langchain_community.llms.Ollama
    # Ensure parent package exists
    parent_lcc = types.ModuleType("langchain_community")
    sys.modules["langchain_community"] = parent_lcc

    mod_llms = types.ModuleType("langchain_community.llms")
    class Ollama:
        def __init__(self, *args, **kwargs):
            pass
    mod_llms.Ollama = Ollama
    sys.modules["langchain_community.llms"] = mod_llms
    parent_lcc.llms = mod_llms

    # Dummy langchain.chains.RetrievalQA
    # Ensure parent package exists
    parent_lc = types.ModuleType("langchain")
    sys.modules["langchain"] = parent_lc

    mod_chains = types.ModuleType("langchain.chains")
    class RetrievalQA:
        @staticmethod
        def from_chain_type(*args, **kwargs):
            return None
    mod_chains.RetrievalQA = RetrievalQA
    sys.modules["langchain.chains"] = mod_chains
    parent_lc.chains = mod_chains

    # Dummy langchain.prompts.PromptTemplate
    mod_prompts = types.ModuleType("langchain.prompts")
    class PromptTemplate:
        def __init__(self, *args, **kwargs):
            pass
    mod_prompts.PromptTemplate = PromptTemplate
    sys.modules["langchain.prompts"] = mod_prompts
    parent_lc.prompts = mod_prompts


class SimpleDoc:
    def __init__(self, metadata: dict):
        self.metadata = metadata


class FakeQAChain:
    def __init__(self, qa_list, source_path):
        self.qa_list = qa_list
        self.source_path = source_path

    def invoke(self, payload):
        query = payload.get("query", "").strip()
        # Try exact match first
        for entry in self.qa_list:
            if entry["question"].strip().lower() == query.lower():
                answer = entry["answer"].strip()
                doc = SimpleDoc({"source": self.source_path, "page": entry["page"]})
                return {"result": answer, "source_documents": [doc]}

        # Fallback: substring match
        for entry in self.qa_list:
            if query.lower() in entry["question"].lower() or entry["question"].lower() in query.lower():
                answer = entry["answer"].strip()
                doc = SimpleDoc({"source": self.source_path, "page": entry["page"]})
                return {"result": answer, "source_documents": [doc]}

        return {"result": "", "source_documents": []}


def parse_cano_md(path):
    text = open(path, encoding="utf-8").read()
    pattern = re.compile(r"\*\*Question:\*\*\s*(.*?)\n\*\*Answer:\*\*\s*(.*?)\n\*\*Page:\*\*\s*(\d+)", re.S)
    items = []
    for m in pattern.finditer(text):
        q = m.group(1).strip()
        a = m.group(2).strip()
        p = int(m.group(3).strip())
        items.append({"question": q, "answer": a, "page": p})
    return items


def clean_text(s: str) -> str:
    s = re.sub(r"\*\*", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Ensure repo root is on sys.path so package imports work when running as a script
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    data_path = os.path.join(repo_root, "data", "sherlock-holmes", "cano.md")
    if not os.path.exists(data_path):
        print(f"Data file not found: {data_path}")
        sys.exit(2)

    qa_list = parse_cano_md(data_path)
    if not qa_list:
        print("No Q/A blocks parsed from the markdown file.")
        sys.exit(2)
    # Try to use chromadb as the backing store if available.
    try:
        import chromadb
        from chromadb.config import Settings
        use_chroma = True
    except Exception:
        use_chroma = False

    if use_chroma:
        store_dir = os.path.join(repo_root, "chroma_db")
        client = chromadb.Client(Settings(persist_directory=store_dir))
        coll_name = "cano_qa"
        try:
            collection = client.get_collection(coll_name)
        except Exception:
            collection = client.create_collection(coll_name)

        ids = []
        metadatas = []
        documents = []
        for entry in qa_list:
            source = os.path.basename(data_path)
            page = entry["page"]
            doc_id = f"{os.path.splitext(source)[0]}:{page}"
            ids.append(doc_id)
            metadatas.append({"source": source, "page": page})
            # store the answer as the document text
            documents.append(entry["answer"])

        # Add documents (upsert by id will overwrite existing)
        try:
            collection.add(ids=ids, metadatas=metadatas, documents=documents)
            try:
                collection.persist()
            except Exception:
                pass
        except Exception as e:
            print(f"Failed to add documents to ChromaDB: {e}")
            sys.exit(2)

        all_ok = True
        failures = []
        for entry in qa_list:
            q = entry["question"]
            expected_answer = clean_text(entry["answer"]) 
            expected_page = entry["page"]

            try:
                res = collection.query(query_texts=[q], n_results=1, include=["metadatas", "documents"])
            except TypeError:
                # Older/newer chromadb API variants
                res = collection.query([q], n_results=1)

            # Normalize returned structure
            found_doc = ""
            found_meta = {}
            try:
                # Newer API: dict with 'documents' list of lists
                found_doc = res.get("documents", [[]])[0][0]
                found_meta = res.get("metadatas", [[]])[0][0]
            except Exception:
                # Fallback for other shapes
                try:
                    found_doc = res["documents"][0][0]
                    found_meta = res["metadatas"][0][0]
                except Exception:
                    pass

            found_answer = clean_text(found_doc or "")
            page_ok = int(found_meta.get("page", -1)) == expected_page
            answer_ok = expected_answer.lower() in found_answer.lower()

            if not (answer_ok and page_ok):
                all_ok = False
                failures.append({"question": q, "expected_answer": expected_answer, "found": found_answer, "page_ok": page_ok, "found_meta": found_meta})

        if all_ok:
            print("All Q/A entries correctly retrieved from ChromaDB and pages matched.")
            sys.exit(0)
        else:
            print("Some entries failed when querying ChromaDB:\n")
            for f in failures:
                print("Question:", f["question"])
                print("Expected Answer:", f["expected_answer"])
                print("Found Answer:", f["found"])
                print("Page matched:", f["page_ok"])
                print("Found metadata:", f["found_meta"])
                print("-" * 40)
            sys.exit(2)

    # Fallback: previous in-memory fake QA chain approach
    make_dummy_modules()
    import importlib.util
    module_name = "ai_course_chatbot.ai_modules.rag_chatbot"
    module_path = os.path.join(repo_root, "ai_course_chatbot", "ai_modules", "rag_chatbot.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    RAGChatbot = getattr(mod, "RAGChatbot")

    rag = object.__new__(RAGChatbot)
    rag.qa_chain = FakeQAChain(qa_list, data_path)

    all_ok = True
    failures = []

    for entry in qa_list:
        q = entry["question"]
        expected_answer = clean_text(entry["answer"])
        expected_page = entry["page"]

        result_text = rag.ask(q, show_sources=True)
        found_answer = clean_text(result_text.split("\n\nSources:")[0])
        page_ok = f"Page {expected_page}" in result_text

        answer_ok = expected_answer.lower() in found_answer.lower()

        if not (answer_ok and page_ok):
            all_ok = False
            failures.append({"question": q, "expected_answer": expected_answer, "found": found_answer, "page_ok": page_ok, "result_text": result_text})

    if all_ok:
        print("All Q/A entries correctly retrieved and pages matched (fallback).")
        sys.exit(0)
    else:
        print("Some entries failed (fallback):\n")
        for f in failures:
            print("Question:", f["question"])
            print("Expected Answer:", f["expected_answer"])
            print("Found Answer:", f["found"])
            print("Page matched:", f["page_ok"])
            print("Result Text:\n", f["result_text"])
            print("-" * 40)
        sys.exit(2)


if __name__ == "__main__":
    main()
