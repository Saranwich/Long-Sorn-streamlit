import redis
import json
from src.core.config import settings

class QueueService:
    def __init__(self):
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.queue_name = settings.JOB_QUEUE_NAME
            print("Successfully connected to Redis for queuing.")
        except Exception as e:
            print(f"Error connecting to Redis for queuing: {e}")
            self.redis_client = None

    def enqueue_video_processing_job(self, video_id: str, r2_object_key: str) -> bool:
        if self.redis_client is None:
            return False
        try:
            job_data = {
                "video_id": str(video_id),
                "r2_object_key": r2_object_key
            }
            self.redis_client.lpush(self.queue_name, json.dumps(job_data))
            print(f"Enqueued job for video_id: {video_id}")
            return True
        except Exception as e:
            print(f"Error enqueuing job: {e}")
            return False

queue_service = QueueService()