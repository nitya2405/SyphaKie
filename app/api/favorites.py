"""Saved generations (favorites)."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.favorite import Favorite
from app.models.request_record import RequestRecord

router = APIRouter()


class SaveRequest(BaseModel):
    request_id: str
    note: str | None = None


@router.post("/favorites")
def save_generation(
    body: SaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(RequestRecord).filter_by(id=body.request_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Request not found.")
    existing = db.query(Favorite).filter_by(user_id=current_user.id, request_id=body.request_id).first()
    if existing:
        if body.note is not None:
            existing.note = body.note
            db.commit()
        return {"favorite": _ser(existing)}
    fav = Favorite(id=uuid.uuid4(), user_id=current_user.id, request_id=uuid.UUID(body.request_id), note=body.note)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return {"favorite": _ser(fav)}


@router.delete("/favorites/{request_id}")
def unsave_generation(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fav = db.query(Favorite).filter_by(user_id=current_user.id, request_id=request_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="Not saved.")
    db.delete(fav)
    db.commit()
    return {"ok": True}


@router.get("/favorites")
def list_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favs = (
        db.query(Favorite, RequestRecord)
        .join(RequestRecord, Favorite.request_id == RequestRecord.id)
        .filter(Favorite.user_id == current_user.id)
        .order_by(desc(Favorite.created_at))
        .all()
    )
    return {
        "favorites": [
            {
                **_ser(fav),
                "request": {
                    "request_id": str(rec.id),
                    "modality": rec.modality,
                    "provider": rec.provider,
                    "model": rec.model_id,
                    "status": rec.status,
                    "prompt": rec.input_payload.get("prompt") if rec.input_payload else None,
                    "output_content": rec.output_content,
                    "output_url": rec.output_url,
                    "output_path": rec.output_path,
                    "credits_deducted": rec.credits_deducted,
                    "created_at": rec.created_at.isoformat() if rec.created_at else None,
                },
            }
            for fav, rec in favs
        ]
    }


@router.get("/favorites/ids")
def list_favorite_ids(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lightweight endpoint — just the set of saved request_ids for the current user."""
    ids = db.query(Favorite.request_id).filter_by(user_id=current_user.id).all()
    return {"ids": [str(r[0]) for r in ids]}


def _ser(f: Favorite) -> dict:
    return {
        "id": str(f.id),
        "request_id": str(f.request_id),
        "note": f.note,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }
