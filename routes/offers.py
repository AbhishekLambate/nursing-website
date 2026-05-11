from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_db
from routes.admin import get_current_admin
import sqlite3

router = APIRouter()

class OfferCreate(BaseModel):
    title: str
    amount: float
    description: Optional[str] = None
    original_amount: Optional[float] = None
    badge: Optional[str] = None
    image_url: Optional[str] = None
    valid_till: Optional[str] = None
    seats_total: Optional[int] = 0
    is_active: Optional[bool] = True

class OfferUpdate(OfferCreate):
    pass

@router.get("")
def get_active_offers(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    offers = cursor.execute('SELECT * FROM offers WHERE is_active=1 ORDER BY created_at DESC').fetchall()
    return {"offers": [dict(row) for row in offers]}

@router.get("/all")
def get_all_offers(admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    offers = cursor.execute('SELECT * FROM offers ORDER BY created_at DESC').fetchall()
    return {"offers": [dict(row) for row in offers]}

@router.get("/{id}")
def get_offer(id: int, db: sqlite3.Connection = Depends(get_db)):
    offer = db.cursor().execute('SELECT * FROM offers WHERE id = ?', (id,)).fetchone()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return {"offer": dict(offer)}

@router.post("")
def create_offer(offer: OfferCreate, admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO offers (title, description, amount, original_amount, badge, image_url, valid_till, seats_total, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        offer.title, offer.description, offer.amount, offer.original_amount, offer.badge,
        offer.image_url, offer.valid_till, offer.seats_total, 1 if offer.is_active else 0
    ))
    db.commit()
    new_offer = cursor.execute('SELECT * FROM offers WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return {"success": True, "offer": dict(new_offer)}

@router.put("/{id}")
def update_offer(id: int, offer: OfferUpdate, admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    existing = cursor.execute('SELECT id FROM offers WHERE id = ?', (id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Offer not found")

    cursor.execute('''
        UPDATE offers SET 
        title=?, description=?, amount=?, original_amount=?, badge=?, image_url=?,
        valid_till=?, seats_total=?, is_active=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    ''', (
        offer.title, offer.description, offer.amount, offer.original_amount, offer.badge,
        offer.image_url, offer.valid_till, offer.seats_total, 1 if offer.is_active else 0, id
    ))
    db.commit()
    updated_offer = cursor.execute('SELECT * FROM offers WHERE id = ?', (id,)).fetchone()
    return {"success": True, "offer": dict(updated_offer)}

@router.patch("/{id}/toggle")
def toggle_offer(id: int, admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    offer = cursor.execute('SELECT id, is_active FROM offers WHERE id = ?', (id,)).fetchone()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
        
    newStatus = 0 if offer['is_active'] else 1
    cursor.execute('UPDATE offers SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (newStatus, id))
    db.commit()
    return {"success": True, "is_active": newStatus}

@router.delete("/{id}")
def delete_offer(id: int, admin: dict = Depends(get_current_admin), db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    existing = cursor.execute('SELECT id FROM offers WHERE id = ?', (id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Offer not found")
        
    cursor.execute('DELETE FROM offers WHERE id = ?', (id,))
    db.commit()
    return {"success": True, "message": "Offer deleted"}
