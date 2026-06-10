import json
from json import JSONDecodeError

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.rag_graph import ask_multi_agent
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import ChatMessage, User
from app.schemas.schemas import AskIn, AskOut

router = APIRouter(prefix="/chat", tags=["Chat"])


def _safe_json_loads(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, JSONDecodeError):
        return fallback


@router.post("/ask", response_model=AskOut)
def ask(payload: AskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        result = ask_multi_agent(payload.question, payload.top_k, owner_id=user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG pipeline failed: {exc}") from exc

    chat = ChatMessage(
        question=payload.question,
        answer=result["answer"],
        citations_json=json.dumps(result["citations"]),
        workflow_json=json.dumps(result["workflow"]),
        owner_id=user.id,
    )
    db.add(chat)
    db.commit()
    return {"answer": result["answer"], "citations": result["citations"], "workflow": result["workflow"]}


@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.owner_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "question": r.question,
            "answer": r.answer,
            "citations": _safe_json_loads(r.citations_json, []),
            "workflow": _safe_json_loads(r.workflow_json, []),
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.delete("/history/{message_id}")
def delete_history_message(
    message_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = (
        db.query(ChatMessage)
        .filter(ChatMessage.id == message_id, ChatMessage.owner_id == user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Chat history item not found")

    db.delete(row)
    db.commit()
    return {"message": "Chat history item deleted", "id": message_id}


@router.delete("/history")
def clear_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    deleted = db.query(ChatMessage).filter(ChatMessage.owner_id == user.id).delete()
    db.commit()
    return {"message": "Conversation history cleared", "deleted": deleted}
