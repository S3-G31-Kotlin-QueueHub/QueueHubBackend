from sqlalchemy import (
    Column,
    DateTime,
    String,
    Table,
    Enum,
    Float,
    Integer, CheckConstraint,
    Sequence
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid

Base = declarative_base()

class UserStatus(enum.Enum):
    POR_VERIFICAR = "POR_VERIFICAR"
    NO_VERIFICADO = "NO_VERIFICADO"
    VERIFICADO = "VERIFICADO"

turno_actual_sequence = Sequence('turno_actual_seq')
users = Table (

    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True,
           default=uuid.uuid4, index=True),
    Column("username", String(), nullable=False,
           index=True, unique=True),
    Column("email", String(), nullable=False,
           unique=True),
    Column("phoneNumber", String(), nullable=True),
    Column("fullName", String(), nullable=True),
    Column("password", String(), nullable=False),
    Column("salt", String(), nullable=False),
    Column("token", String(), nullable=False),
    Column("expireAt", DateTime(), nullable=False)

)

sedes = Table (

    "sedes",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True,
           default=uuid.uuid4, index=True),
    Column("idFranquicia", String(), nullable=False,
           index=True, unique=True),
    Column("nombre", String(), nullable=False,
           unique=True),
    Column("telefono", Integer(), nullable=True),
    Column("direccion", String(), nullable=False),
    Column("latitud", Float(), nullable=False),
    Column("longitud", Float(), nullable=False),
    Column("urlImg", String(), nullable=False),
    

)

turnos = Table (

    "turnos",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True,
           default=uuid.uuid4, index=True),
    Column("idCliente", UUID(as_uuid=True), nullable=False,
           index=True, unique=True),
    Column("idCola", UUID(as_uuid=True), nullable=False),
    Column("horaInicio", DateTime(), nullable=True),
    Column("horaFin", DateTime(), nullable=True),
    Column("fecha", DateTime(), nullable=False),
    Column("tiempoDuracion", Float(), nullable=True),
    Column("turnoAsignado", Integer(), nullable=False,
              default=turno_actual_sequence),
      Column("status", String(), nullable=False),  
    CheckConstraint("status IN ('CANCELADA', 'FINALIZADA', 'PENDIENTE')", name="check_status")  
)

colas = Table (

    "colas",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True,
           default=uuid.uuid4, index=True),
    Column("fecha", DateTime(), nullable=True),
    Column("turnoActual", Integer(), nullable=False),
    Column("turnoMaximo", Integer(), nullable=False))
 
resColas = Table (

    "resColas",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True,
           default=uuid.uuid4, index=True),
    Column("idRestaurant", UUID(as_uuid=True), nullable=False),
    Column("idCola", UUID(as_uuid=True), nullable=False)
    )
 
