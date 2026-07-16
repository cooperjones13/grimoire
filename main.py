from pydantic import BaseModel

class HealthCheck(BaseModel):
    status: str


from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "welcome to grimoire"}


@app.get("/health")
def health_check():
    return HealthCheck(status="ok")
