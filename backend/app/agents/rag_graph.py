from __future__ import annotations

from typing import Any, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.core.config import get_settings
from app.services.vector_store import similarity_search


class RAGState(TypedDict):
    question: str
    top_k: int
    owner_id: int | None
    retrieved: list[dict]
    analysis: str
    summary: str
    verification: str
    answer: str
    citations: list[dict]
    workflow: list[dict]


def _llm() -> ChatOpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to your .env file before asking questions.")
    return ChatOpenAI(model=settings.openai_model, temperature=0.1, api_key=settings.openai_api_key)


def _context(retrieved: list[dict]) -> str:
    blocks = []
    for idx, item in enumerate(retrieved, start=1):
        meta = item.get("metadata", {})
        blocks.append(
            f"[Source {idx}] file={meta.get('source')} page={meta.get('page')} "
            f"chunk={meta.get('chunk_id')}\n{item.get('content')}"
        )
    return "\n\n".join(blocks)


def retriever_agent(state: RAGState) -> RAGState:
    retrieved = similarity_search(
        state["question"],
        top_k=state.get("top_k", 5),
        owner_id=state.get("owner_id"),
    )
    state["retrieved"] = retrieved
    state["workflow"].append(
        {"agent": "Retriever Agent", "status": "complete", "detail": f"Retrieved {len(retrieved)} chunks"}
    )
    return state


def analyzer_agent(state: RAGState) -> RAGState:
    if not state["retrieved"]:
        state["analysis"] = "No relevant retrieved context was found."
    else:
        prompt = (
            "Analyze the retrieved context for the question. Do not invent facts.\n"
            f"Question: {state['question']}\nContext:\n{_context(state['retrieved'])}"
        )
        state["analysis"] = _llm().invoke(prompt).content
    state["workflow"].append({"agent": "Analyzer Agent", "status": "complete", "detail": "Context analyzed"})
    return state


def summarizer_agent(state: RAGState) -> RAGState:
    if not state["retrieved"]:
        state["summary"] = "No evidence available from uploaded documents."
    else:
        prompt = (
            "Summarize only the evidence relevant to the user question.\n"
            f"Question: {state['question']}\nAnalysis:\n{state['analysis']}"
        )
        state["summary"] = _llm().invoke(prompt).content
    state["workflow"].append({"agent": "Summarizer Agent", "status": "complete", "detail": "Evidence summarized"})
    return state


def hallucination_checker_agent(state: RAGState) -> RAGState:
    if not state["retrieved"]:
        state["verification"] = "FAIL: No source context was retrieved."
    else:
        prompt = (
            "Check whether the summary is grounded in the provided context. "
            "Return PASS or FAIL with brief reason.\n"
            f"Context:\n{_context(state['retrieved'])}\nSummary:\n{state['summary']}"
        )
        state["verification"] = _llm().invoke(prompt).content
    state["workflow"].append(
        {"agent": "Hallucination Checker Agent", "status": "complete", "detail": state["verification"][:160]}
    )
    return state


def final_answer_agent(state: RAGState) -> RAGState:
    if not state["retrieved"]:
        state["answer"] = "I don't know based on the uploaded documents. No relevant source chunks were found."
        state["citations"] = []
    else:
        prompt = (
            "Create a clear final answer using only the context. Include source numbers inline like [Source 1]. "
            "If the answer is missing, say you do not know.\n"
            f"Question: {state['question']}\nContext:\n{_context(state['retrieved'])}\n"
            f"Summary:\n{state['summary']}\nVerification:\n{state['verification']}"
        )
        state["answer"] = _llm().invoke(prompt).content
        state["citations"] = [
            {
                "source": item.get("metadata", {}).get("source", "unknown"),
                "chunk_id": item.get("metadata", {}).get("chunk_id"),
                "page": str(item.get("metadata", {}).get("page", "unknown")),
                "content_preview": item.get("content", "")[:220],
            }
            for item in state["retrieved"]
        ]

    state["workflow"].append(
        {"agent": "Final Answer Agent", "status": "complete", "detail": "Final answer generated with citations"}
    )
    return state


def build_rag_graph():
    graph = StateGraph(RAGState)
    graph.add_node("retrieve", retriever_agent)
    graph.add_node("analyze", analyzer_agent)
    graph.add_node("summarize", summarizer_agent)
    graph.add_node("verify", hallucination_checker_agent)
    graph.add_node("final", final_answer_agent)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "summarize")
    graph.add_edge("summarize", "verify")
    graph.add_edge("verify", "final")
    graph.add_edge("final", END)
    return graph.compile()


def ask_multi_agent(question: str, top_k: int = 5, owner_id: int | None = None) -> dict[str, Any]:
    app = build_rag_graph()
    initial = {
        "question": question,
        "top_k": top_k,
        "owner_id": owner_id,
        "retrieved": [],
        "analysis": "",
        "summary": "",
        "verification": "",
        "answer": "",
        "citations": [],
        "workflow": [],
    }
    return app.invoke(initial)
