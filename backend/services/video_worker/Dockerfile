# ใช้ Python เวอร์ชั่น 3.11 แบบ slim เป็น Image พื้นฐาน
FROM python:3.11-slim

# --- นี่คือส่วนที่สำคัญที่สุดสำหรับ Worker ---
# อัปเดตรายการ package และติดตั้งโปรแกรม ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# กำหนด Working Directory ภายใน Container
WORKDIR /app

# คัดลอกไฟล์ requirements.txt ของ Worker เข้าไป
COPY requirements.txt .

# ติดตั้ง Python libraries ที่ Worker ต้องการ
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมดของ Worker เข้าไป
COPY . .

# คำสั่งที่จะรันเมื่อคอนเทนเนอร์เริ่มทำงาน
CMD ["python", "main.py"]