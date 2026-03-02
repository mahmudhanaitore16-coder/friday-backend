from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import psycopg2
import uuid

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(DATABASE_URL)


# =====================
# MODELS
# =====================

class RegisterRequest(BaseModel):
    username: str

class ChatRequest(BaseModel):
    token: str
    message: str

class AssistantNameRequest(BaseModel):
    token: str
    assistant_name: str


# =====================
# REGISTER
# =====================

@app.post("/register")
def register(data: RegisterRequest):
    token = str(uuid.uuid4())

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, token) VALUES (%s, %s) RETURNING id",
            (data.username, token)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

    cur.close()
    conn.close()

    return {
        "message": "User created",
        "token": token
    }


# =====================
# CHAT (TOKEN BASED)
# =====================

@app.post("/chat")
def chat(data: ChatRequest):
    conn = get_connection()
    cur = conn.cursor()

    # token арқылы user табу
    cur.execute("SELECT id, assistant_name FROM users WHERE token = %s", (data.token,))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = user[0]
    assistant_name = user[1]

    user_text = data.message
    bot_reply = f"{assistant_name}: Сен жаздың → {user_text}"

    # user_id арқылы сақтау
    cur.execute(
        "INSERT INTO messages (user_id, user_message, bot_response) VALUES (%s, %s, %s)",
        (user_id, user_text, bot_reply)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"response": bot_reply}


# =====================
# GET ONLY MY MESSAGES
# =====================

@app.get("/messages")
def get_messages(token: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE token = %s", (token,))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = user[0]

    cur.execute(
        "SELECT user_message, bot_response, created_at FROM messages WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "user_message": r[0],
            "bot_response": r[1],
            "created_at": str(r[2])
        })

    return {"items": result}


# =====================
# MY PROFILE
# =====================

@app.get("/me")
def me(token: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT username, assistant_name, created_at FROM users WHERE token = %s",
        (token,)
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "username": user[0],
        "assistant_name": user[1],
        "created_at": str(user[2])
    }


# =====================
# CHANGE ASSISTANT NAME
# =====================

@app.post("/assistant-name")
def change_assistant_name(data: AssistantNameRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE token = %s", (data.token,))
    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid token")

    cur.execute(
        "UPDATE users SET assistant_name = %s WHERE token = %s",
        (data.assistant_name, data.token)
    )

    conn.commit()
    cur.close()
    conn.close()
    return{"message": "Assistant name updated"}
