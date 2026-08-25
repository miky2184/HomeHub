from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import TrainingSession as TrainingSessionModel
from app.schemas.common import TrainingActivityDetail, TrainingSessionOut
from app.services.aggregator import dieta_activity_summary, get_dieta_activity, get_garmin_scheduled_workout

router = APIRouter(prefix="/api/training", tags=["training"])


@router.get("/week", response_model=list[TrainingSessionOut])
async def get_week_training(week_start_date: date, db: Session = Depends(get_db)) -> list[TrainingSessionOut]:
    """Il piano della settimana viene letto prima di tutto da Garmin Connect
    (dove l'utente assegna gli allenamenti ai giorni). Gli allenamenti
    svolti si leggono invece da dieta.allenamento (altra web app
    dell'utente, dati più ricchi della sola API Garmin). Un giorno compare
    nell'elenco se ha ALMENO UNA delle tre cose: un piano da Garmin, un
    allenamento svolto (anche non pianificato, es. una sessione spontanea),
    o un inserimento manuale preesistente — quest'ultimo resta un fallback
    per i casi non coperti dagli altri due. Vedi ARCHITECTURE.md e la
    docstring di adapters/garmin.py."""
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

        scheduled = await get_garmin_scheduled_workout(session_date)
        garmin_title = scheduled["title"] if scheduled else None
        # Il futuro non ha ancora attività svolte: ha senso controllare
        # dieta.allenamento solo per oggi o giorni già passati.
        activity = get_dieta_activity(db, session_date) if session_date <= today else None

        if session is not None and session.from_garmin and garmin_title is None and activity is None:
            # La riga era solo uno specchio del piano Garmin per questo
            # giorno, e Garmin non lo pianifica più (spostato altrove,
            # rimosso...): niente da mostrare più qui, altrimenti resta un
            # allenamento fantasma per sempre (Garmin non "cancella" mai
            # quello che abbiamo già scritto, aggiorna solo se c'è un piano
            # attuale — vedi sotto).
            db.delete(session)
            db.commit()
            session = None

        effective_text = garmin_title or (session.session_text if session else None) or (
            activity.titolo if activity else None
        )
        if effective_text is None:
            continue  # nessun piano, né svolto né pianificato, per questo giorno

        if session is None:
            session = TrainingSessionModel(
                week_start_date=week_start_date,
                day_of_week=day_of_week,
                session_text=effective_text,
                done=bool(activity),
                from_garmin=bool(garmin_title),
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        else:
            changed = False
            if garmin_title and session.session_text != garmin_title:
                session.session_text = garmin_title
                changed = True
            if garmin_title and not session.from_garmin:
                session.from_garmin = True
                changed = True
            if activity and not session.done:
                session.done = True
                changed = True
            if changed:
                db.commit()

        garmin_note = dieta_activity_summary(activity) if activity else None
        # Priorità allo sport dell'attività SVOLTA (dato certo) sul quello
        # solo pianificato, se per qualche motivo differiscono.
        sport_type = (activity.tipo if activity else None) or (scheduled["sport_type"] if scheduled else None)

        results.append(
            TrainingSessionOut(
                id=session.id,
                week_start_date=session.week_start_date,
                day_of_week=session.day_of_week,
                session_text=session.session_text,
                done=session.done,
                garmin_note=garmin_note,
                sport_type=sport_type,
            )
        )
    return results


@router.get("/activity/{activity_date}", response_model=TrainingActivityDetail)
def get_activity_detail(activity_date: date, db: Session = Depends(get_db)) -> TrainingActivityDetail:
    """Dettaglio completo dell'allenamento svolto in una data (per la modale
    di dettaglio in UI) — da dieta.allenamento, non da Garmin direttamente."""
    activity = get_dieta_activity(db, activity_date)
    if not activity:
        raise HTTPException(status_code=404, detail="Nessun allenamento svolto trovato per questa data")
    return activity


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
