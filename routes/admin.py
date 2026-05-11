from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from database import get_db
import sqlite3
import os

router = APIRouter()
security = HTTPBearer(auto_error=False)

JWT_SECRET = os.environ.get('JWT_SECRET', 'nursingcne_secret')

class LoginRequest(BaseModel):
    username: str
    password: str

class PasswordChangeRequest(BaseModel):
    currentPassword: str
    newPassword: str

def get_current_admin(request: Request, adminToken: str = Cookie(None)):
    token = adminToken
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/login")
def login(login_data: LoginRequest, response: Response, db: sqlite3.Connection = Depends(get_db)):
    if not login_data.username or not login_data.password:
        raise HTTPException(status_code=400, detail="Username and password required")

    cursor = db.cursor()
    admin = cursor.execute('SELECT * FROM admins WHERE username = ?', (login_data.username,)).fetchone()
    
    if not admin or not bcrypt.checkpw(login_data.password.encode(), admin['password'].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    exp = datetime.now(timezone.utc) + timedelta(hours=24)
    token = jwt.encode({"id": admin['id'], "username": admin['username'], "exp": exp}, JWT_SECRET, algorithm="HS256")

    response.set_cookie(
        key="adminToken",
        value=token,
        httponly=True,
        max_age=24 * 60 * 60,
        samesite="strict"
    )

    return {"success": True, "token": token, "username": admin['username']}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("adminToken")
    return {"success": True}

@router.get("/verify")
def verify(admin: dict = Depends(get_current_admin)):
    return {"valid": True, "username": admin['username']}

@router.get("/dashboard")
def dashboard(admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    totalOffers = cursor.execute('SELECT COUNT(*) as cnt FROM offers').fetchone()['cnt']
    activeOffers = cursor.execute('SELECT COUNT(*) as cnt FROM offers WHERE is_active=1').fetchone()['cnt']
    totalRegs = cursor.execute('SELECT COUNT(*) as cnt FROM registrations').fetchone()['cnt']
    paidRegs = cursor.execute("SELECT COUNT(*) as cnt FROM registrations WHERE payment_status='success'").fetchone()['cnt']
    
    tot_rev_row = cursor.execute("SELECT COALESCE(SUM(amount),0) as total FROM registrations WHERE payment_status='success'").fetchone()
    totalRevenue = tot_rev_row['total'] if tot_rev_row else 0
    
    recentRegs_cursor = cursor.execute("""
        SELECT r.*, o.title as offer_title 
        FROM registrations r 
        LEFT JOIN offers o ON r.offer_id = o.id 
        ORDER BY r.created_at DESC LIMIT 5
    """)
    recentRegs = [dict(row) for row in recentRegs_cursor.fetchall()]

    return {
        "totalOffers": totalOffers,
        "activeOffers": activeOffers,
        "totalRegs": totalRegs,
        "paidRegs": paidRegs,
        "totalRevenue": totalRevenue,
        "recentRegs": recentRegs
    }

@router.put("/change-password")
def change_password(req: PasswordChangeRequest, admin_payload: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    admin = cursor.execute('SELECT * FROM admins WHERE id = ?', (admin_payload['id'],)).fetchone()
    
    if not bcrypt.checkpw(req.currentPassword.encode(), admin['password'].encode()):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
        
    hashed = bcrypt.hashpw(req.newPassword.encode(), bcrypt.gensalt()).decode()
    cursor.execute('UPDATE admins SET password = ? WHERE id = ?', (hashed, admin_payload['id']))
    db.commit()
    
    return {"success": True, "message": "Password updated successfully"}
