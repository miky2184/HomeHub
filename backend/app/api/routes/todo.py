from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import TodoItem
from app.schemas.common import TodoItemCreate, TodoItemOut, TodoItemUpdate
from app.services.aggregator import sort_todos, todo_item_out

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("", response_model=list[TodoItemOut])
def list_todos(include_done: bool = True, db: Session = Depends(get_db)) -> list[TodoItemOut]:
    """Tutta la lista, ordinata per priorità/scadenza (vedi sort_todos).
    include_done=false per la vista "solo da fare" del tab Todo."""
    items = db.scalars(select(TodoItem)).all()
    if not include_done:
        items = [i for i in items if not i.done]
    return [todo_item_out(i) for i in sort_todos(items)]


@router.post("", response_model=TodoItemOut, status_code=201)
def create_todo(payload: TodoItemCreate, db: Session = Depends(get_db)) -> TodoItemOut:
    item = TodoItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return todo_item_out(item)


@router.patch("/{todo_id}", response_model=TodoItemOut)
def update_todo(todo_id: int, payload: TodoItemUpdate, db: Session = Depends(get_db)) -> TodoItemOut:
    """PATCH parziale: usato sia dal form di modifica (titolo/priorità/
    scadenza/assegnatario) sia dal semplice toggle "fatto" ({"done": true})."""
    item = db.get(TodoItem, todo_id)
    if not item:
        raise HTTPException(status_code=404, detail="Todo non trovato")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return todo_item_out(item)


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)) -> None:
    item = db.get(TodoItem, todo_id)
    if not item:
        raise HTTPException(status_code=404, detail="Todo non trovato")
    db.delete(item)
    db.commit()
