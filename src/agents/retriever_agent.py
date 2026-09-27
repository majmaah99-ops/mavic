# src/agents/retriever_agent.py
from src.rag.retrieval import search_sources

class RetrieverAgent:
    def run(self, query: str, top_k=2):
        return search_sources(query, top_k=top_k)
