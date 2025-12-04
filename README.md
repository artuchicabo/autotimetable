# AutoTimetable - ระบบสร้างตารางเรียนอัตโนมัติ

## 🌐 เข้าใช้งานจากเน็ตไหนก็ได้

ระบบใช้ **Dynamic API URL Detection** - Frontend จะตรวจจับ hostname อัตโนมัติ:
- เข้าผ่าน **http://172.29.61.56:3000** → API: `http://172.29.61.56:5000`
- เข้าผ่าน **http://localhost:3000** → API: `http://localhost:5000`  
- เข้าผ่าน **http://yourdomain.com:3000** → API: `http://yourdomain.com:5000`

## 🚀 Quick Start

### Deploy บน Server
```bash
docker-compose up --build -d
```

### เข้าใช้งาน
**ในเครือข่ายเดียวกัน:**
- Frontend: http://172.29.61.56:3000
- Backend: http://172.29.61.56:5000

**จากภายนอก (Internet):** ต้องมี Public IP หรือใช้ Tunnel

## 🌍 เข้าถึงจาก Internet

### ตัวเลือก 1: ใช้ Public IP + Domain (แนะนำ)
1. ซื้อ domain (เช่น timetable.yourdomain.com)
2. ตั้งค่า DNS A Record → Public IP ของ server
3. Port forward ที่ router:
   - `80 → 3000` (frontend)
   - `5000 → 5000` (backend)
4. เข้าใช้: **http://timetable.yourdomain.com**

### ตัวเลือก 2: ngrok (ฟรี, ทดสอบง่าย)
```bash
# Terminal 1 - Expose frontend
ngrok http 3000

# Terminal 2 - Expose backend  
ngrok http 5000
```
จะได้ URL เช่น: `https://abc123.ngrok.io`

### ตัวเลือก 3: Cloudflare Tunnel (ฟรี)
```bash
# Install
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Run tunnel
cloudflared tunnel --url http://localhost:3000
```

## 📁 Project Structure
```
AUTOTIMETABLE/
├── backend/              # Flask API
│   ├── dataset/         # CSV data files
│   ├── key2.json        # Firebase credentials
│   └── Dockerfile
├── frontend/            # Vue.js UI
│   └── Dockerfile
└── docker-compose.yml
```

## 🔧 Manual Setup (Without Docker)

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py  # Runs on 0.0.0.0:5000
```

### Frontend
```bash
cd frontend
npm install
npm run build
npm run preview
```

## 🔑 Default Login
- **Admin**: ID: `admin`, Password: `admin`
- **Teacher**: ดูใน `backend/dataset/teacher.csv`

## ⚠️ Network Requirements

### สำหรับ Local Network
- เปิด ports: **3000, 5000**
- Bind to: **0.0.0.0** (already configured)

### สำหรับ Internet Access
- ต้องมี **Public IP** หรือใช้ tunnel service
- ตั้งค่า **port forwarding** ที่ router
- หรือใช้ **ngrok/cloudflare tunnel**

## 🐛 Troubleshooting

### ไม่สามารถเข้าจาก network อื่นได้
```bash
# 1. ตรวจสอบ firewall
sudo ufw allow 3000
sudo ufw allow 5000

# 2. ตรวจสอบว่า bind ถูกต้อง
netstat -tuln | grep :5000
# ต้องเห็น 0.0.0.0:5000 ไม่ใช่ 127.0.0.1:5000

# 3. ตรวจสอบ Docker logs
docker-compose logs backend
docker-compose logs frontend
```

### API connection refused
- Verify backend health: `curl http://<YOUR_IP>:5000`
- Check CORS settings in `backend/app.py`
- Check browser console for errors

## 📝 Features
- ✅ **Dynamic API URL** - ใช้งานได้จากเน็ตไหนก็ได้
- ✅ Real-time Firebase sync
- ✅ CRUD data management with edit
- ✅ AI timetable generation (Genetic Algorithm)
- ✅ Export to Excel/PDF
- ✅ Premium Aurora theme
