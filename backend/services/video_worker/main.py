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

# --- โหลดการตั้งค่าจาก .env ---
print("Loading environment variables...")
load_dotenv()

# R2/S3 Credentials
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

# --- 1. โหลดการตั้งค่าจาก .env ---
print("--- Loading environment variables... ---")
load_dotenv()
# Redis Credentials (ใช้ตัวแปรแยกเพื่อความชัดเจน)
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
JOB_QUEUE_NAME = os.getenv("JOB_QUEUE_NAME", "video_processing_queue")
AI_QUEUE_NAME = "ai-analysis-queue"
# --- ส่วนที่เพิ่มเข้ามาเพื่อ Debug ---
print(f"DEBUG: Attempting to connect to Redis with the following credentials:")
print(f"DEBUG:   - HOST: {REDIS_HOST}")
print(f"DEBUG:   - PORT: {REDIS_PORT}")
print(f"DEBUG:   - PASSWORD: {'*' * len(REDIS_PASSWORD) if REDIS_PASSWORD else 'None'}")
print(f"DEBUG:   - QUEUE: {JOB_QUEUE_NAME}")
print("-----------------------------------------")
# ------------------------------------

# Database Credentials
DATABASE_URL = os.getenv("DATABASE_URL")

# --- ตั้งค่า Clients สำหรับเชื่อมต่อ Services ---
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

    # Redis Client (ระบุค่าการเชื่อมต่อแบบเจาะจง)
    print("Connecting to Redis...")
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=int(REDIS_PORT),
        password=REDIS_PASSWORD,
        ssl=True,  # บังคับใช้ SSL/TLS สำหรับ Upstash
        decode_responses=True # ทำให้ข้อมูลที่ได้เป็น string
    )
    redis_client.ping() # ทดสอบการเชื่อมต่อ
    print("Successfully connected to Redis.")

    print("Service clients initialized successfully.")
except Exception as e:
    print(f"!!! Failed to initialize clients: {e}")
    exit(1)


def process_video_job(job_data: dict):
    """
    ฟังก์ชันหลักในการประมวลผลวิดีโอ 1 งาน
    """
    video_id = job_data.get("video_id")
    r2_object_key = job_data.get("r2_object_key")
    print(f"Processing job for video_id: {video_id}")

    temp_dir = f"/tmp/{video_id}"
    os.makedirs(temp_dir, exist_ok=True)
    local_video_path = os.path.join(temp_dir, os.path.basename(r2_object_key))
    local_audio_path = os.path.join(temp_dir, "audio.m4a")
    audio_object_key = f"audio/{video_id}.m4a"

    db = SessionLocal()
    try:
        print(f"Downloading {r2_object_key} from R2...")
        s3_client.download_file(R2_BUCKET_NAME, r2_object_key, local_video_path)
        print("Download complete.")

        print("Extracting audio with FFmpeg...")
        subprocess.run(
            ["ffmpeg", "-i", local_video_path, "-vn", "-acodec", "copy", local_audio_path],
            check=True, capture_output=True, text=True
        )
        print("Audio extraction complete.")

        print(f"Uploading audio to R2 at {audio_object_key}...")
        s3_client.upload_file(local_audio_path, R2_BUCKET_NAME, audio_object_key)
        print("Audio upload complete.")

        print("Enqueuing job for AI analysis...")
        ai_job_data = { "video_id": video_id, "audio_r2_key": audio_object_key }
        redis_client.lpush(AI_QUEUE_NAME, json.dumps(ai_job_data))
        print(f"Successfully enqueued AI job for video_id: {video_id}")
        
        print("Updating database status to PENDING_AI_ANALYSIS...")
        update_query = text("UPDATE videos SET status = 'PENDING_AI_ANALYSIS', audio_r2_key = :audio_key WHERE id = :vid")
        db.execute(update_query, {"audio_key": audio_object_key, "vid": video_id})
        db.commit()
        print("Database updated.")

    except Exception as e:
        print(f"!!! AN ERROR OCCURRED for video_id {video_id}: {e}")
        try:
            error_query = text("UPDATE videos SET status = 'FAILED_PROCESSING' WHERE id = :vid")
            db.execute(error_query, {"vid": video_id})
            db.commit()
        except Exception as db_error:
            print(f"!!! Could not update status to FAILED for video_id {video_id}: {db_error}")
        
    finally:
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
            job_tuple = redis_client.brpop(JOB_QUEUE_NAME, timeout=0)
            if job_tuple:
                job_data_str = job_tuple[1]
                print(f"\n--- New Job Received ---")
                job_data = json.loads(job_data_str)
                process_video_job(job_data)
        except Exception as e:
            print(f"!!! A critical error occurred in the main loop: {e}")
            time.sleep(5) 

if __name__ == "__main__":
    main_loop()  