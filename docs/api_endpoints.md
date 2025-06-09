# Long Sorn API Documentation (v1)
เอกสารนี้อธิบายถึง API endpoint สำหรับโปรเจกต์ Long Sorn (v1). API ทั้งหมดถูกออกแบบตามหลักการ RESTful เพื่อให้ง่ายต่อการใช้งานและทำความเข้าใจ

### ข้อมูลพื้นฐาน
**Base URL:** 
```
/api/v1
```
**Authentication:**
ระบบใช้ JWT (JSON Web Token) ในการยืนยันตัวตน สำหรับ Endpoint ที่ต้องการการยืนยันตัวตน ให้แนบ Token ไปใน Header ดังนี้
```
Authorization: Bearer <your_jwt_token>
```

## รูปแบบการตอบกลับ
- **Success:** การร้องขอที่สำเร็จจะได้รับ HTTP Status Code 2xx พร้อมข้อมูลในรูปแบบ JSON
- **Error:** การร้องขอที่ผิดพลาดจะได้รับ HTTP Status Code 4xx หรือ 5xx พร้อมข้อมูลในรูปแบบ JSON
```
{
  "detail": "คำอธิบายข้อผิดพลาด"
}
```

## Authentication Endpoints (/auth)
Endpoints ที่เกี่ยวข้องกับการลงทะเบียนและเข้าสู่ระบบ

#### POST /auth/register

- **คำอธิบาย:** สร้างบัญชีผู้ใช้ใหม่
- **ยืนยันตัวตน:** ไม่ต้องใช้ (Public)
**Request Body:**
```
{
  "name": "Krittikorn Sangthong",
  "email": "arm@superai.com",
  "password": "passwordnotfound"
}
```
**Success Response (201 Created):**
```
{
  "id": "user-id-1412",
  "name": "Krittikorn Sangthong",
  "email": "arm@superai.com",
  "created_at": "2025-06-09T15:00:00Z"
}
```
**Error Responses:**
- **409 Conflict:** หากมีอีเมลนี้อยู่ในระบบแล้ว

#### POST /auth/register
- **คำอธิบาย:** เข้าสู่ระบบเพื่อรับ Access Token (JWT)
- **ยืนยันตัวตน:** ไม่ต้องใช้ (Public)
**Request Body:**
```
{
  "email": "arm@superai.com",
  "password": "passwordnotfound"
}
```
**Success Response (200 OK):**
```
{
  "access_token": "your_long_jwt_token_here",
  "token_type": "bearer"
}
```
**Error Responses:**
- 401 Unauthorized: หากอีเมลหรือรหัสผ่านไม่ถูกต้อง

## User Endpoints (/users)
Endpoints สำหรับจัดการข้อมูลผู้ใช้

#### GET /users/me
- **คำอธิบาย:** ดึงข้อมูลโปรไฟล์ของผู้ใช้ที่กำลัง login อยู่ (ดูจาก Token)
- **ยืนยันตัวตน:** ต้องใช้
**Success Response (200 OK):**
```
{
  "id": "user-id-1412",
  "name": "Krittikorn Sangthong",
  "email": "arm@superai.com",
  "created_at": "2025-06-09T15:00:00Z"
}
```
#### PUT /users/me
- **คำอธิบาย:** อัปเดตข้อมูลโปรไฟล์ของผู้ใช้ที่กำลัง login อยู่
- **ยืนยันตัวตน:** ต้องใช้
**Request Body:**
```
{
  "name": "Arm Krittikorn"
}
```
**Success Response (200 OK):**
```
{
  "id": "user-id-123",
  "name": "Arm Krittikorn",
  "email": "arm@superai.com",
  "created_at": "2025-06-09T15:00:00Z"
}
```

## Video & Analysis Endpoints (/videos)
Endpoints สำหรับจัดการวิดีโอและผลการวิเคราะห์

#### POST /videos/upload-url
- **คำอธิบาย:** (Step 1) ขอ URL ที่ปลอดภัย (Signed URL) สำหรับอัปโหลดไฟล์วิดีโอไปยัง Cloud Storage
- **ยืนยันตัวตน:** ต้องใช้
**Request Body:**
```
{
  "fileName": "my_video.mp4",
  "contentType": "video/mp4"
}
```
**Success Response (200 OK):**
```
{
  "videoId": "video-id-abc-456",
  "uploadUrl": "https://<cloudflare_r2_signed_url>"
}
```
- หมายเหตุ: หลังจากได้ uploadUrl แล้ว Frontend จะต้องใช้ PUT method เพื่อส่ง File ของวิดีโอไปที่ URL นั้นโดยตรง

#### POST /videos/{video_id}/upload-complete
- **คำอธิบาย:** (Step 2) แจ้ง Server ว่าการอัปโหลดไฟล์ไปยัง Cloud Storage ในขั้นตอนที่ 1 เสร็จสิ้นแล้ว
- **ยืนยันตัวตน:** ต้องใช้
- **Path Parameter:** video_id (ID จาก Step 1)
**Success Response (202 Accepted):**
```
{
  "message": "Video accepted and is now being processed."
}
```
- หมายเหตุ: การเรียก API นี้จะไปกระตุ้นให้ Backend เริ่มกระบวนการประมวลผลวิดีโอ (ส่งงานเข้า Queue)

#### GET /videos
- **คำอธิบาย:** ดึงรายการวิดีโอทั้งหมดของผู้ใช้ที่กำลัง login อยู่ (แบบแบ่งหน้า)
- **ยืนยันตัวตน:** ต้องใช้
**Query Parameters (ตัวเลือก):**
- skip (number, default: 0): จำนวนรายการที่ต้องการข้าม
- limit (number, default: 20): จำนวนรายการสูงสุดที่ต้องการในหนึ่งหน้า
**Success Response (200 OK):**
```
{
  "items": [
    {
      "id": "video-id-abc-456",
      "title": "my_video.mp4",
      "status": "COMPLETED",
      "createdAt": "2025-06-09T15:05:00Z"
    },
    {
      "id": "video-id-xyz-789",
      "title": "weekly_update.mov",
      "status": "PROCESSING",
      "createdAt": "2025-06-09T15:10:00Z"
    }
  ]
}
```
#### GET /videos/{video_id}
- **คำอธิบาย:** ดึงข้อมูลของวิดีโอ 1 ไฟล์ พร้อมผลการวิเคราะห์ทั้งหมด
- **ยืนยันตัวตน:** ต้องใช้
**Path Parameter:** video_id
**Success Response (200 OK):**
```
{
  "id": "video-id-abc-456",
  "title": "my_video.mp4",
  "status": "COMPLETED", // อาจจะเป็น "PROCESSING", "FAILED"
  "createdAt": "2025-06-09T15:05:00Z",
  "analysis": { // จะเป็น null หาก status ยังไม่ COMPLETED
    "summary": "ผู้สอนพูดได้ดี แต่มีคำว่า 'เอ่อ' บ่อยครั้งในช่วงต้น",
    "fillerWordsCount": 15,
    "advice": [
      {
        "timestamp": "00:01:23",
        "type": "FILLER_WORD",
        "suggestion": "ลองหยุดหายใจแทนการพูดคำว่า 'เอ่อ' ในจุดนี้"
      },
      {
        "timestamp": "00:05:40",
        "type": "SPEAKING_RATE",
        "suggestion": "ช่วงนี้พูดเร็วเกินไป ลองลดความเร็วลงเล็กน้อย"
      }
    ]
  }
}
```