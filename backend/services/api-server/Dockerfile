# Stage 1: Build the application
FROM python:3.11-slim as builder

# กำหนด Working Directory
WORKDIR /app

# (สำคัญ) ตั้งค่า PYTHONPATH ภายใน Image โดยตรง
# เพื่อให้ Python หาโมดูลใน /app เจอเสมอ
ENV PYTHONPATH=/app

# คัดลอกเฉพาะไฟล์ requirements.txt เข้ามาก่อนเพื่อใช้ Docker cache
COPY ./services/api-server/requirements.txt /app/requirements.txt

# ติดตั้ง dependencies ทั้งหมด
RUN pip install --no-cache-dir -r /app/requirements.txt

# คัดลอกโค้ดของ api-server (เฉพาะโฟลเดอร์ src) เข้าไป
COPY ./services/api-server/src /app/src

# คัดลอกโค้ดของ shared เข้าไปใน src/shared
COPY ./shared /app/src/shared


# Stage 2: Final image (ถ้าต้องการ image ที่เล็กลง)
# ในตอนนี้เราใช้แค่ Stage เดียวเพื่อความง่ายในการดีบัก

# EXPOSE Port
EXPOSE 8000