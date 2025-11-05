from flask import Flask, render_template
from routes import register_routes
import firebase_admin
from firebase_admin import credentials, db
import os

cred = credentials.Certificate("config/Key.json")


firebase_admin.initialize_app(cred, {
    'databaseURL': "https://autotimetable-382ee-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

# # -----------------------------
# # 🔐 ตรวจสอบไฟล์คีย์ Firebase
# # -----------------------------
# SERVICE_ACCOUNT = "serviceAccountKey.json"  # ✅ ชื่อไฟล์ต้องตรงกับไฟล์จริง
# if not os.path.exists(SERVICE_ACCOUNT):
#     raise RuntimeError("❌ ไม่พบไฟล์ serviceAccountKey.json — ใส่ไฟล์คีย์ Firebase ลงในโฟลเดอร์ backend/ ก่อน")

# # -----------------------------
# # 🔗 เชื่อมต่อ Firebase Realtime Database
# # -----------------------------
# cred = credentials.Certificate(SERVICE_ACCOUNT)
# firebase_admin.initialize_app(credentials, {
#     "databaseURL": "https://autotimetable-382ee-default-rtdb.asia-southeast1.firebasedatabase.app/"
# })

# -----------------------------
# ⚙️ สร้างแอป Flask
# -----------------------------
app = Flask(__name__, template_folder="templates")

# -----------------------------
# 📡 ลงทะเบียน routes ทั้งหมด (ไม่ต้องส่ง db)
# -----------------------------
register_routes(app)

# -----------------------------
# 🏠 Routes หน้าเว็บหลัก
# -----------------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/manage')
def manage():
    return render_template('manage.html')

# -----------------------------
# 🚀 รันแอป
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
