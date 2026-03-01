from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="ZERDE Backend")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
def root():
    return {"status": "Backend is running 🚀"}

@app.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest):
    return {
        "response": f"Сен жаздың: {data.message}"
    }
