# /backend/shared/db/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env เข้ามาใน Environment Variables ของโปรแกรม
load_dotenv()

# 1. อ่านค่า DATABASE_URL จาก Environment Variable
# โดยมีค่า Default เผื่อไว้ในกรณีที่ไม่ได้ตั้งค่าใน .env
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:passw0rd@postgreshost/db")

# 2. สร้าง Engine ของ SQLAlchemy ซึ่งเป็น "หัวใจ" ของการเชื่อมต่อ
# engine จะทำหน้าที่จัดการการเชื่อมต่อกับฐานข้อมูล PostgreSQL
engine = create_engine(DATABASE_URL)

# 3. สร้าง Session_Local ซึ่งเป็น "โรงงาน" ที่ใช้สร้าง session การเชื่อมต่อ
# เมื่อเราต้องการคุยกับ Database เราจะขอ session จากโรงงานนี้
Session_Local = sessionmaker(autocommit = False, autoflush = False, bind = engine)

# 4. สร้าง Base ซึ่งเป็นคลาสพื้นฐานสำหรับ Model ของตารางทั้งหมด
# ทุกครั้งที่เราสร้าง Model เช่น User, Video จะต้องสืบทอดจากคลาส Base นี้
Base = declarative_base()

# --- ฟังก์ชันสำหรับ Dependency Injection ใน FastAPI ---
def get_db_session():
    """
    ฟังก์ชันนี้จะถูกเรียกใช้ในทุกๆ API Endpoint ที่ต้องการคุยกับ Database
    มันจะทำการเปิด session, ให้ API นำไปใช้งาน, และปิด session อัตโนมัติเมื่อ API ทำงานเสร็จ
    """
    db = Session_Local()
    try:
        yield db
    finally:
        db.close()