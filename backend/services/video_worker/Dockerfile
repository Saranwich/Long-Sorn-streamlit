# ใช้ Python เวอร์ชั่น 3.11 แบบ slim เป็น Image พื้นฐาน
FROM python:3.11-slim

# --- บรรทัดสำคัญ: ติดตั้ง FFmpeg ---
# อัปเดตรายการ package และติดตั้ง ffmpeg โดยไม่ถามคำถาม (-y)
RUN apt-get update && apt-get install -y ffmpeg

# กำหนด Working Directory ภายใน Container
WORKDIR /app

# --- ส่วนที่แก้ไข: ระบุ Path ไปยัง requirements.txt ให้ถูกต้อง ---
# Path นี้จะอ้างอิงจาก build context ที่กำหนดใน docker-compose.yml (./backend)
COPY ./services/video_worker/requirements.txt .

# ติดตั้ง Python libraries ที่ Worker ต้องการ
RUN pip install --no-cache-dir -r requirements.txt

# --- ส่วนที่แก้ไข: คัดลอกโค้ดทั้งหมดของ Worker เข้าไป ---
# ระบุ Path ไปยังโฟลเดอร์ของ Worker ให้ถูกต้อง
COPY ./services/video_worker/ .

# คำสั่งที่จะรันเมื่อคอนเทนเนอร์เริ่มทำงาน
CMD ["python", "main.py"]