import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# ตั้งค่า logging เพื่อให้เห็น error ได้ง่ายขึ้น
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# สร้างแอปพลิเคชัน FastAPI
app = FastAPI(
    title="Long Sorn API",
    description="API for the Long Sorn project, providing endpoints for all services.",
    version="1.0.0"
)

# สร้าง Exception Handler เพื่อดักจับ Error ทั้งหมด
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"An unhandled exception occurred: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

# สร้าง Endpoint แรกที่ path "/"
@app.get("/")
def read_root():
    logger.info("Root endpoint was called.")
    return {"message": "Welcome to Long Sorn API! The server is running."}

# เพิ่ม Endpoint สำหรับทดสอบ
@app.get("/health")
def health_check():
    logger.info("Health check endpoint was called.")
    return {"status": "ok"}

logger.info("FastAPI application startup complete.")