
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class User(BaseModel):
    id: Optional[UUID]
    username: str
    email: str
    phoneNumber: Optional[str]
    fullName: Optional[str]
    password: str
    salt: str
    token: str
    expireAt: datetime
    

class Sede(BaseModel):
    id: Optional[UUID]
    idFranquicia: str
    nombre: str
    direccion: str
    telefono: int
    latitud: float
    longitud: float
    urlImg: str


class Turno(BaseModel):
    id: Optional[UUID]
    idCliente: UUID
    idCola: UUID
    horaInicio: datetime
    horaFin: Optional[datetime]
    fecha: datetime
    tiempoDuracion: Optional[float]
    turnoAsignado: Optional[int]
    status:str

class Cola(BaseModel):
    id: Optional[UUID]
    fecha: datetime
    turnoActual: int
    turnoMaximo: int

class resCola(BaseModel):
    id: Optional[UUID]
    idRestaurant: UUID
    idCola: UUID