from fastapi import FastAPI, HTTPException, status, Depends, Header
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from hashlib import sha256
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import requests
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


 


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/ping")
def healthCheck():
    return "pong"


@app.get("/update_db")
def updateDB():
    turns = requests.get('http://web_server:8000/turnos').json()
   
    queres = requests.get('http://web_server:8000/restcola').json()
    places = requests.get('http://web_server:8000/restaurants').json()

    queues = requests.get('http://web_server:8000/colas').json()
    mapper = queres_mapper(queres, places,queues)

    
    proccess_t = proccess_turn(turns, mapper)
    proccess_p =process_restaurants(places, turns, mapper)
    save_json(proccess_t, "user_behavior")
    save_json(proccess_t, "place_efficience")
    return {'msg' : "SE HAN GENERADO DATOS DE ANALITICA"}
    

def proccess_turn(turns, mapper):
    dicti = []
    for i in turns:
        data = {
            'client' : i['idCliente'],
            'restaurant' :  mapper[i['idCola']]['nombre'],
            'latitud' :  mapper[i['idCola']]['latitud'],
            'longitud' :  mapper[i['idCola']]['longitud'],
            'duration' :  i['tiempoDuracion']

        }
        dicti.append(data)
        

    return dicti

def queres_mapper(queres, places, colas):
    result = {}
    for i in queres:
        for rest in places:
            cola = None
            for col in colas:
                if i['idCola'] == col['id']:
                    cola = col
            if i['idRestaurant'] == rest['id']:
                rest['totalQueue'] = cola['turnoActual']
                result[i['idCola']] = rest
                

    return result
def process_restaurants(places, turns, mapper):
    result = []
    for place in places:
        cont = 0
        temp = {}
        
        for turn in turns:
            if mapper[turn['idCola']]['id'] == place['id']:
                cont += 1
                temp[turn['idCliente']] = temp.get(turn['idCliente'], 0) + 1
        
        if temp:
            most_common_customer = max(temp, key=temp.get)
        else:
            most_common_customer = None
        
        data = {
            'id': place['id'],
            'nombre': place['nombre'],
            'totalCont': cont,
            'MostCommonCustomer': most_common_customer  
        }
        
        result.append(data)

    return result

        

import os
import json

def save_json(data, filename):
    directory = './jsons/'
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, f"{filename}.json")
    
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)  

@app.get('/users_insights')
def get_behavior():
    file_path = './jsons/user_behavior.json'
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type='application/json', filename="user_behavior.json")
@app.get('/place_insights')
def get_behavior():
    file_path = './jsons/place_efficience.json'
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type='application/json', filename="user_behavior.json")