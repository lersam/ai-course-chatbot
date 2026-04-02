"""
RAG Chatbot Module
Implements a Retrieval-Augmented Generation chatbot using Ollama.
"""

import logging
import os
from typing import AsyncGenerator

from langchain_community.llms import Ollama
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from .vector_store import VectorStore
from ai_course_chatbot.config import get_settings

logger = logging.getLogger(__name__)


class RAGChatbot:
    """RAG-based chatbot using Ollama for LLM."""

    def __init__(self, vector_store: VectorStore,
                 model_name: str | None = None,
                 num_ctx: int | None = None,
                 temperature: float | None = None):
        settings = get_settings()

        self.vector_store = vector_store
        self.model_name = model_name or settings.ollama_model
        self.num_ctx = num_ctx if num_ctx is not None else settings.llm_num_ctx
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.retriever_k = settings.retriever_k
        self.base_url = settings.ollama_base_url

        self.llm = Ollama(
            model=self.model_name,
            base_url=self.base_url,
            num_ctx=self.num_ctx,
            temperature=self.temperature,
        )

        self.prompt_template = """Use the following pieces of context to answer the question at the end.  
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Context: {context}
        Question: {question}
        Answer:"""

        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"],
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.get_retriever(k=self.retriever_k),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt},
        )

    def ask(self, question: str, show_sources: bool = True) -> str:
        try:
            result = self.qa_chain.invoke({"query": question})
            answer = result["result"]

            if show_sources and "source_documents" in result:
                sources = result["source_documents"]
                if sources:
                    answer += "\n\nSources:"
                    seen: set[tuple[str, str]] = set()
                    idx = 1
                    for doc in sources:
                        source = doc.metadata.get("source", "Unknown")
                        page = doc.metadata.get("page", "N/A")
                        display_source = os.path.splitext(os.path.basename(source))[0]
                        key = (display_source, str(page))
                        if key in seen:
                            continue
                        seen.add(key)
                        answer += f"\n{idx}. {display_source} (Page {page})"
                        idx += 1
            return answer
        except Exception as e:
            logger.exception("Error generating answer: %s", e)
            return "Unable to generate an answer. Please try rephrasing your question or check if the vector store is properly initialized."

    async def ask_stream(self, question: str, show_sources: bool = True) -> AsyncGenerator[str, None]:
        """Async generator that streams tokens from the LLM."""
        try:
            retriever = self.vector_store.get_retriever(k=self.retriever_k)
            docs = retriever.invoke(question)

            context = "\n\n".join(doc.page_content for doc in docs)
            formatted_prompt = self.prompt.format(context=context, question=question)

            chat_llm = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                num_ctx=self.num_ctx,
                temperature=self.temperature,
            )

            async for chunk in chat_llm.astream([HumanMessage(content=formatted_prompt)]):
                token = chunk.content
                if token:
                    yield token

            if show_sources and docs:
                sources_text = "\n\nSources:"
                seen: set[tuple[str, str]] = set()
                idx = 1
                for doc in docs:
                    source = doc.metadata.get("source", "Unknown")
                    page = doc.metadata.get("page", "N/A")
                    display_source = os.path.splitext(os.path.basename(source))[0]
                    key = (display_source, str(page))
                    if key in seen:
                        continue
                    seen.add(key)
                    sources_text += f"\n{idx}. {display_source} (Page {page})"
                    idx += 1
                yield sources_text

        except Exception as e:
            logger.exception("Error during streaming answer: %s", e)
            yield "Unable to generate an answer. Please try rephrasing your question."

    def chat(self) -> None:
        logger.info("Starting interactive chat session (Model: %s)", self.model_name)
        print(f"\n{'=' * 60}")
        print(f"AI RAG Chatbot (Model: {self.model_name})")
        print(f"{'=' * 60}")
        print("Type 'quit' or 'exit' to end the conversation.\n")

        while True:
            try:
                question = input("You: ").strip()
                if question.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break
                if not question:
                    continue
                answer = self.ask(question)
                print(f"\nBot: {answer}\n")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
