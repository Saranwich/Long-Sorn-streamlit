# C:\Users\GitHub\Long-Sorn\backend\services\video_worker\main.py
# การส่งต่องานจาก Video Worker ไปยัง AI Orchestrator สร้างทางเชื่อมระหว่างการประมวลผลวิดีโอเบื้องต้นกับการวิเคราะห์ด้วย AI

import os
import json
import time
import shutil
import subprocess
from dotenv import load_dotenv
import redis
import boto3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- 1. โหลดการตั้งค่าจาก .env ---
print("Loading environment variables...")
load_dotenv()

# R2/S3 Credentials
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

# Redis Credentials
REDIS_URL = os.getenv("REDIS_URL")
JOB_QUEUE_NAME = os.getenv("JOB_QUEUE_NAME", "video_processing_queue")
AI_QUEUE_NAME = "ai-analysis-queue" # คิวใหม่สำหรับส่งต่องานให้ AI

# Database Credentials
DATABASE_URL = os.getenv("DATABASE_URL")

# --- 2. ตั้งค่า Clients สำหรับเชื่อมต่อ Services ---
print("Initializing service clients...")
try:
    # Database Session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # S3 Client (for R2)
    s3_client = boto3.client('s3',
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY
    )

    # Redis Client
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping() # ทดสอบการเชื่อมต่อ
    print("Service clients initialized successfully.")
except Exception as e:
    print(f"!!! Failed to initialize clients: {e}")
    exit(1)


def process_video_job(job_data: dict):
    """
    ฟังก์ชันหลักในการประมวลผลวิดีโอ 1 งาน
    """
    video_id = job_data.get("video_id")
    r2_object_key = job_data.get("r2_object_key") # เปลี่ยนจาก object_key เป็น r2_object_key ตามโค้ดเดิม
    print(f"Processing job for video_id: {video_id}")

    # สร้างโฟลเดอร์ชั่วคราวสำหรับเก็บไฟล์
    temp_dir = f"/tmp/{video_id}"
    os.makedirs(temp_dir, exist_ok=True)
    local_video_path = os.path.join(temp_dir, os.path.basename(r2_object_key))
    local_audio_path = os.path.join(temp_dir, "audio.m4a")
    audio_object_key = f"audio/{video_id}.m4a" # แนะนำให้เก็บไฟล์เสียงใน folder แยก

    db = SessionLocal()
    try:
        # --- 3. ดาวน์โหลดวิดีโอจาก R2 ---
        print(f"Downloading {r2_object_key} from R2...")
        s3_client.download_file(R2_BUCKET_NAME, r2_object_key, local_video_path)
        print("Download complete.")

        # --- 4. ใช้ FFmpeg แยกเสียง ---
        print("Extracting audio with FFmpeg...")
        subprocess.run(
            ["ffmpeg", "-i", local_video_path, "-vn", "-acodec", "copy", local_audio_path],
            check=True, capture_output=True, text=True
        )
        print("Audio extraction complete.")

        # --- 5. อัปโหลดไฟล์เสียงกลับไปที่ R2 ---
        print(f"Uploading audio to R2 at {audio_object_key}...")
        s3_client.upload_file(local_audio_path, R2_BUCKET_NAME, audio_object_key)
        print("Audio upload complete.")

        # --- 6. ส่งต่องานไปให้ AI Orchestrator ---
        print("Enqueuing job for AI analysis...")
        ai_job_data = {
            "video_id": video_id,
            "audio_r2_key": audio_object_key
        }
        
        # ใช้ redis_client ที่มีอยู่แล้วเพื่อส่ง Job ใหม่เข้าไปใน ai-analysis-queue
        redis_client.lpush(AI_QUEUE_NAME, json.dumps(ai_job_data))
        print(f"Successfully enqueued AI job for video_id: {video_id}")
        
        # --- 7. อัปเดตสถานะใน Database ---
        print("Updating database status to PENDING_AI_ANALYSIS...")
        update_query = text("UPDATE videos SET status = 'PENDING_AI_ANALYSIS', audio_r2_key = :audio_key WHERE id = :vid")
        db.execute(update_query, {"audio_key": audio_object_key, "vid": video_id})
        db.commit()
        print("Database updated.")

    except Exception as e:
        print(f"!!! AN ERROR OCCURRED for video_id {video_id}: {e}")
        # หากเกิด Error ให้พยายามอัปเดตสถานะเป็น FAILED
        try:
            error_query = text("UPDATE videos SET status = 'FAILED_PROCESSING' WHERE id = :vid")
            db.execute(error_query, {"vid": video_id})
            db.commit()
        except Exception as db_error:
            print(f"!!! Could not update status to FAILED for video_id {video_id}: {db_error}")
        
    finally:
        # ลบไฟล์และโฟลเดอร์ชั่วคราว
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        db.close()
        print(f"Finished job for video_id: {video_id}\n")


def main_loop():
    """
    ฟังก์ชันหลักที่จะทำงานวนลูปเพื่อรอรับงานจาก Redis
    """
    print(f"Worker started, waiting for jobs on queue '{JOB_QUEUE_NAME}'...")
    while True:
        try:
            # รอและดึงงานจากคิวแบบ Blocking
            # จะคืนค่าเป็น tuple: (ชื่อคิว, ข้อมูลงาน)
            job_tuple = redis_client.brpop(JOB_QUEUE_NAME, timeout=0)

            if job_tuple:
                # ข้อมูลงานจะอยู่ในลำดับที่ 1 และเป็น bytes, ต้อง decode ก่อน
                job_data_str = job_tuple[1].decode('utf-8')
                print(f"\n--- New Job Received ---")
                
                # แปลง JSON string เป็น Python dict
                job_data = json.loads(job_data_str)
                
                # เรียกใช้ฟังก์ชันประมวลผลวิดีโอ
                process_video_job(job_data)

        except Exception as e:
            # กรณีเกิด Error ที่ไม่คาดคิดใน Loop หลัก ให้พิมพ์ Error แล้วรอสักครู่ก่อนเริ่มใหม่
            print(f"!!! A critical error occurred in the main loop: {e}")
            time.sleep(5) 

if __name__ == "__main__":
    main_loop()  