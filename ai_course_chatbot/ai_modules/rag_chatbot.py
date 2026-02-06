"""
RAG Chatbot Module
Implements a Retrieval-Augmented Generation chatbot using Ollama.
"""

from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from vector_store import VectorStore


class RAGChatbot:
    """RAG-based chatbot using Ollama for LLM."""

    def __init__(self, vector_store: VectorStore,
                 model_name: str = "llama2",
                 temperature: float = 0.7):
        """
        Initialize the RAG chatbot.
        
        Args:
            vector_store: Vector store instance for retrieval
            model_name: Name of the Ollama model to use
            temperature: Temperature for text generation
        """
        self.vector_store = vector_store
        self.model_name = model_name

        # Initialize Ollama LLM
        self.llm = Ollama(
            model=model_name,
            temperature=temperature
        )

        # Create custom prompt template
        self.prompt_template = """Use the following pieces of context to answer the question at the end.  
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Context: {context}
        Question: {question}
        Answer:"""

        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )

        # Create retrieval QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.get_retriever(),
            return_source_documents=True,
            chain_type_kwargs={"prompt": self.prompt}
        )

    def ask(self, question: str, show_sources: bool = True) -> str:
        """
        Ask a question to the chatbot.
        
        Args:
            question: The question to ask
            show_sources: Whether to show source documents
            
        Returns:
            The answer from the chatbot
        """
        try:
            result = self.qa_chain({"query": question})
            answer = result["result"]

            if show_sources and "source_documents" in result:
                sources = result["source_documents"]
                if sources:
                    answer += "\n\nSources:"
                    for i, doc in enumerate(sources, 1):
                        source = doc.metadata.get("source", "Unknown")
                        page = doc.metadata.get("page", "N/A")
                        answer += f"\n{i}. {source} (Page {page})"

            return answer
        except Exception as e:
            # Log full exception for debugging while providing user-friendly message
            print(f"Debug: Exception occurred: {e}")
            return "Unable to generate an answer. Please try rephrasing your question or check if the vector store is properly initialized."

    def chat(self) -> None:
        """Interactive chat loop."""
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

                print("\nChatbot: ", end="", flush=True)
                answer = self.ask(question)
                print(answer)
                print()

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")
