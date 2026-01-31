import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image
import numpy as np
import cv2
from datetime import datetime
from gtts import gTTS
import io
from fpdf import FPDF
import time
import requests
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Hệ thống Bác Sĩ Lúa AI 4.0", page_icon="🌾", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f4fdf4; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 8px solid #2e7d32; }
    h1 { color: #1b5e20; font-family: 'Helvetica Neue', sans-serif; }
</style>
""", unsafe_allow_html=True)

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "🌾 Chào bà con!"}]
if 'history' not in st.session_state:
    st.session_state['history'] = []

DATA_BENH = {
    "Bacterial Leaf Blight": {
        "ten": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "trieu_chung": "Vết bệnh lan dọc mép lá từ chóp xuống, màu vàng hoặc trắng xám.",
        "nguyen_nhan": "Vi khuẩn Xanthomonas oryzae. Thừa đạm, mưa bão.",
        "thuoc": ["Starner 20WP", "Xanthomix 20WP", "Totan 200WP"],
        "loi_khuyen": "Ngưng bón đạm, bón Kali. Rút nước ruộng.",
        "icon": "🦠"
    },
    "Blast": {
        "ten": "BỆNH ĐẠO ÔN",
        "trieu_chung": "Vết bệnh hình mắt én, tâm xám, viền nâu đậm.",
        "nguyen_nhan": "Nấm Pyricularia oryzae. Độ ẩm cao, sương mù.",
        "thuoc": ["Beam 75WP", "Fuji-one 40EC", "Flash 75WP"],
        "loi_khuyen": "Giữ nước ruộng ổn định.",
        "icon": "🔥"
    },
    "Brown Spot": {
        "ten": "BỆNH ĐỐM NÂU",
        "trieu_chung": "Vết tròn màu nâu như hạt mè.",
        "nguyen_nhan": "Nấm. Thiếu dinh dưỡng, đất phèn.",
        "thuoc": ["Tilt Super 300EC", "Anvil 5SC"],
        "loi_khuyen": "Bón cân đối N-P-K, bổ sung vôi.",
        "icon": "🍂"
    }
}
DATA_BENH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"}
})

def lay_thoi_tiet(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain&timezone=auto"
        response = requests.get(url, timeout=5).json()
        return response.get('current')
    except: return None

def xuat_pdf_don_thuoc(info, confidence):
    """Fix UTF-8: Dùng ASCII thay vì tiếng Việt có dấu"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="PHIEU CHAN DOAN LUA AI 4.0", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(0, 10, txt=f"Ngay: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
    pdf.cell(0, 10, txt=f"Benh: {info['ten']}", ln=1)
    pdf.cell(0, 10, txt=f"Do chinh xac: {confidence:.1f}%", ln=1)
    pdf.multi_cell(0, 10, txt=f"Thuoc: {', '.join(info['thuoc'])}")
    pdf.multi_cell(0, 10, txt=f"Loi khuyen: {info.get('loi_khuyen','')}")
    return pdf.output(dest='S').encode('latin-1', 'replace')  # Thay 'ignore' -> 'replace' an toàn hơn

st.markdown("<h1>🌾 BÁC SĨ LÚA AI 4.0</h1>", unsafe_allow_html=True)
st.caption("Chẩn đoán bệnh lúa qua hình ảnh với AI")

st.markdown("### 🌤️ Thời Tiết")
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
            if weather['rain'] > 0: st.error("⚠️ Đang mưa!")
            elif weather['relative_humidity_2m'] > 85: st.warning("🔥 Ẩm cao!")
            else: st.success("🌤️ Thời tiết tốt")
else:
    st.info("📍 Cho phép truy cập vị trí để xem thời tiết")

st.markdown("---")

tab_chinh, tab_chat, tab_nhat_ky = st.tabs(["🔍 CHẨN ĐOÁN", "💬 TRỢ LÝ AI", "📋 LỊCH SỬ"])

with tab_chinh:
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        st.subheader("1. Chụp/Tải ảnh lá lúa")
        input_type = st.radio("Nguồn:", ["Tải ảnh", "Chụp Camera"], horizontal=True)
        file = st.camera_input("Chụp") if input_type == "Chụp Camera" else st.file_uploader("Chọn ảnh", type=['jpg','png','jpeg'])

    if file:
        img = Image.open(file)
        with col_l:
            st.image(img, use_column_width=True, caption="Ảnh đầu vào")
            if st.button("🚀 CHẨN ĐOÁN", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("AI đang phân tích..."):
                        img.save("process.jpg")
                        client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key="8tf2UvcnEv8h80bV2G0Q")
                        res = client.infer("process.jpg", model_id="rice-leaf-disease-twtlz/1")
                        preds = res.get('predictions', [])
                        
                        if isinstance(preds, dict): 
                            preds = [{"class": k, "confidence": v['confidence']} for k, v in preds.items()]

                        if preds:
                            # HIỂN THỊ TOP 3 VỚI % CONFIDENCE
                            top3 = sorted(preds, key=lambda x: x['confidence'], reverse=True)[:3]
                            st.subheader("📊 Kết quả AI (Roboflow)")
                            col1, col2, col3 = st.columns(3)
                            for i, pred in enumerate(top3):
                                with [col1, col2, col3][i]:
                                    emoji = "🟢" if i==0 else "🟡" if i==1 else "🟠"
                                    st.metric(f"{emoji} {pred['class']}", f"{pred['confidence']*100:.1f}%")
                            
                            top = top3[0]
                            benh = DATA_BENH.get(top['class'])
                            if benh and "ref" in benh: benh = DATA_BENH.get(benh["ref"])
                            
                            if benh:
                                st.markdown(f"### ✅ Kết luận: {benh['ten']} ({top['confidence']*100:.1f}%)")
                                st.markdown(f"""
                                <div class="report-card">
                                    <p><b>🧐 Triệu chứng:</b> {benh.get('trieu_chung','N/A')}</p>
                                    <p><b>🌪️ Nguyên nhân:</b> {benh.get('nguyen_nhan','N/A')}</p>
                                    <p style="color: #d32f2f;"><b>💊 Thuốc:</b> {', '.join(benh['thuoc'])}</p>
                                    <p><b>💡 Khuyến cáo:</b> {benh.get('loi_khuyen','')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Voice
                                txt = f"Lúa bị {benh['ten']}. Dùng thuốc {benh['thuoc'][0]}."
                                gTTS(txt, lang='vi').save("voice.mp3")
                                st.audio("voice.mp3")
                                
                                # Lưu lịch sử
                                st.session_state.history.append({
                                    "time": datetime.now().strftime("%H:%M"), 
                                    "benh": benh['ten'],
                                    "conf": top['confidence']*100
                                })
                                
                                # PDF (fix UTF-8)
                                pdf_data = xuat_pdf_don_thuoc(benh, top['confidence']*100)
                                st.download_button("📥 Tải PDF", pdf_data, f"KQ_{top['class']}.pdf")
                        else:
                            st.success("🌿 Cây lúa khỏe mạnh!")

with tab_chat:
    st.subheader("💬 Hỏi đáp AI")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if p := st.chat_input("Hỏi về bệnh lúa..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        reply = "Bà con hỏi tên bệnh cụ thể để tư vấn thuốc nhé!"
        if "đạo ôn" in p.lower(): reply = "Đạo ôn dùng Beam 75WP hoặc Fuji-one. Giữ nước ruộng."
        elif "bạc lá" in p.lower(): reply = "Bạc lá ngưng đạm, phun Starner 20WP ngay."
        
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"): st.write(reply)

with tab_nhat_ky:
    st.subheader("📋 Lịch sử chẩn đoán")
    if st.session_state.history:
        for h in reversed(st.session_state.history):
            st.write(f"⏰ {h['time']} - **{h['benh']}** ({h['conf']:.1f}%)")
    else:
        st.write("Chưa có lượt khám.")
