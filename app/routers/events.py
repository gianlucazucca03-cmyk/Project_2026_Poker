from fastapi import APIRouter, HTTPException
from datetime import datetime
from sqlmodel import SQLModel, select

from app.data.db import SessionDep
from app.models.event import Event
from app.models.user import User
from app.models.registration import Registration



router = APIRouter(prefix="/events", tags=["events"])

class EventCreate(SQLModel):
    """
    Dati necessari per creare un torneo poker.
    """

    title: str
    description: str
    date: datetime
    location: str
    chips: int
    buy_in: float
    montepremi: int
    end_late_reg: datetime


class UserCreate(SQLModel):
    """
    Dati necessari per registrare un giocatore a un torneo.
    """

    username: str
    name: str
    email: str
    numero_carta: str #da tenere poiche senza un  utente creato non avrebbe carta e cvv (per tenere la richiesta del prof l iscrizione dovra avere anche cvv e numero carta)
    cvv_carta: str    # senza questo piccolo dettaglio si possono togliere per rendere il progetto piu realistico

def validate_card(numero_carta: str, cvv_carta: str):
    """
    Controlla che numero carta e CVV siano formalmente validi.
    """
    if len(numero_carta) != 16 or not numero_carta.isdigit():
        raise HTTPException(
            status_code=422,
            detail="Il numero della carta deve contenere esattamente 16 cifre",
        )

    if len(cvv_carta) != 3 or not cvv_carta.isdigit():
        raise HTTPException(
            status_code=422,
            detail="Il CVV deve contenere esattamente 3 cifre",
        )


def validate_name(name: str):
    cleaned_name = name.replace(" ", "")

    if not cleaned_name.isalpha():
        raise HTTPException(
            status_code=422,
            detail="Il nome deve contenere solo lettere e spazi",
        )


@router.get("")
def get_events(session: SessionDep):
    """
    Restituisce tutti gli eventi presenti nel database.
    """
    return session.exec(select(Event)).all()


@router.post("", status_code=201)
def create_event(event_data: EventCreate, session: SessionDep):
    """
    Crea un nuovo evento.
    """
    event = Event(
        title=event_data.title,
        description=event_data.description,
        date=event_data.date,
        location=event_data.location,
        chips=event_data.chips,
        buy_in=event_data.buy_in,
        montepremi=event_data.montepremi,
        end_late_reg=event_data.end_late_reg,
        )
    session.add(event)
    session.commit()
    session.refresh(event)

    return event


@router.get("/{event_id}")
def get_event(event_id: int, session: SessionDep):
    """
    Restituisce un evento dato il suo id.
    """
    event = session.get(Event, event_id)

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return event


@router.put("/{event_id}")
def update_event(event_id: int, event_data: EventCreate, session: SessionDep):
    """
    Aggiorna un evento esistente.
    """
    event = session.get(Event, event_id)

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    event.title = event_data.title
    event.description = event_data.description
    event.date = event_data.date
    event.location = event_data.location
    event.chips = event_data.chips
    event.buy_in = event_data.buy_in
    event.montepremi = event_data.montepremi
    event.end_late_reg = event_data.end_late_reg


    session.add(event)
    session.commit()
    session.refresh(event)

    return event



@router.post("/{event_id}/register", status_code=201)
def register_to_event(event_id: int, user_data: UserCreate, session: SessionDep):
    """
    Registra un utente a un evento.
    Se l'utente non esiste, viene creato automaticamente.
    """
    event = session.get(Event, event_id)
    #controllo evento
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
        
    now = datetime.now()

    if now > event.end_late_reg:
        raise HTTPException(
            status_code=400,
            detail="Registrazione tardiva terminata",
        )
    
      
    existing_user = session.get(User, user_data.username)
    
    #controllo user
    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    #controllo email
    existing_email = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()

    if existing_email is not None  and existing_email.username != user_data.username:
        raise HTTPException(
            status_code=400,
            detail="Email already exists, no multi-account"
        )

    #controllo carta
    existing_card = session.exec(
        select(User).where(User.numero_carta == user_data.numero_carta)
    ).first()
    
    if existing_card is not None and existing_card.username != user_data.username:
        raise HTTPException(
            status_code=400,
            detail="Card already exists"
        )
    raise HTTPException(status_code=400, detail="Card already exists, no multi-account")
    
    #controllo vincoli carte e cvv
    validate_card(user_data.numero_carta, user_data.cvv_carta)
    #controllo nome vincolo
    validate_name(user_data.name)

    user = session.get(User, user_data.username)
    
    
    if user is None:
        user = User(
            username=user_data.username,
            name=user_data.name,
            email=user_data.email,
            numero_carta=user_data.numero_carta,    #togliere per progetto realistico, tenere per la richiesta del prof sul API
            cvv_carta=user_data.cvv_carta,          #togliere per progetto realistico, tenere per la richiesta del prof sul API
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    existing_registration = session.get(
        Registration,
        (user_data.username, event_id),
    )

    if existing_registration is not None:
        return existing_registration
    
    if user.saldo < event.buy_in:
        raise HTTPException(
            status_code=400,
            detail="Saldo insufficiente per iscriversi al torneo",
        )

    user.saldo -= event.buy_in
    session.add(user)
    session.commit()
    session.refresh(user)
    
    registration = Registration(
        username=user_data.username,
        event_id=event_id,
    )

    session.add(registration)
    session.commit()
    session.refresh(registration)

    return registration


@router.delete("")
def delete_all_events(session: SessionDep):
    """
    Elimina tutti gli eventi e tutte le registrazioni associate.
    """
    registrations = session.exec(select(Registration)).all()

    for registration in registrations:
        session.delete(registration)

    events = session.exec(select(Event)).all()

    for event in events:
        session.delete(event)

    session.commit()

    return {"message": "All events deleted"}


@router.delete("/{event_id}")
def delete_event(event_id: int, session: SessionDep):
    """
    Elimina un evento e tutte le registrazioni associate.
    """
    event = session.get(Event, event_id)

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    registrations = session.exec(
        select(Registration).where(Registration.event_id == event_id)
    ).all()

    for registration in registrations:
        session.delete(registration)

    session.delete(event)
    session.commit()

    return {"message": "Event deleted"}
    
    
