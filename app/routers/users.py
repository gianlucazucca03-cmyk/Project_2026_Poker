from fastapi import APIRouter, HTTPException
from sqlmodel import SQLModel,select

from app.data.db import SessionDep
from app.models.user import User
from app.models.registration import Registration


router = APIRouter(prefix="/users", tags=["users"])

class UserCreate(SQLModel):
    username: str
    name: str
    email: str
    numero_carta: str
    cvv_carta: str

class DepositRequest(SQLModel):
    """
    Dati necessari per simulare una ricarica.
    """

    card_holder: str
    card_number: str
    card_cvv: str
    amount: float 


def validate_name(name: str):
    cleaned_name = name.replace(" ", "")

    if not cleaned_name.isalpha():
        raise HTTPException(
            status_code=422,
            detail="Il nome deve contenere solo lettere e spazi",
        )

    
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


@router.get("")
def get_users(session: SessionDep):
    """
    Restituisce tutti gli utenti presenti nel database.
    """
    return session.exec(select(User)).all()


@router.post("", status_code=201)
def create_user(user_data: UserCreate, session: SessionDep):
    """
    Crea un nuovo utente.
    """
    #controllo user
    existing_user = session.get(User, user_data.username)

    if existing_user is not None:
        raise HTTPException(status_code=400, detail="User already exists")
        
    #contollo carta
    existing_card = session.exec(
        select(User).where(User.numero_carta == user_data.numero_carta)
    ).first()

    if existing_card is not None:
        raise HTTPException(status_code=400, detail="Card already exists, no multi-account")
        
    #controllo email
    existing_email = session.exec(
        select(User).where(User.email == user_data.email)
    ).first()

    if existing_email is not None:
        raise HTTPException(
            status_code=400,
            detail="Email already exists, no multi-account"
        )
    #controllo vincolo nome
    validate_name(user_data.name)
    #controllo vincolo numerocarta e cvv
    validate_card(user_data.numero_carta, user_data.cvv_carta)
    
    user = User(
        username=user_data.username,
        name=user_data.name,
        email=user_data.email,
        numero_carta=user_data.numero_carta,
        cvv_carta=user_data.cvv_carta,
        saldo=10,
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@router.get("/{username}")
def get_user(username: str, session: SessionDep):
    """
    Restituisce un utente dato il suo username.
    """
    user = session.get(User, username)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.post("/{username}/deposit")
def deposit_balance(username: str, data: DepositRequest, session: SessionDep):
    """
    Simula una transazione e aggiunge saldo al giocatore.
    """
    user = session.get(User, username)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    validate_card(data.card_number, data.card_cvv)

    if data.card_holder.strip().lower() != user.name.strip().lower():
        raise HTTPException(
            status_code=400,
            detail="Card holder must match user name",
        )

    if data.card_number != user.numero_carta:
        raise HTTPException(status_code=400, detail="Invalid card number")

    if data.card_cvv != user.cvv_carta:
        raise HTTPException(status_code=400, detail="Invalid CVV")

    user.saldo += data.amount

    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "message": "Deposit completed",
        "username": user.username,
        "saldo": user.saldo,
    }

@router.delete("")
def delete_all_users(session: SessionDep):
    """
    Elimina tutti gli utenti e tutte le registrazioni associate.
    """
    registrations = session.exec(select(Registration)).all()

    for registration in registrations:
        session.delete(registration)

    users = session.exec(select(User)).all()

    for user in users:
        session.delete(user)

    session.commit()

    return {"message": "All users deleted"}


@router.delete("/{username}")
def delete_user(username: str, session: SessionDep):
    """
    Elimina un utente e tutte le sue registrazioni.
    """
    user = session.get(User, username)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    registrations = session.exec(
        select(Registration).where(Registration.username == username)
    ).all()

    for registration in registrations:
        session.delete(registration)

    session.delete(user)
    session.commit()

    return {"message": "User deleted"}
    

