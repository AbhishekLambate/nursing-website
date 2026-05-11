from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Response
from pydantic import BaseModel, EmailStr
from typing import Optional
import re
import io
import pandas as pd
from datetime import datetime
from database import get_db
from routes.admin import get_current_admin
from utils.mailer import send_admin_notification, send_user_confirmation
import sqlite3

router = APIRouter()

class RegistrationCreate(BaseModel):
    offer_id: Optional[int] = None
    name: str
    institute: str
    mobile: str
    email: EmailStr
    reg_number: Optional[str] = None

class StatusUpdate(BaseModel):
    payment_status: str
    notes: Optional[str] = None

@router.post("")
def create_registration(reg: RegistrationCreate, background_tasks: BackgroundTasks, db: sqlite3.Connection = Depends(get_db)):
    if not reg.name or not reg.institute or not reg.mobile or not reg.email:
        raise HTTPException(status_code=400, detail="All fields are required")
        
    cleaned_mobile = "".join(filter(str.isdigit, reg.mobile))
    if len(cleaned_mobile) != 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number (10 digits required)")

    cursor = db.cursor()
    amount = 0.0
    offerTitle = "General Registration"
    
    if reg.offer_id:
        offer = cursor.execute('SELECT * FROM offers WHERE id = ?', (reg.offer_id,)).fetchone()
        if offer:
            amount = offer['amount']
            offerTitle = offer['title']

    cursor.execute('''
        INSERT INTO registrations (offer_id, name, institute, mobile, email, reg_number, amount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (reg.offer_id, reg.name, reg.institute, reg.mobile, reg.email, reg.reg_number, amount))
    db.commit()
    
    reg_id = cursor.lastrowid
    
    def send_emails(name, inst, mob, em, reg_num, title, amt, r_id):
        admin_sent = send_admin_notification(name, inst, mob, em, reg_num, title, amt)
        send_user_confirmation(name, em, title, r_id)
        if admin_sent:
            with sqlite3.connect('data/nursingcne.db', check_same_thread=False) as conn:
                conn.execute('UPDATE registrations SET email_sent=1 WHERE id=?', (r_id,))
                conn.commit()

    background_tasks.add_task(send_emails, reg.name, reg.institute, reg.mobile, reg.email, reg.reg_number, offerTitle, amount, reg_id)

    return {
        "success": True,
        "registration_id": reg_id,
        "amount": amount,
        "message": "Registration successful! You will receive a confirmation email shortly."
    }

@router.get("")
def get_registrations(
        search: Optional[str] = None,
        status: Optional[str] = None,
        offer_id: Optional[int] = None,
        page: int = 1,
        limit: int = 50,
        admin: dict = Depends(get_current_admin),
        db: sqlite3.Connection = Depends(get_db)
    ):
    cursor = db.cursor()
    query = """
    SELECT r.*, o.title as offer_title 
    FROM registrations r 
    LEFT JOIN offers o ON r.offer_id = o.id 
    WHERE 1=1
    """
    params = []

    if search:
        query += " AND (r.name LIKE ? OR r.email LIKE ? OR r.mobile LIKE ? OR r.institute LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
        
    if status:
        query += " AND r.payment_status = ?"
        params.append(status)
        
    if offer_id:
        query += " AND r.offer_id = ?"
        params.append(offer_id)

    query += " ORDER BY r.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, (page - 1) * limit])

    registrations = cursor.execute(query, params).fetchall()
    
    count_query = "SELECT COUNT(*) as cnt FROM registrations WHERE 1=1"
    # Basic implementation without repeating filters for count
    total = cursor.execute(count_query).fetchone()['cnt']
    
    return {
        "registrations": [dict(row) for row in registrations],
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/export/excel")
def export_excel(
    response: Response,
    status: Optional[str] = None,
    offer_id: Optional[int] = None,
    admin: dict = Depends(get_current_admin),
    db: sqlite3.Connection = Depends(get_db)
):
    query = """
    SELECT r.id as ID, r.name as Name, r.institute as Institute, r.mobile as Mobile, r.email as Email, r.reg_number as 'Reg. Number',
           o.title as Offer, r.amount as 'Amount (₹)', r.payment_status as 'Payment Status', r.transaction_id as 'Transaction ID',
           r.created_at as 'Registered On'
    FROM registrations r 
    LEFT JOIN offers o ON r.offer_id = o.id WHERE 1=1
    """
    params = []
    if status:
        query += " AND r.payment_status = ?"
        params.append(status)
    if offer_id:
        query += " AND r.offer_id = ?"
        params.append(offer_id)
    query += " ORDER BY r.created_at DESC"
    
    df = pd.read_sql_query(query, db, params=params)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Registrations')
        
    output.seek(0)
    response.headers["Content-Disposition"] = f'attachment; filename="NursingCNE_Registrations_{int(datetime.now().timestamp())}.xlsx"'
    response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return Response(content=output.read(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=response.headers)

@router.get("/{id}")
def get_registration(id: int, admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    reg = db.cursor().execute("""
        SELECT r.*, o.title as offer_title 
        FROM registrations r 
        LEFT JOIN offers o ON r.offer_id = o.id 
        WHERE r.id = ?
    """, (id,)).fetchone()
    
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
        
    return {"registration": dict(reg)}

@router.patch("/{id}/status")
def update_status(id: int, data: StatusUpdate, admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    if data.payment_status not in ['pending', 'success', 'failed', 'refunded']:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    db.cursor().execute('UPDATE registrations SET payment_status=?, notes=? WHERE id=?', (data.payment_status, data.notes, id))
    db.commit()
    return {"success": True}

@router.delete("/{id}")
def delete_registration(id: int, admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    db.cursor().execute('DELETE FROM registrations WHERE id = ?', (id,))
    db.commit()
    return {"success": True, "message": "Registration deleted"}
