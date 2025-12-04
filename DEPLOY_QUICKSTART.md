# AutoTimetable - Quick Deploy Guide

## 🚀 เริ่มต้นเร็วที่สุด: Render.com (แนะนำ)

### 1. เตรียม GitHub
```bash
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/autotimetable.git
git push -u origin main
```

### 2. Deploy บน Render.com
1. สมัครที่ https://render.com (ฟรี)
2. New → Blueprint
3. เลือก repo → Apply
4. ตั้ง environment variable: `FIREBASE_CREDENTIALS` (วาง key2.json content)
5. รอ 5-10 นาที → เสร็จ! 🎉

## 📚 คู่มือเต็ม
ดูรายละเอียดทั้งหมดใน [DEPLOYMENT.md](./DEPLOYMENT.md)

## ✅ ไฟล์ที่สร้างแล้ว
- ✅ `render.yaml` - Render.com config
- ✅ `railway.json` - Railway config  
- ✅ `frontend/nginx.conf` - Production web server
- ✅ `.gitignore` - Security (ป้องกันไฟล์ sensitive)
- ✅ `DEPLOYMENT.md` - คู่มือครบทุกแพลตฟอร์ม

## 🧪 ทดสอบก่อน Deploy
```bash
docker-compose up --build
```
เข้า http://localhost:3000 ตรวจสอบว่าใช้งานได้

## 🆓 Platform Comparison
| Platform | ฟรี | ง่าย | เร็ว |
|----------|-----|------|------|
| Render.com | ✅ | ⭐⭐⭐⭐⭐ | ช้าครั้งแรก |
| Railway | ✅ ($5/mo) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Cloud Run | ✅ | ⭐⭐ | ⭐⭐⭐⭐ |
