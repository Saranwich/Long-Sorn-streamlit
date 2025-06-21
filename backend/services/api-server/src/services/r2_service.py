# src/services/r2_service.py

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from ..core.config import settings

class R2Service:
    """
    Service class for interacting with Cloudflare R2 Storage.
    """
    def __init__(self):
        # 1. อ่านค่า Config และ 2. สร้าง Client ของ boto3
        try:
            self.client = boto3.client(
                service_name='s3',
                endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT_URL,
                aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
                config=Config(signature_version='s3v4'),
                region_name='auto'  # For Cloudflare R2, 'auto' is standard
            )
            self.bucket_name = settings.CLOUDFLARE_R2_BUCKET_NAME
            print("Successfully connected to Cloudflare R2.")
        except Exception as e:
            print(f"Error connecting to R2: {e}")
            self.client = None

    def generate_presigned_upload_url(self, object_key: str, expiration: int = 3600) -> str | None:
        """
        3. เรียกใช้ฟังก์ชัน generate_presigned_url เพื่อสร้าง Signed URL
        สำหรับอัปโหลดไฟล์ (HTTP PUT)
        """
        if self.client is None:
            return None
            
        try:
            url = self.client.generate_presigned_url(
                ClientMethod='put_object',
                Params={'Bucket': self.bucket_name, 'Key': object_key},
                ExpiresIn=expiration  # URL is valid for 1 hour
            )
            return url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

# สร้าง instance ของ service ไว้เพื่อให้ง่ายต่อการ import ไปใช้ในที่ต่างๆ
r2_service = R2Service()