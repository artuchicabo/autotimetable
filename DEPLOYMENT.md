# 🚀 AutoTimetable - คู่มือ Deploy บน Docker (ฟรี 100%)

## 📋 สารบัญ
- [ตัวเลือก Platform](#-ตัวเลือก-platform-ฟรีทั้งหมด)
- [Render.com (แนะนำ!)](#-1-rendercom-แนะนำ)
- [Railway](#-2-railway)
- [Google Cloud Run](#-3-google-cloud-run)
- [ทดสอบก่อน Deploy](#-ทดสอบก่อน-deploy)

---

## 🎯 ตัวเลือก Platform (ฟรีทั้งหมด)

| Platform | ฟรี | Auto Deploy | Cold Start | ความยาก | แนะนำ |
|----------|-----|-------------|------------|---------|-------|
| **Render.com** | ✅ ถาวร | ✅ | ~30 วินาที | ⭐ ง่าย | ⭐⭐⭐⭐⭐ |
| **Railway** | ✅ $5/เดือน | ✅ | ไม่มี | ⭐⭐ กลาง | ⭐⭐⭐⭐ |
| **Cloud Run** | ✅ 2M req/เดือน | ⚠️ Manual | ไม่มี | ⭐⭐⭐ ยาก | ⭐⭐⭐ |

---

## 🌟 1. Render.com (แนะนำ!)

### ข้อดี
- ✅ ฟรีถาวร ไม่ต้องใส่บัตรเครดิต
- ✅ Auto SSL (HTTPS)
- ✅ Auto deploy จาก Git
- ✅ Dashboard ใช้งานง่าย

### ข้อจำกัด
- ⚠️ Sleep หลังไม่มีคนใช้ 15 นาที (ครั้งแรกช้า ~30 วินาที)
- ⚠️ 750 hours/เดือน (พอสำหรับ demo)

### 📝 ขั้นตอน Deploy

#### 1. เตรียม GitHub Repository
```bash
# ใน project directory
git init
git add .
git commit -m "Initial commit for deployment"

# สร้าง repo บน GitHub แล้ว push
git remote add origin https://github.com/YOUR_USERNAME/autotimetable.git
git branch -M main
git push -u origin main
```

> ⚠️ **สำคัญ!** ห้าม commit `backend/key2.json` และ `backend/.env` 

ตรวจสอบ `.gitignore`:
```gitignore
# Backend
backend/.env
backend/key2.json
backend/__pycache__/
backend/*.pyc

# Frontend
frontend/node_modules/
frontend/dist/
frontend/.env
```

#### 2. สมัคร Render.com
1. ไปที่ https://render.com
2. คลิก **"Get Started for Free"**
3. Sign up ด้วย GitHub account

#### 3. Deploy ด้วย Blueprint
1. ใน Dashboard → **"New"** → **"Blueprint"**
2. เลือก repository `autotimetable`
3. Render จะอ่าน `render.yaml` อัตโนมัติ
4. คลิก **"Apply"**

#### 4. ตั้งค่า Environment Variables

**Backend Service:**
1. เข้า `autotimetable-backend` service
2. คลิก **"Environment"** tab
3. เพิ่ม variable:
   ```
   Key: FIREBASE_CREDENTIALS
   Value: <วาง content ทั้งหมดจากไฟล์ key2.json>
   ```

**วิธีดู content ของ key2.json:**
```bash
# Windows PowerShell
Get-Content backend\key2.json | Set-Clipboard
# แล้ว Paste ใน Render
```

#### 5. รอ Deploy เสร็จ
- Backend: 5-10 นาที
- Frontend: 3-5 นาที

#### 6. รับ URL
จะได้ URL ประมาณนี้:
- Backend: `https://autotimetable-backend-xxxx.onrender.com`
- Frontend: `https://autotimetable-frontend-xxxx.onrender.com`

✅ **เสร็จแล้ว!** เข้าใช้งานได้ทันที

---

## 🚂 2. Railway

### ข้อดี
- ✅ $5 credit ฟรี/เดือน (พอใช้ ~500 ชั่วโมง)
- ✅ ไม่มี Cold Start
- ✅ Deploy เร็ว
- ✅ UI/UX สวยมาก

### ข้อจำกัด
- ⚠️ ต้องใส่บัตรเครดิต (แต่ไม่ charge ถ้าไม่เกิน $5)
- ⚠️ Credit จะหมดถ้าใช้ตลอด 24/7

### 📝 ขั้นตอน Deploy

#### 1. เตรียม GitHub Repository
(เหมือนขั้นตอน Render ข้างบน)

#### 2. สมัคร Railway
1. ไปที่ https://railway.app
2. คลิก **"Start a New Project"**
3. Sign in ด้วย GitHub

#### 3. สร้าง Project
1. **"New Project"** → **"Deploy from GitHub repo"**
2. เลือก repository `autotimetable`

#### 4. สร้าง Service สำหรับ Backend
1. คลิก **"Add Service"** → **"GitHub Repo"**
2. Configure:
   - **Root Directory**: `backend`
   - **Dockerfile Path**: `backend/Dockerfile`
3. เพิ่ม Environment Variables:
   ```
   FLASK_APP=app.py
   FLASK_ENV=production
   PORT=5000
   FIREBASE_CREDENTIALS=<paste key2.json>
   ```
4. Deploy

#### 5. สร้าง Service สำหรับ Frontend
1. ในโปรเจกต์เดียวกัน คลิก **"New Service"**
2. Configure:
   - **Root Directory**: `frontend`
   - **Dockerfile Path**: `frontend/Dockerfile`
3. Deploy

#### 6. รับ URL
Railway จะ generate URL ให้อัตโนมัติ:
- Backend: `https://autotimetable-backend-production.up.railway.app`
- Frontend: `https://autotimetable-frontend-production.up.railway.app`

---

## ☁️ 3. Google Cloud Run

### ข้อดี
- ✅ 2 ล้าน requests ฟรี/เดือน
- ✅ Scale อัตโนมัติ
- ✅ Enterprise-grade infrastructure

### ข้อจำกัด
- ⚠️ ต้องใส่บัตรเครดิต
- ⚠️ Setup ซับซ้อนกว่า

### 📝 ขั้นตอน Deploy

#### 1. Install Google Cloud CLI
```bash
# Download from: https://cloud.google.com/sdk/docs/install
# หลัง install แล้ว login
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### 2. Enable APIs
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

#### 3. Deploy Backend
```bash
cd backend

# Build และ Push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/timetable-backend

# Deploy to Cloud Run
gcloud run deploy timetable-backend \
  --image gcr.io/YOUR_PROJECT_ID/timetable-backend \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars "FLASK_ENV=production,FLASK_APP=app.py,PORT=5000" \
  --set-env-vars "FIREBASE_CREDENTIALS=$(cat key2.json)"
```

#### 4. Deploy Frontend
```bash
cd ../frontend

# Build และ Push image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/timetable-frontend

# Deploy to Cloud Run
gcloud run deploy timetable-frontend \
  --image gcr.io/YOUR_PROJECT_ID/timetable-frontend \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated
```

#### 5. รับ URL
Cloud Run จะแสดง URL:
```
Service [timetable-backend] deployed to:
https://timetable-backend-xxxxx-as.a.run.app

Service [timetable-frontend] deployed to:
https://timetable-frontend-xxxxx-as.a.run.app
```

---

## 🧪 ทดสอบก่อน Deploy

### 1. ทดสอบ Docker ใน Local
```bash
# Build และ run ทั้ง backend + frontend
docker-compose up --build

# ทดสอบ:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:5000
```

### 2. Checklist การทดสอบ
- [ ] Login ได้ (admin/admin)
- [ ] เพิ่ม/แก้ไข/ลบ Teachers, Subjects, Rooms, Groups ได้
- [ ] Generate timetable ได้
- [ ] Export Excel/PDF ทำงาน
- [ ] เปิด Browser Console (F12) → ไม่มี error สีแดง

### 3. Debug Tips
```bash
# ดู logs
docker-compose logs backend
docker-compose logs frontend

# เข้าไปใน container
docker exec -it timetable_backend sh
docker exec -it timetable_frontend sh

# Stop และลบ containers
docker-compose down
```

---

## 🔒 Security Checklist

- [ ] ไฟล์ `key2.json` **ไม่ถูก commit** ลง Git
- [ ] ไฟล์ `.env` **ไม่ถูก commit** ลง Git
- [ ] `.gitignore` ครอบคลุม sensitive files
- [ ] Firebase credentials ใส่ผ่าน environment variables
- [ ] CORS settings อนุญาตเฉพาะ domain ที่ deploy

---

## 🆘 Troubleshooting

### ปัญหา: Backend 500 Error
```bash
# ดู logs ใน Render/Railway dashboard
# หรือใน Cloud Run:
gcloud run services logs read timetable-backend --region asia-southeast1
```

**สาเหตุมักเจอ:**
- ❌ Firebase credentials ไม่ถูกต้อง
- ❌ Environment variables ไม่ครบ
- ❌ Dependencies ขาดหาย

### ปัญหา: Frontend ไม่เชื่อม Backend
1. เปิด Browser Console (F12)
2. ดู Network tab
3. ตรวจสอบ API URL ถูกต้องหรือไม่

**แก้ไข:** Frontend ใช้ dynamic API detection อัตโนมัติ
- หากไม่ work ให้ hardcode ใน `frontend/src/config.js`:
  ```javascript
  const API_URL = 'https://your-backend-url.onrender.com'
  ```

### ปัญหา: CORS Error
ตรวจสอบใน `backend/app.py`:
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # อนุญาตทุก origin
```

---

## 📞 ต้องการความช่วยเหลือ?

1. ตรวจสอบ logs ของ service ก่อน
2. ลอง deploy ใหม่ (`Redeploy` button)
3. ตรวจสอบ environment variables ครบหรือไม่

**Platform Support:**
- Render: https://render.com/docs
- Railway: https://docs.railway.app
- Cloud Run: https://cloud.google.com/run/docs

---

## 🎉 สำเร็จแล้ว!

หลัง deploy เสร็จแล้ว คุณจะได้:
- ✅ **Free HTTPS website** ใช้งานได้ทั่วโลก
- ✅ **Auto deployment** ทุกครั้งที่ push GitHub
- ✅ **Custom domain** (optional - ตั้งค่าได้ใน dashboard)

**URLs ของคุณ:**
- Frontend: `https://your-app.onrender.com`
- Backend API: `https://your-api.onrender.com`

แชร์ URL ให้เพื่อนใช้ได้เลย! 🚀
