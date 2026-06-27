from datetime import datetime
from sqlmodel import SQLModel, Field

class  Event(SQLModel, table=True):
    """
    Modello evento
    """
    
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str
    date: datetime
    location: str
    chips: int
    buy_in:float
    montepremi: int
    end_late_reg: datetime