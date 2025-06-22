# /backend/services/api-server/src/api/endpoints/videos.py

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import uuid
from sqlalchemy.orm import Session

# --- ส่วน Imports ที่ต้องมีในโปรเจค ---
from src.api.dependencies import get_current_user  # Dependency สำหรับ User
from src.shared.db.database import get_db_session  # Dependency สำหรับ Database Session
from src.services.r2_service import r2_service # Service R2
from src.services.queue_service import queue_service
# Models
from src.models.auth import User
from src.models.video import Video, VideoStatus

# Router for endpoint
router = APIRouter(prefix="/videos", tags=["Videos"])

# --- Pydantic Schemas สำหรับ Request/Response ---
class VideoUploadRequest(BaseModel):
    filename: str
    content_type: str # "video/mp4"

class VideoUploadResponse(BaseModel):
    video_id: uuid.UUID
    upload_url: str

# --- Endpoint ---    
@router.post("/request-upload", status_code=200, response_model=VideoUploadResponse, summary="Request a URL to upload a video", description="Initializes a video record in the database and returns a secure, short-lived URL for the client to upload the file directly to Cloudflare R2.")

@router.post(
    "/{video_id}/upload-complete",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Confirm video upload is complete and trigger processing",
    description="Called by the client after a file is successfully uploaded to R2. This updates the video status and enqueues it for background processing."
)

def request_video_upload(request_data: VideoUploadRequest, db: Session = Depends(get_db_session), current_user: User = Depends(get_current_user)):
    """
    Endpoint สำหรับให้ User ที่ล็อกอินแล้วขอสิทธิ์ในการอัปโหลดวิดีโอ
    """
    # สร้าง Key ที่จะไม่ซ้ำกันสำหรับเก็บไฟล์ใน R2
    video_id = uuid.uuid4()
    object_key = f"users/{current_user.id}/videos/{video_id}/{request_data.filename}"
    # เรียกใช้ Service เพื่อสร้าง Signed URL
    upload_url = r2_service.generate_presigned_upload_url(object_key)

    if not upload_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not create an upload URL at this time. Please try again later.",
        )
    # บันทึกข้อมูลเบื้องต้นของวิดีโอลงในตาราง videos
    try:
        new_video_record = Video(
            id=video_id,
            user_id=current_user.id,
            original_filename=request_data.filename,
            r2_object_key=object_key,
            status=VideoStatus.UPLOADING, # กำหนดสถานะเริ่มต้น
            # ... สามารถเพิ่ม fields อื่นๆ เช่น content_type ได้
        )
        db.add(new_video_record)
        db.commit()
        db.refresh(new_video_record)
    except Exception as e:
        # มี logging ที่ดี เพื่อให้ทีม backend ตรวจสอบได้
        print(f"Database Error on creating video record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while preparing the video record.",
        )
    # ส่ง Signed URL ที่ได้กลับไปเป็น Response
    return VideoUploadResponse(
        video_id=new_video_record.id,
        upload_url=upload_url
    )

def confirm_upload_complete(
    video_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # ค้นหาวิดีโอใน DB และตรวจสอบความเป็นเจ้าของ
    video_record = db.query(Video).filter(Video.id == video_id, Video.user_id == current_user.id).first()

    if not video_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found or you do not have permission to access it."
        )
    # อัปเดตสถานะวิดีโอ
    video_record.status = VideoStatus.UPLOADED # or PENDING_PROCESSING
    db.commit()
    # ส่ง Job เข้าสู่ Queue ผ่าน Service
    success = queue_service.enqueue_video_processing_job(
        video_id=str(video_record.id),
        r2_object_key=video_record.r2_object_key
    )

    if not success:
        # หากส่งเข้าคิวไม่สำเร็จมี Logic จัดการ เช่น ตั้งสถานะเป็น FAILED_TO_QUEUE
        # หรือมีระบบ retry ภายหลัง
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue video for processing."
        )
    
    return {"status": "ok", "message": "Video processing has been successfully queued."}