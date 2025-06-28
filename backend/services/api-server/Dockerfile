# ใช้ Python เวอร์ชั่น 3.11 แบบ slim เป็น Image พื้นฐาน
FROM python:3.11-slim

# กำหนด Working Directory ภายใน Container
WORKDIR /app

# (สำคัญ) ตั้งค่า PYTHONPATH ภายใน Image โดยตรง
ENV PYTHONPATH=/app

# คัดลอกเฉพาะไฟล์ requirements.txt เข้ามาก่อนเพื่อใช้ Docker cache
# ระบุ path ที่ถูกต้องไปยังไฟล์จาก Build Context (./backend)
COPY ./services/api-server/requirements.txt /app/requirements.txt

# ติดตั้ง library ทั้งหมด
RUN pip install --no-cache-dir -r /app/requirements.txt

# คัดลอกโค้ดทั้งหมดของ api-server เข้าไปใน /app
# คำสั่งนี้จะคัดลอกโฟลเดอร์ src ทั้งหมด (ที่มี shared อยู่ข้างใน) เข้าไปด้วย
COPY ./services/api-server/src /app/src

# EXPOSE Port เพื่อประกาศให้ทราบ
EXPOSE 8000