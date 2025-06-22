# ใช้ Python เวอร์ชั่น 3.11 แบบ slim เป็น Image พื้นฐาน
FROM python:3.11-slim

# กำหนด Working Directory ภายใน Container
WORKDIR /app

# Copy ไฟล์ที่ระบุรายการ Library ที่ต้องใช้เข้าไปก่อน
# การ Copy แค่ไฟล์นี้ก่อนจะช่วยให้ Docker-cache ทำงานได้ดีขึ้นในอนาคต
COPY ./services/api-server/requirements.txt .

# รันคำสั่ง pip install เพื่อติดตั้ง Library ทั้งหมด
RUN pip install --no-cache-dir -r requirements.txt

# Copy โค้ดของแอปพลิเคชันทั้งหมด (ที่อยู่ในโฟลเดอร์ src) เข้าไปใน Container
COPY ./services/api-server/ /app
COPY ./shared/ /app/src/shared/

# EXPOSE 8000 เป็นการประกาศให้ทราบว่า Container นี้จะทำงานที่ Port 8000
EXPOSE 8000