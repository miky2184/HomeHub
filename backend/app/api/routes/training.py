from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import TrainingSession as TrainingSessionModel
from app.schemas.common import TrainingSessionOut, TrainingSessionUpsert
from app.services.aggregator import get_garmin_activities_for_date

router = APIRouter(prefix="/api/training", tags=["training"])


@router.get("/week", response_model=list[TrainingSessionOut])
async def get_week_training(week_start_date: date, db: Session = Depends(get_db)) -> list[TrainingSessionOut]:
    sessions = db.scalars(
        select(TrainingSessionModel).where(TrainingSessionModel.week_start_date == week_start_date)
    ).all()

    today = date.today()
    results: list[TrainingSessionOut] = []
    for s in sessions:
        session_date = week_start_date + timedelta(days=s.day_of_week)
        garmin_note = None

        # Ha senso controllare Garmin solo per giorni già passati (o oggi):
        # il futuro non ha ancora attività registrate.
        if session_date <= today:
            activities = await get_garmin_activities_for_date(session_date)
            if activities:
                garmin_note = activities[0]["summary"]
                if not s.done:
                    s.done = True
                    db.commit()

        results.append(
            TrainingSessionOut(
                id=s.id,
                week_start_date=s.week_start_date,
                day_of_week=s.day_of_week,
                session_text=s.session_text,
                done=s.done,
                garmin_note=garmin_note,
            )
        )
    return results


@router.put("", response_model=TrainingSessionOut)
def upsert_training_session(
    payload: TrainingSessionUpsert, db: Session = Depends(get_db)
) -> TrainingSessionOut:
    session = db.scalar(
        select(TrainingSessionModel).where(
            TrainingSessionModel.week_start_date == payload.week_start_date,
            TrainingSessionModel.day_of_week == payload.day_of_week,
        )
    )
    if session:
        session.session_text = payload.session_text
    else:
        session = TrainingSessionModel(**payload.model_dump(), done=False)
        db.add(session)
    db.commit()
    db.refresh(session)
    return TrainingSessionOut(
        id=session.id,
        week_start_date=session.week_start_date,
        day_of_week=session.day_of_week,
        session_text=session.session_text,
        done=session.done,
    )


@router.patch("/{session_id}/done", response_model=TrainingSessionOut)
def mark_training_done(session_id: int, done: bool = True, db: Session = Depends(get_db)) -> TrainingSessionOut:
    session = db.get(TrainingSessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    session.done = done
    db.commit()
    db.refresh(session)
    return TrainingSessionOut(
        id=session.id,
        week_start_date=session.week_start_date,
        day_of_week=session.day_of_week,
        session_text=session.session_text,
        done=session.done,
    )
