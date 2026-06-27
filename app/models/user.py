from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    """
    Modello Utente
    """
    
    username: str = Field(primary_key=True)
    name: str
    email: str
    saldo: float = Field(default=10)
    numero_carta: str # (| None = Field(default=None) ) codice da inserire per il progetto realistico, se si toglie API richiesta dal prof non puo funzionare bene su questa API(register to event)
    cvv_carta: str # (| None = Field(default=None)) codice da inserire per il progetto realistico, se si toglie API richiesta dal prof non puo funzionare bene su questo API(register to event)


