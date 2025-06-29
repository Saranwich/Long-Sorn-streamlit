# backend/services/api-server/src/models/video.py

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as PgEnum
from sqlalchemy.dialects.postgresql import UUID
from src.shared.db.database import Base

class VideoStatus(str, enum.Enum):
    """Enum for video processing statuses."""
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class Video(Base):
    """
    Represents the Video model in our database.
    This table tracks the state of each video uploaded by a user.
    """
    __tablename__ = "videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    original_filename = Column(String, nullable=False)
    r2_object_key = Column(String, unique=True, nullable=False)
    audio_r2_key = Column(String, unique=True, nullable=True) # To be filled by worker
    
    status = Column(PgEnum(VideoStatus, name="video_status_enum"), nullable=False, default=VideoStatus.UPLOADING)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)