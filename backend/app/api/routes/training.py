from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import TrainingSession as TrainingSessionModel
from app.schemas.common import TrainingSessionOut, TrainingSessionUpsert
from app.services.aggregator import get_garmin_activity_summaries, get_garmin_scheduled_title

router = APIRouter(prefix="/api/training", tags=["training"])


@router.get("/week", response_model=list[TrainingSessionOut])
async def get_week_training(week_start_date: date, db: Session = Depends(get_db)) -> list[TrainingSessionOut]:
    """Il piano della settimana viene letto prima di tutto da Garmin Connect
    (dove l'utente assegna gli allenamenti ai giorni): se Garmin ha un
    allenamento pianificato per un giorno, il suo titolo sostituisce/crea la
    sessione salvata in Postgres. L'inserimento manuale resta un fallback
    per i giorni senza nulla di assegnato su Garmin (o se Garmin non è
    configurato) — vedi ARCHITECTURE.md e la docstring di adapters/garmin.py."""
    existing = {
        s.day_of_week: s
        for s in db.scalars(
            select(TrainingSessionModel).where(TrainingSessionModel.week_start_date == week_start_date)
        ).all()
    }

    today = date.today()
    results: list[TrainingSessionOut] = []

    for day_of_week in range(7):
        session_date = week_start_date + timedelta(days=day_of_week)
        session = existing.get(day_of_week)

        garmin_title = await get_garmin_scheduled_title(session_date)
        if garmin_title:
            if session is None:
                session = TrainingSessionModel(
                    week_start_date=week_start_date,
                    day_of_week=day_of_week,
                    session_text=garmin_title,
                    done=False,
                )
                db.add(session)
                db.commit()
                db.refresh(session)
            elif session.session_text != garmin_title:
                session.session_text = garmin_title
                db.commit()

        if session is None:
            continue  # nessun piano, né da Garmin né manuale, per questo giorno

        garmin_note = None
        # Ha senso controllare le attività svolte solo per giorni già
        # passati (o oggi): il futuro non ne ha ancora.
        if session_date <= today:
            summaries = await get_garmin_activity_summaries(session_date)
            if summaries:
                garmin_note = "; ".join(summaries)
                if not session.done:
                    session.done = True
                    db.commit()

        results.append(
            TrainingSessionOut(
                id=session.id,
                week_start_date=session.week_start_date,
                day_of_week=session.day_of_week,
                session_text=session.session_text,
                done=session.done,
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
