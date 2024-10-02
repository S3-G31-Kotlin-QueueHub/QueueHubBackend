FROM python:latest

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./ /app
WORKDIR /app/user-service

ENV DB_USER postgres

ENV DB_PASSWORD password

ENV DB_HOST postgres

ENV DB_PORT 5432

ENV DB_NAME queue_db

ENV USERS_PATH http://localhost:8000

ENV write_result=not_show

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]