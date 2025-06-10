# /backend/services/api-server/Dockerfile

# Step 1: ใช้ Python 3.11-slim เป็น Image พื้นฐาน
FROM python:3.11-slim

# Step 2: ตั้งค่า Working Directory ภายใน Container
WORKDIR /app

# Step 3: บอก Python ว่าให้มองหาโมดูลในโฟลเดอร์ /app ด้วย
ENV PYTHONPATH=/app

# Step 4: คัดลอกไฟล์ requirements.txt เข้าไปใน Container ก่อน
# ที่ทำแบบนี้เพราะ Docker จะได้ไม่ต้องติดตั้ง library ใหม่ทุกครั้งที่เราแก้โค้ด (ถ้า library ไม่เปลี่ยน)
COPY requirements.txt requirements.txt

# Step 5: ติดตั้ง Library ทั้งหมดที่โปรเจกต์ต้องการ
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: คัดลอกโค้ดทั้งหมดในโฟลเดอร์ app ของเราเข้าไปใน Container
COPY ./app .

# Step 7: บอก Docker ว่า Container นี้จะเปิด Port 8000 รอรับการเชื่อมต่อ
EXPOSE 8000

# หมายเหตุ: เราไม่ต้องใส่ CMD หรือ ENTRYPOINT ที่นี่เพราะเราได้สั่งให้รันด้วย uvicorn ในไฟล์ docker-compose.yml อยู่แล้ว