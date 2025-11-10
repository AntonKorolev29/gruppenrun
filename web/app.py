from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3

app = FastAPI(title="Gruppen Run Bot API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

WEB_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(WEB_DIR, "templates")
STATIC_DIR = os.path.join(WEB_DIR, "static")
DB_PATH = "/root/gruppenrun_bot/bot_data.db"

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))

@app.get("/api/status")
async def status():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Всего пользователей
        cursor.execute("SELECT COUNT(*) as count FROM users")
        users = cursor.fetchone()['count']
        
        # Активных за 7 дней
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as count 
            FROM event_tracking 
            WHERE created_at >= datetime('now', '-7 days')
        """)
        active = cursor.fetchone()['count']
        
        # Всего регистраций
        cursor.execute("""
            SELECT COUNT(*) as count FROM (
                SELECT user_id FROM gruppenrun_registrations
                UNION ALL
                SELECT user_id FROM iremel_registrations
                UNION ALL
                SELECT user_id FROM krugosvetka_registrations
            )
        """)
        regs = cursor.fetchone()['count']
        
        conn.close()
        return {
            "is_running": True,
            "users_count": users,
            "active_users": active,
            "registrations": regs
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"is_running": True, "users_count": 0, "active_users": 0, "registrations": 0}

@app.get("/api/stats")
async def stats():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM gruppenrun_registrations")
        grupp = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM iremel_registrations WHERE is_registered = 1")
        iremel = cursor.fetchone()['count']
        
        conn.close()
        return {
            "gruppenrun_registrations": grupp,
            "iremel_registrations": iremel
        }
    except:
        return {"gruppenrun_registrations": 0, "iremel_registrations": 0}

@app.get("/api/users")
async def users():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name, username 
            FROM users 
            ORDER BY created_at DESC 
            LIMIT 50
        """)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {"user_id": r['user_id'], "first_name": r['name'] or "—", "username": r['username'] or "unknown"}
            for r in rows
        ]
    except:
        return []
