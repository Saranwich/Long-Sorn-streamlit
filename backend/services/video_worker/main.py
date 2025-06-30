# C:\Users\GitHub\Long-Sorn\backend\services\video_worker\main.py
# การส่งต่องานจาก Video Worker ไปยัง AI Orchestrator สร้างทางเชื่อมระหว่างการประมวลผลวิดีโอเบื้องต้นกับการวิเคราะห์ด้วย AI
import redis
import boto3
import json
import os
import subprocess
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from queue_service import queue_service

# --- โหลดการตั้งค่าจาก .env ---
load_dotenv()

# R2/S3 Credentials
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")

# Redis Credentials
REDIS_URL = os.getenv("REDIS_URL")
JOB_QUEUE_NAME = os.getenv("JOB_QUEUE_NAME", "video-processing-queue")

# Database Credentials
DATABASE_URL = os.getenv("DATABASE_URL")

# --- ตั้งค่า Clients สำหรับเชื่อมต่อ Services ---
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

def process_video_job(job_data: dict):
    """
    ฟังก์ชันหลักในการประมวลผลวิดีโอ 1 งาน
    """
    video_id = job_data.get("video_id")
    r2_object_key = job_data.get("r2_object_key")
    print(f"Processing job for video_id: {video_id}")

    # สร้างโฟลเดอร์ชั่วคราวสำหรับเก็บไฟล์
    temp_dir = f"/tmp/{video_id}"
    os.makedirs(temp_dir, exist_ok=True)
    local_video_path = os.path.join(temp_dir, os.path.basename(r2_object_key))
    local_audio_path = os.path.join(temp_dir, "audio.m4a") # or .mp3, .wav
    audio_object_key = f"{os.path.dirname(r2_object_key)}/audio.m4a"

    db = SessionLocal()
    try:
        # --- ดาวน์โหลดวิดีโอจาก R2 ---
        print(f"Downloading {r2_object_key} from R2...")
        s3_client.download_file(R2_BUCKET_NAME, r2_object_key, local_video_path)
        print("Download complete.")

        # --- ใช้ FFmpeg แยกเสียง --- 
        print("Extracting audio with FFmpeg...")
        subprocess.run(
            ["ffmpeg", "-i", local_video_path, "-vn", "-acodec", "copy", local_audio_path],
            check=True, capture_output=True
        )
        print("Audio extraction complete.")
        # --- อัปโหลดไฟล์เสียงกลับไปที่ R2 ---
        print(f"Uploading audio to R2 at {audio_object_key}...")
        s3_client.upload_file(local_audio_path, R2_BUCKET_NAME, audio_object_key)
        print("Audio upload complete.")

        # --- อัปเดตสถานะใน Database ---
        print("Updating database status...")
        update_query = text("""
            UPDATE videos SET status = 'SUCCESS', audio_r2_key = :audio_key WHERE id = :vid
        """)
        db.execute(update_query, {"audio_key": audio_object_key, "vid": video_id})
        db.commit()
        print("Database updated.")

        print("Enqueuing job for AI analysis...")
        ai_queue_name = "ai-analysis-queue" # คิวใหม่สำหรับ AI

        success = queue_service.enqueue_job(
            queue_name=ai_queue_name,
            job_data={
                "video_id": video_id,
                "audio_r2_key": audio_object_key # ส่ง Path ของไฟล์เสียงไปให้ AI Worker
            }
        )
        if success:
            print(f"Successfully enqueued AI job for video_id: {video_id}")
            # อัปเดตสถานะใน DB เป็น PENDING_AI_ANALYSIS
            update_query = text("UPDATE videos SET status = 'PENDING_AI_ANALYSIS', audio_r2_key = :audio_key WHERE id = :vid")
            db.execute(update_query, {"audio_key": audio_object_key, "vid": video_id})
            db.commit()
            print("Database status updated to PENDING_AI_ANALYSIS.")
        else:
            raise Exception("Failed to enqueue AI job.")

    except Exception as e:
        print(f"!!! AN ERROR OCCURRED for video_id {video_id}: {e}")
        error_query = text("UPDATE videos SET status = 'FAILED' WHERE id = :vid")
        db.execute(error_query, {"vid": video_id})
        db.commit()
        pass
    finally:
        # ลบไฟล์ชั่วคราว
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        db.close()
        print(f"Finished job for video_id: {video_id}\n")
        pass
    