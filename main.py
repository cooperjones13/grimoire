from pydantic import BaseModel
from fastapi import FastAPI
from dotenv import load_dotenv
import psycopg
import os

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

class HealthCheck(BaseModel):
    status: str

app = FastAPI()

@app.get("/")
def root():
    return {"message": "welcome to grimoire"}


@app.get("/health")
def health_check():
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            conn.execute("SELECT 1").fetchone()
        return HealthCheck(status="ok")
    except psycopg.OperationalError:
        return HealthCheck(status="error")
