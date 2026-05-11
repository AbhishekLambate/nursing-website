import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routes import admin, offers, payment, registrations, settings
from database import init_db

# Ensure db initialized
init_db()

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="NursingCNE")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs('uploads', exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(offers.router, prefix="/api/offers", tags=["offers"])
app.include_router(registrations.router, prefix="/api/registrations", tags=["registrations"])
app.include_router(payment.router, prefix="/api/payment", tags=["payment"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])

@app.get("/api/health")
def health_check():
    import datetime
    return {"status": "ok", "time": datetime.datetime.utcnow().isoformat() + "Z", "site": "NursingCNE"}

# Serving Frontend React/Static build on Catch-All or exact matches
@app.get("/")
def serve_index():
    return FileResponse("public/index.html")

@app.get("/admin")
def serve_admin():
    return FileResponse("public/admin/index.html")

@app.get("/payment-success")
def serve_payment_success():
    return FileResponse("public/payment-success.html")

@app.get("/payment-failed")
def serve_payment_failed():
    return FileResponse("public/payment-failed.html")

app.mount("/", StaticFiles(directory="public", html=True), name="public")

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"error": "API endpoint not found"})
    # for frontend router
    return FileResponse("public/index.html")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print('❌ Server Error:', exc)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc) or "Internal server error"}
    )
