from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from database import get_db
from routes.admin import get_current_admin
import sqlite3

router = APIRouter()

class SettingsUpdate(BaseModel):
    settings: Dict[str, Any]

@router.get("")
def get_settings(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    rows = cursor.execute('SELECT key, value FROM site_settings').fetchall()
    settings = {row['key']: row['value'] for row in rows}
    return {"settings": settings}

@router.put("")
def update_settings(data: SettingsUpdate, admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    if not isinstance(data.settings, dict):
        raise HTTPException(status_code=400, detail="Invalid settings data")

    cursor = db.cursor()
    for key, val in data.settings.items():
        cursor.execute('''
            INSERT INTO site_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
        ''', (key, str(val)))
        
    db.commit()
    return {"success": True, "message": "Settings updated"}
