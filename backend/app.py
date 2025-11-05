# อัพเดต 1.0 - app.py
from flask import Flask, render_template
from routes import register_routes
import firebase_admin
from firebase_admin import credentials, db
import os

SERVICE_ACCOUNT = "serviceAccountKey.json"
if not os.path.exists(SERVICE_ACCOUNT):
    raise RuntimeError("❌ ไม่พบไฟล์ serviceAccountKey.json — ใส่ไฟล์คีย์ Firebase ลงในโฟลเดอร์ backend/ ก่อน")

cred = credentials.Certificate(SERVICE_ACCOUNT)
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://autotimetable-382ee-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

app = Flask(__name__, template_folder="templates")

# ลงทะเบียน route ทั้งหมด (Realtime DB)
register_routes(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/manage')
def manage():
    return render_template('manage.html')

if __name__ == '__main__':
    app.run(debug=True)
