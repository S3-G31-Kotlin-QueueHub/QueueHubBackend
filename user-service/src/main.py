from fastapi import FastAPI, HTTPException, status, Depends, Header
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from hashlib import sha256
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from src.schemas import (
    User, Sede, Cola, Turno, resCola
)
from src.models import (
    users, Base, colas, sedes, resColas, turnos
)

app = FastAPI()

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")


 
engine = create_engine(
    f"postgresql+psycopg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}", echo=True
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)

@app.get("/ping")
def healthCheck():
    return "pong"

@app.get("/users", response_model=List[User])
def getUsers():
    with engine.connect() as c:
        result = c.execute(text("SELECT * FROM users"))
        return result.all()
 
@app.get("/restaurants/top/{top}", response_model=List[Sede])
def getRestaurants(top:int):
    with engine.connect() as c:
        result = c.execute(text("SELECT * FROM sedes"))
        return result.fetchmany(top)
    
@app.get("/restaurants", response_model=List[Sede])
def getAllRestaurants():
    with engine.connect() as c:
        result = c.execute(text("SELECT * FROM sedes"))
        return result.all()

@app.get("/turnos", response_model=List[Turno])
def getTurnos():
    with engine.connect() as c:
        result = c.execute(text("SELECT * FROM turnos"))
        return result.all()

@app.get("/colas", response_model=List[Cola])
def getColas():
    with engine.connect() as c:
        result = c.execute(text("SELECT * FROM colas"))
        return result.all()
     
def getUser(username: str):
    with engine.connect() as c:
        stmt = users.select().where(users.c.username == username)
        result = c.execute(stmt).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result

def getSede(id: str):
    with engine.connect() as c:
        stmt = sedes.select().where(sedes.c.id == id )
        result = c.execute(stmt).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="Sede not found")
        
        return result
    
def getSedeByName(nombre: str):
    with engine.connect() as c:
        stmt = sedes.select().where(sedes.c.nombre == nombre )
        result = c.execute(stmt).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="Sede not found")
        return result
@app.post("/users")
def addUser(user:dict):
   
    if user.get('password') is None or user.get('username') is None or user.get('fullName') is None or  user.get('email') is None:
        raise HTTPException(status_code=400, detail="User incomplete data")
    
    salt = user['username'][:2] + user['fullName'][1]
    user["password"]= sha256((user['password']+salt).encode("utf-8")).hexdigest()
    user["salt"] =  salt
    user["token"]= "temp"
    user["expireAt"]= datetime.now()
  
    with engine.connect() as c:
        try:
            getUser(user['username'])
            return "Cannot create User, already exists"
        except HTTPException as e:
            try:
                c.execute(users.insert().values(user))
                c.commit()
                final = getUser(user['username'])
                
                response = JSONResponse(
                    content={"id": str(final[0]), "username": str(final[-5])},
                    status_code=201
                )
               
                return response
            except IntegrityError as ie:
                raise HTTPException(status_code=400, detail="User invalid data") from ie
            

@app.post("/restaurants")
def addSede(restaurant:dict):
    necesary = ['idFranquicia', 'nombre', 'direccion', 'telefono','latitud', 'longitud']
    for i in necesary:
        if i not in restaurant:
            raise HTTPException(status_code=412, detail="Restaurant data incomplete data. %s Missing"%(i))

    restaurant["urlImg"]= f"/restaurants/{restaurant['nombre'].replace(' ','')}/photo/icon" 
    with engine.connect() as c:
        try:
            getSedeByName(restaurant['nombre'])
            return "Cannot create Restaurant, already exists"
        except HTTPException as e:
            try:
                c.execute(sedes.insert().values(restaurant))
                c.commit()
                final = getSedeByName(restaurant['nombre'])
                
                response = JSONResponse(
                    content={"id": str(final[0]), "username": str(final[-5])},
                    status_code=201 
                )
               
                return response
            except IntegrityError as ie:
                raise HTTPException(status_code=400, detail="User invalid data") from ie


@app.post("/restaurant/{idRestaurant}/cola", response_model=Cola)
def addCola(idRestaurant):
    result = getSede(idRestaurant)
    if result is None:
        return "Cannot create queue for a non-existing restaurant"
    cola = {
        'fecha' : datetime.now(),
        'turnoMaximo' : 1000,
        'turnoActual' : 0,
        'id': uuid.uuid4()

    }
    with engine.connect() as c:

            result = c.execute(resColas.select().where(resColas.c.idRestaurant == idRestaurant)).fetchone()
            if result is not None:
                raise HTTPException(status_code=412, detail="Restaurant Already have an queue")
         
            result = c.execute(colas.insert().values(cola))
            c.execute(resColas.insert().values({'idRestaurant': idRestaurant, 'idCola' : cola['id'] }))
            
            c.commit() 
            result = c.execute(colas.select().where(colas.c.id == cola['id'])).fetchone()
            return result
            
def getColaById(id):
    with engine.connect() as c:
        result =  c.execute(colas.select().where(colas.c.id==id)).one()
        return Cola(**result._mapping)
    
@app.post("/cola/{colaId}/user/{userId}")
def addTurno(colaId, userId):
    
    user = getUserById(userId)
    cola = getColaById(colaId)
    if getTurn(user[0], cola.id) is not None:
        raise HTTPException(status_code=401, detail="Turn already asigned for a user")
    
    with engine.connect() as c:
    
        turno = {
        'idCliente' : userId,
        'idCola': colaId,
        'horaInicio': datetime.now(),
        'fecha': datetime.now(),
        'status': 'PENDIENTE'
        }
        c.execute(turnos.insert().values(turno))
        result = c.execute(turnos.select().where(turnos.c.idCola == str(colaId), turnos.c.idCliente == str(userId)))
        c.commit()
        return result

@app.put("/cola/{colaId}/user/{userId}")
def finishTurn(colaId, userId, body= None):
    
    user = getUserById(userId)
    cola = getColaById(colaId)
    if getTurn(user[0], cola.id) is  None:
        raise HTTPException(status_code=401, detail="Turn not asigned to a user")
    
    with engine.connect() as c:
        turno = getTurn(user[0], cola.id) 
        horaFin = datetime.now()
        if body is None:

            turno = {
            'horaFin': horaFin,
            'status': 'FINALIZADA',
            'tiempoDuracion':int((horaFin - turno[3]).total_seconds() / 60)
            }
        else:
            turno = {
            'horaFin': horaFin,
            'status': 'CANCELADA',
            
            }
        cola = c.execute(colas.select().where(colas.c.id == colaId)).one()
        c.execute(colas.update().where(colas.c.id == colaId).values({'turnoActual':cola[-2] +1}))
        result = c.execute(turnos.update().where(turnos.c.idCola == str(colaId), turnos.c.idCliente == str(userId)).values(turno))
        c.commit()
        return result
    

@app.get('/turns/{idCola}/{idUser}', response_model=Turno)
def getTurn(idUser, idCola):
    with engine.connect() as c:
        result = c.execute(turnos.select().where((turnos.c.idCliente== idUser )&( idCola == turnos.c.idCola))).first()
        return result
def getUserById(id: str):
    
    with engine.connect() as c:
        stmt = users.select().where(users.c.id == id)
        
        result = c.execute(stmt).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="User by ID not found")
        
        return result

@app.patch("/users/{id}")
def update_user(id: str, user: dict):
    if len(user) == 0 :
        raise HTTPException(status_code=400)
    with engine.connect() as c:
        try:
            existing_user = getUserById(id)
            update_data = user
            if not update_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

            c.execute(users.update().where(users.c.id == id).values(**update_data))
            c.commit()
            
            return {"msg": "el usuario ha sido actualizado"}
        
        except HTTPException as e:
            raise e
import uuid
@app.post("/users/auth")
def auth(body: dict):

    if body.get('email') is None or body.get('password') is None:
        raise HTTPException(status_code=400)

    with engine.connect() as c:
        result = c.execute(users.select().where(users.c.email == body['email'])).fetchone()
        if result is None:
            raise HTTPException(status_code=404, detail="User invalid credentials")
        if result[-4] != sha256((body['password'] + result[-3]).encode("utf-8")).hexdigest():
            raise HTTPException(status_code=404, detail="User invalid password ")
        token = {'token': uuid.uuid4(), 'expireAt' :datetime.now()+ timedelta(minutes=30)}
        
        c.execute(users.update().where(users.c.email == body['email']).values(**token))
        c.commit()

        return {"id":result[0], "token": token['token'],'expireAt' : token['expireAt']}


# def verify_token(authorization: Optional[str] = Header(None)):
#     if authorization is None or not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=403, detail="Token is not in the header.")
#     token = authorization.split(" ")[1]
#     if token.strip() == "":
#         raise HTTPException(status_code=403, detail="Token is not in the header.")
#     with engine.connect() as conn:
#         result = conn.execute(users.select().where(users.c.token == token)).fetchone()
#         if result is None:
#             raise HTTPException(status_code=401, detail="Token is not valid.")
#         return result

@app.get("/users/me", response_model=User)
def read_users_me(body:dict):
    if 'token' not in body:
        raise HTTPException(status_code=412 , detail='Missing Token')
    with engine.connect() as c:
        result = c.execute(users.select().where(users.c.token == body['token'])).fetchone()
        if result is None: 
             raise HTTPException(status_code=400, detail='Token is not valid')
        return result
@app.post("/users/reset")
def reset():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return {"msg":"Database reset/created"}
    


@app.get("/")
def root():
    with engine.connect() as c:
        postgresql_version = c.execute(text("SELECT version()")).fetchone()[0]
        return ["Hello world", {"postgres_version": postgresql_version}]


@app.get("/places/shortest-time-lasthour")
def getShortestHour():
    results = {}
    with engine.connect() as c:
        response_dict = {

        }
        result = c.execute(turnos.select().where(turnos.c.status == 'FINALIZADA')).all()
        for res in result:

            response_dict [res[2]]  = response_dict.get(res[2], {'cont':0, 'contLastHour':0, 'waitingTimeSum':0, 'waitingTimeSumLastHour':0,  '6am-12pm':0  , '12pm-4pm':0  , '4pm-7pm':0  , '7pm-12am': 0 }) 
            if res[4]> datetime.now() - timedelta(minutes=60):
                response_dict [res[2]]['contLastHour']  = response_dict [res[2]]['contLastHour'] +1
                response_dict [res[2]]['waitingTimeSumLastHour']  = response_dict [res[2]]['waitingTimeSumLastHour'] + res[-3]
            response_dict [res[2]]['cont']  = response_dict [res[2]]['cont'] +1
            response_dict [res[2]]['waitingTimeSum']  = response_dict [res[2]]['waitingTimeSum'] + res[-3]
            if response_dict [res[2]]['contLastHour'] <=0:
                response_dict [res[2]]['contLastHour'] = 1
            
                response_dict [res[2]]['waitingTimeSumLastHour'] = 5
            if response_dict [res[2]]['cont'] <=0:
                response_dict [res[2]]['cont'] = 1
                response_dict [res[2]]['waitingTimeSum'] = 5
            fecha = res[4]
            morning = datetime.strptime("6:00", "%H:%M").time()
            midday = datetime.strptime("12:00", "%H:%M").time()
            afternoon = datetime.strptime("16:00", "%H:%M").time()
            evening = datetime.strptime("19:00", "%H:%M").time()
            if morning <= fecha.time() <= midday:
               response_dict [res[2]]['6am-12pm']=response_dict [res[2]]['6am-12pm'] +1
            elif midday < fecha.time() <= afternoon:
                response_dict [res[2]]['12pm-4pm'] =response_dict [res[2]]['12pm-4pm'] +1
            elif afternoon < fecha.time() <= evening:
                response_dict [res[2]]['4pm-7pm']= response_dict [res[2]]['4pm-7pm'] +1
            elif evening < fecha.time() :
                response_dict [res[2]]['7pm-12am']=response_dict [res[2]]['7pm-12am'] +1
            time_ranges = {key: response_dict[res[2]][key] for key in ['6am-12pm', '12pm-4pm', '4pm-7pm', '7pm-12am']}

            # Obtener la clave con el valor máximo en el subconjunto
            maximun = min(time_ranges, key=time_ranges.get)
                        
            values = getRestByCola(res[2])
            sede_data = {
    'id': str(values[0]),         
    'idFranquicia': str(values[1]), 
    'nombre': str(values[2]),      
    'direccion': str(values[4]),   
    'telefono': str(values[3]), 
    'latitud': str(values[5]),      
    'longitud': str(values[6]),     
    'urlImg': str(values[7]),   
    'averageWaitingTime': str(response_dict[res[2]]['waitingTimeSum'] / response_dict[res[2]]['cont']),
    'averageWaitingTimeLastHour': str(response_dict[res[2]]['waitingTimeSumLastHour'] / response_dict[res[2]]['contLastHour']),
    'cont': str(response_dict[res[2]]['cont']),
    'contLastHour': str(response_dict[res[2]]['contLastHour']),
    'betterTime': maximun
}

            results[values[0]]= sede_data

        return  list(results.values())
    
def getRestByCola(colaId):
    colaId
    with engine.connect() as c:
        
        cola  = c.execute(resColas.select().where(resColas.c.idCola == colaId)).first()
        if cola is None:
            raise HTTPException(status_code=404, detail= str(colaId))
        return c.execute(sedes.select().where(sedes.c.id == cola[1])).fetchone()
@app.get('/restcola', response_model=List[resCola])
def getRestColas():
    with engine.connect() as c:
        cola  = c.execute(resColas.select()).all()
        
        return cola
    


@app.get("/places/common-by-user/{idCliente}")
def getCommon(idCliente):
    results = {}
    with engine.connect() as c:
        response_dict = {

        }
        result = c.execute(turnos.select().where(turnos.c.status == 'FINALIZADA', turnos.c.idCliente == idCliente )).all()
        for res in result:

            response_dict [res[2]]  = response_dict.get(res[2], {'cont':0, 'contLastHour':0, 'waitingTimeSum':0, 'waitingTimeSumLastHour':0,  '6am-12pm':0  , '12pm-4pm':0  , '4pm-7pm':0  , '7pm-12am': 0 }) 
            if res[4]> datetime.now() - timedelta(minutes=60):
                response_dict [res[2]]['contLastHour']  = response_dict [res[2]]['contLastHour'] +1
                response_dict [res[2]]['waitingTimeSumLastHour']  = response_dict [res[2]]['waitingTimeSumLastHour'] + res[-3]
            response_dict [res[2]]['cont']  = response_dict [res[2]]['cont'] +1
            response_dict [res[2]]['waitingTimeSum']  = response_dict [res[2]]['waitingTimeSum'] + res[-3]
            if response_dict [res[2]]['contLastHour'] <=0:
                response_dict [res[2]]['contLastHour'] = 1
            
                response_dict [res[2]]['waitingTimeSumLastHour'] = 5
            if response_dict [res[2]]['cont'] <=0:
                response_dict [res[2]]['cont'] = 1
                response_dict [res[2]]['waitingTimeSum'] = 5
            fecha = res[4]
            morning = datetime.strptime("6:00", "%H:%M").time()
            midday = datetime.strptime("12:00", "%H:%M").time()
            afternoon = datetime.strptime("16:00", "%H:%M").time()
            evening = datetime.strptime("19:00", "%H:%M").time()
            if morning <= fecha.time() <= midday:
               response_dict [res[2]]['6am-12pm']=response_dict [res[2]]['6am-12pm'] +1
            elif midday < fecha.time() <= afternoon:
                response_dict [res[2]]['12pm-4pm'] =response_dict [res[2]]['12pm-4pm'] +1
            elif afternoon < fecha.time() <= evening:
                response_dict [res[2]]['4pm-7pm']= response_dict [res[2]]['4pm-7pm'] +1
            elif evening < fecha.time() :
                response_dict [res[2]]['7pm-12am']=response_dict [res[2]]['7pm-12am'] +1
            time_ranges = {key: response_dict[res[2]][key] for key in ['6am-12pm', '12pm-4pm', '4pm-7pm', '7pm-12am']}

            maximun = min(time_ranges, key=time_ranges.get)
                        
            values = getRestByCola(res[2])
            sede_data = {
    'id': str(values[0]),         
    'idFranquicia': str(values[1]), 
    'nombre': str(values[2]),      
    'direccion': str(values[4]),   
    'telefono': str(values[3]), 
    'latitud': str(values[5]),      
    'longitud': str(values[6]),     
    'urlImg': str(values[7]),   
    'averageWaitingTime': str(response_dict[res[2]]['waitingTimeSum'] / response_dict[res[2]]['cont']),
    'averageWaitingTimeLastHour': str(response_dict[res[2]]['waitingTimeSumLastHour'] / response_dict[res[2]]['contLastHour']),
    'cont': str(response_dict[res[2]]['cont']),
    'contLastHour': str(response_dict[res[2]]['contLastHour']),
    'betterTime': maximun  
}

            results[values[0]]= sede_data

        return  list(results.values())