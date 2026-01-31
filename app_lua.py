import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
from datetime import datetime
from gtts import gTTS
import requests
from streamlit_js_eval import get_geolocation
import google.generativeai as genai
import os
from dotenv import load_dotenv

# CONFIG GEMINI
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Bác Sĩ Lúa AI 4.0", page_icon="🌾", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f4fdf4; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 8px solid #2e7d32; }
    h1 { color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

# KHỞI TẠO SESSION STATE
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "🌾 Chào bà con! Hỏi tôi về bệnh lúa, thuốc trừ, kinh nghiệm phun thuốc..."}
    ]

# DỮ LIỆU BỆNH
DATA_BENH = {
    "Bacterial Leaf Blight": {
        "ten": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "trieu_chung": "Vết bệnh lan dọc mép lá từ chóp xuống, màu vàng hoặc trắng xám, rìa gợn sóng.",
        "nguyen_nhan": "Vi khuẩn Xanthomonas oryzae. Thừa đạm, mưa bão làm rách lá lây lan.",
        "thuoc": ["Starner 20WP", "Xanthomix 20WP", "Totan 200WP"],
        "loi_khuyen": "Ngưng bón đạm, bón bổ sung Kali. Rút nước ruộng để hạn chế vi khuẩn.",
        "icon": "🦠"
    },
    "Blast": {
        "ten": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "trieu_chung": "Vết bệnh hình mắt én, tâm xám trắng, viền nâu đậm. Nặng có thể gây cháy cả lá.",
        "nguyen_nhan": "Nấm Pyricularia oryzae. Trời âm u, sương mù, độ ẩm cao.",
        "thuoc": ["Beam 75WP", "Fuji-one 40EC", "Filia 525SE"],
        "loi_khuyen": "Giữ nước ruộng ổn định. Không phun phân bón lá khi lúa đang bệnh.",
        "icon": "🔥"
    },
    "Brown Spot": {
        "ten": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "trieu_chung": "Vết bệnh tròn nhỏ màu nâu như hạt mè rải rác trên phiến lá.",
        "nguyen_nhan": "Nấm. Thường gặp ở ruộng thiếu dinh dưỡng, đất phèn, ngộ độc hữu cơ.",
        "thuoc": ["Tilt Super 300EC", "Anvil 5SC"],
        "loi_khuyen": "Cần bón cân đối N-P-K, bổ sung vôi để cải tạo đất phèn.",
        "icon": "🍂"
    }
}
DATA_BENH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"},
    "Rice Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"}
})

def lay_thoi_tiet(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain&timezone=auto"
        return requests.get(url, timeout=5).json().get('current')
    except: 
        return None

def ve_bbox_len_anh(img, predictions):
    """Vẽ % confidence lên ảnh như Roboflow"""
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    for pred in predictions[:3]:
        conf = pred['confidence'] * 100
        label = f"{pred['class']}: {conf:.1f}%"
        x, y = 20, 20 + predictions.index(pred) * 40
        bbox = draw.textbbox((x, y), label, font=font)
        draw.rectangle(bbox, fill=(0, 128, 0, 200))
        draw.text((x, y), label, fill=(255, 255, 255), font=font)
    return img

# HEADER
st.markdown("<h1>🌾 BÁC SĨ LÚA AI 4.0</h1>", unsafe_allow_html=True)
st.caption("Giải pháp chẩn đoán bệnh lúa qua hình ảnh + Tư vấn AI với Gemini")

# THỜI TIẾT
st.markdown("### 🌤️ Thời Tiết Nông Vụ Thực Tế")
loc = get_geolocation()

if loc and 'coords' in loc:
    lat, lon = loc['coords'].get('latitude'), loc['coords'].get('longitude')
    weather = lay_thoi_tiet(lat, lon)
    if weather:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🌡️ Nhiệt độ", f"{weather['temperature_2m']}°C")
        c2.metric("💧 Độ ẩm", f"{weather['relative_humidity_2m']}%")
        c3.metric("🌧️ Mưa", f"{weather['rain']} mm")
        with c4:
            if weather['rain'] > 0: 
                st.error("⚠️ Đang mưa: Đừng phun thuốc!")
            elif weather['relative_humidity_2m'] > 85: 
                st.warning("🔥 Ẩm cao: Cẩn thận đạo ôn!")
            else: 
                st.success("🌤️ Thời tiết tốt")
else:
    st.info("📍 Vui lòng 'Cho phép' truy cập vị trí để xem thời tiết chính xác tại ruộng")

st.markdown("---")

# TABS
tab1, tab2, tab3 = st.tabs(["🔍 CHẨN ĐOÁN HÌNH ẢNH", "💬 TƯ VẤN GEMINI AI", "📋 LỊCH SỬ KHÁM"])

# TAB 1: CHẨN ĐOÁN
with tab1:
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        st.subheader("1. Chụp ảnh/Tải ảnh lá lúa")
        
        # CHỌN NGUỒN
        input_type = st.radio("Chọn nguồn:", ["Tải ảnh từ máy", "Chụp bằng Camera"], horizontal=True)
        
        if input_type == "Chụp bằng Camera":
            file = st.camera_input("Chụp ảnh lá lúa")
        else:
            file = st.file_uploader("Chọn file ảnh", type=['jpg','png','jpeg'])

    if file:
        img = Image.open(file).convert("RGB")
        with col_l:
            st.image(img, use_column_width=True, caption="Mẫu bệnh đầu vào")
            
            if st.button("🚀 BẮT ĐẦU CHẨN ĐOÁN", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("AI đang phân tích từ model Roboflow của bạn..."):
                        img.save("process.jpg")
                        
                        # GỌI ROBOFLOW MODEL
                        client = InferenceHTTPClient(
                            api_url="https://detect.roboflow.com", 
                            api_key="8tf2UvcnEv8h80bV2G0Q"
                        )
                        res = client.infer("process.jpg", model_id="rice-leaf-disease-twtlz/1")
                        preds = res.get('predictions', [])
                        
                        if isinstance(preds, dict): 
                            preds = [{"class": k, "confidence": v['confidence']} for k, v in preds.items()]

                        if preds:
                            # TOP 3
                            top3 = sorted(preds, key=lambda x: x['confidence'], reverse=True)[:3]
                            
                            # VẼ % LÊN ẢNH
                            img_annotated = ve_bbox_len_anh(img.copy(), top3)
                            st.image(img_annotated, caption="Kết quả AI với % Confidence")
                            
                            # HIỂN THỊ METRIC TOP 3
                            st.subheader("📊 Độ tin cậy từ Model Roboflow")
                            c1, c2, c3 = st.columns(3)
                            for i, pred in enumerate(top3):
                                with [c1, c2, c3][i]:
                                    emoji = "🟢" if i==0 else "🟡" if i==1 else "🟠"
                                    st.metric(f"{emoji} {pred['class']}", f"{pred['confidence']*100:.1f}%")
                            
                            # THÔNG TIN BỆNH TOP 1
                            top = top3[0]
                            benh = DATA_BENH.get(top['class'])
                            if benh and "ref" in benh: 
                                benh = DATA_BENH.get(benh["ref"])
                            
                            if benh:
                                st.markdown(f"### ✅ Kết luận: {benh['ten']} ({top['confidence']*100:.1f}%)")
                                st.markdown(f"""
                                <div class="report-card">
                                    <p><b>🧐 Dấu hiệu:</b> {benh.get('trieu_chung','Chưa có dữ liệu')}</p>
                                    <p><b>🌪️ Nguyên nhân:</b> {benh.get('nguyen_nhan','Chưa có dữ liệu')}</p>
                                    <p style="color: #d32f2f;"><b>💊 Thuốc đặc trị:</b> {', '.join(benh['thuoc'])}</p>
                                    <p><b>💡 Lời khuyên:</b> {benh.get('loi_khuyen','')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # GIỌNG NÓI
                                txt_read = f"Lúa bị {benh['ten']}. Bà con dùng thuốc {benh['thuoc'][0]}."
                                gTTS(txt_read, lang='vi').save("voice.mp3")
                                st.audio("voice.mp3")
                                
                                # LƯU LỊCH SỬ
                                st.session_state.history.append({
                                    "time": datetime.now().strftime("%H:%M"),
                                    "benh": benh['ten'],
                                    "conf": top['confidence']*100
                                })
                        else:
                            st.success("🌿 Cây lúa khỏe mạnh! Chúc mừng bà con.")

# TAB 2: CHATBOT GEMINI
with tab2:
    st.subheader("💬 Hỏi đáp cùng chuyên gia Gemini AI")
    
    # Hiển thị lịch sử chat
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Input câu hỏi
    if prompt := st.chat_input("Hỏi về bệnh lúa, thuốc trừ, kinh nghiệm phun thuốc..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # GỌI GEMINI
        with st.spinner("Gemini đang trả lời..."):
            system_prompt = f"""Bạn là chuyên gia nông nghiệp Việt Nam, chuyên sâu về bệnh lúa và cây trồng.
Trả lời ngắn gọn, thực tế, dễ hiểu cho nông dân. Tập trung vào:
- Tên bệnh, triệu chứng
- Thuốc trừ bệnh cụ thể (tên thương mại + hoạt chất)
- Cách phòng bệnh, thời điểm phun
- Kinh nghiệm thực tế

Câu hỏi của nông dân: {prompt}"""
            
            try:
                response = model.generate_content(system_prompt)
                reply = response.text
            except Exception as e:
                reply = f"⚠️ Lỗi kết nối Gemini: {str(e)}. Vui lòng kiểm tra API key hoặc thử lại."
        
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)

# TAB 3: LỊCH SỬ
with tab3:
    st.subheader("📋 Lịch sử chẩn đoán trong ngày")
    if st.session_state.history:
        for h in reversed(st.session_state.history):
            st.write(f"⏰ {h['time']} - Phát hiện: **{h['benh']}** ({h['conf']:.1f}%)")
    else:
        st.write("Chưa có lượt khám nào.")
