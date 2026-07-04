# polls.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from voting.db import get_db
from voting.models import Option, Poll
from voting.schemas import PollCreate, PollDetail, PollSummary

router = APIRouter(prefix="/polls", tags=["polls"])


# POST /polls
@router.post("", status_code=status.HTTP_201_CREATED, response_model=PollDetail)
def create_poll(payload: PollCreate, db: Session = Depends(get_db)) -> Poll:
    poll = Poll(title=payload.title, closes_at=payload.closes_at)
    poll.options = [Option(label=label) for label in payload.options]
    db.add(poll)
    db.commit()
    db.refresh(poll)
    return poll


# GET /polls
@router.get("", response_model=list[PollSummary])
def list_polls(db: Session = Depends(get_db)) -> list[Poll]:
    stmt = select(Poll).order_by(Poll.id.desc())
    return list(db.scalars(stmt).all())


# GET /polls/{poll_id}
@router.get("/{poll_id}", response_model=PollDetail)
def get_poll(poll_id: int, db: Session = Depends(get_db)) -> Poll:
    stmt = (
        select(Poll)
        .where(Poll.id == poll_id)
        .options(selectinload(Poll.options))
    )
    poll = db.scalars(stmt).one_or_none()
    if poll is None:
        raise HTTPException(status_code=404, detail="poll not found")
    return poll
