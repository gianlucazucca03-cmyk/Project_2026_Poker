from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.data.db import SessionDep
from app.models.event import Event
from app.models.user import User
from app.models.registration import Registration


router = APIRouter(prefix="/registrations", tags=["registrations"])


@router.get("")
def get_registrations(session: SessionDep):
    """
    Restituisce tutte le registrazioni presenti nel database.
    """
    return session.exec(select(Registration)).all()


@router.delete("")
def delete_registration(username: str, event_id: int, session: SessionDep):
    """
    Elimina una registrazione tramite username ed event_id.
    """
    user = session.get(User, username)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    event = session.get(Event, event_id)

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    registration = session.get(Registration, (username, event_id))

    if registration is None:
        raise HTTPException(status_code=404, detail="Registration not found")

    session.delete(registration)
    session.commit()

    return {"message": "Registration deleted"}