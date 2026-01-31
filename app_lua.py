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

# ==========================================
# 1. THIẾT LẬP CẤU HÌNH VÀ GIAO DIỆN
# ==========================================
st.set_page_config(page_title="Hệ thống Bác Sĩ Lúa AI 4.0", page_icon="🌾", layout="wide")

# CSS để App trông "xịn" hơn
st.markdown("""
<style>
    .main { background-color: #f4fdf4; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 8px solid #2e7d32; }
    h1 { color: #1b5e20; font-family: 'Helvetica Neue', sans-serif; }
</style>
""", unsafe_allow_html=True)

# Khởi tạo bộ nhớ tạm
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "🌾 Chào bà con! Tôi là Trợ lý AI chuyên về lúa gạo. Bà con cần hỗ trợ gì về bệnh lý hay thời tiết không?"}]
if 'history' not in st.session_state:
    st.session_state['history'] = []

# ==========================================
# 2. KHO DỮ LIỆU THUỐC & KIẾN THỨC NÔNG NGHIỆP
# ==========================================
DATA_BENH = {
    "Bacterial Leaf Blight": {
        "ten": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "trieu_chung": "Vết bệnh lan dọc mép lá từ chóp xuống, màu vàng hoặc trắng xám, rìa gợn sóng.",
        "nguyen_nhan": "Vi khuẩn Xanthomonas oryzae. Thừa đạm, mưa bão làm rách lá lây lan.",
        "hoat_chat": "Bismerthiazol, Oxolinic acid, Kasugamycin.",
        "thuoc": ["Starner 20WP", "Xanthomix 20WP", "Totan 200WP", "Sasa 25WP"],
        "loi_khuyen": "Ngưng bón đạm, bón bổ sung Kali. Rút nước ruộng để hạn chế vi khuẩn.",
        "icon": "🦠"
    },
    "Blast": {
        "ten": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "trieu_chung": "Vết bệnh hình mắt én, tâm xám trắng, viền nâu đậm. Nặng có thể gây cháy cả lá.",
        "nguyen_nhan": "Nấm Pyricularia oryzae. Trời âm u, sương mù, độ ẩm cao.",
        "hoat_chat": "Tricyclazole, Isoprothiolane, Fenoxanil.",
        "thuoc": ["Beam 75WP", "Fuji-one 40EC", "Filia 525SE", "Flash 75WP"],
        "loi_khuyen": "Giữ nước ruộng ổn định. Không phun phân bón lá khi lúa đang bệnh.",
        "icon": "🔥"
    },
    "Brown Spot": {
        "ten": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "trieu_chung": "Vết bệnh tròn nhỏ màu nâu như hạt mè rải rác trên phiến lá.",
        "nguyen_nhan": "Nấm. Thường gặp ở ruộng thiếu dinh dưỡng, đất phèn, ngộ độc hữu cơ.",
        "hoat_chat": "Propiconazole, Difenoconazole.",
        "thuoc": ["Tilt Super 300EC", "Anvil 5SC", "Nevo 330EC"],
        "loi_khuyen": "Cần bón cân đối N-P-K, bổ sung vôi để cải tạo đất phèn.",
        "icon": "🍂"
    }
}
# Đăng ký các tên thay thế từ Model AI
DATA_BENH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"}, "Rice Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"},
    "Sheathblight": {"ten": "KHÔ VẰN", "thuoc": ["Validacin 5L", "Anvil 5SC"], "icon": "🍄"},
    "Hispa": {"ten": "SÂU GAI", "thuoc": ["Padan 95SP", "Reasgant 3.6EC"], "icon": "🐛"},
    "Leafscald": {"ten": "CHÁY CHÓP LÁ", "thuoc": ["Carbenzim 500FL"], "icon": "🍂"}
})

# ==========================================
# 3. CÁC MODULE CHỨC NĂNG HỆ THỐNG
# ==========================================

def lay_thoi_tiet(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain&timezone=auto"
        response = requests.get(url, timeout=5).json()
        return response.get('current')
    except: return None

def xuat_pdf_don_thuoc(info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="PHIEU KET QUA CHAN DOAN LUA 4.0", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(0, 10, txt=f"Ngay chan doan: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
    pdf.cell(0, 10, txt=f"KET LUAN: {info['ten']}", ln=1)
    if 'thuoc' in info:
        pdf.multi_cell(0, 10, txt=f"Danh sach thuoc goi y: {', '.join(info['thuoc'])}")
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# ==========================================
# 4. GIAO DIỆN CHÍNH (MAIN UI)
# ==========================================

st.markdown("<h1>🌾 BÁC SĨ LÚA AI: SIÊU TRỢ LÝ NÔNG NGHIỆP</h1>", unsafe_allow_html=True)
st.caption("Giải pháp công nghệ chẩn đoán bệnh lúa qua hình ảnh, tư vấn thuốc và thời tiết thực tế.")

# --- MODULE THỜI TIẾT GPS ---
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
            if weather['rain'] > 0: st.error("⚠️ Đang mưa: Đừng phun thuốc!")
            elif weather['relative_humidity_2m'] > 85: st.warning("🔥 Ẩm cao: Cẩn thận đạo ôn!")
            else: st.success("🌤️ Thời tiết tốt để ra thăm đồng.")
else:
    st.info("📍 Vui lòng 'Cho phép' truy cập vị trí để xem thời tiết chính xác tại ruộng của bà con.")

st.markdown("---")

# --- CHIA TAB CHỨC NĂNG ---
tab_chinh, tab_chat, tab_nhat_ky = st.tabs(["🔍 CHẨN ĐOÁN HÌNH ẢNH", "💬 TRỢ LÝ AI", "📋 NHẬT KÝ KHÁM"])

# TAB 1: CHẨN ĐOÁN
with tab_chinh:
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        st.subheader("1. Chụp ảnh/Tải ảnh lá lúa")
        input_type = st.radio("Chọn nguồn:", ["Tải ảnh từ máy", "Chụp bằng Camera"], horizontal=True)
        file = st.camera_input("Chụp ảnh") if input_type == "Chụp bằng Camera" else st.file_uploader("Chọn file ảnh", type=['jpg','png','jpeg'])

    if file:
        img = Image.open(file)
        with col_l:
            st.image(img, use_column_width=True, caption="Mẫu bệnh đầu vào")
            if st.button("🚀 BẮT ĐẦU CHẨN ĐOÁN", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("AI đang làm việc..."):
                        img.save("process.jpg")
                        client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key="8tf2UvcnEv8h80bV2G0Q")
                        res = client.infer("process.jpg", model_id="rice-leaf-disease-twtlz/1")
                        preds = res.get('predictions', [])
                        
                        if isinstance(preds, dict): preds = [{"class": k, "confidence": v['confidence']} for k, v in preds.items()]

                        if preds:
                            top = max(preds, key=lambda x: x['confidence'])
                            benh = DATA_BENH.get(top['class'])
                            if benh and "ref" in benh: benh = DATA_BENH.get(benh["ref"])
                            
                            if benh:
                                st.markdown(f"### ✅ Đã xác định: {benh['ten']}")
                                st.markdown(f"""
                                <div class="report-card">
                                    <p><b>🧐 Dấu hiệu:</b> {benh.get('trieu_chung','Chưa có dữ liệu')}</p>
                                    <p><b>🌪️ Nguyên nhân:</b> {benh.get('nguyen_nhan','Chưa có dữ liệu')}</p>
                                    <p style="color: #d32f2f;"><b>💊 Thuốc đặc trị:</b> {', '.join(benh['thuoc'])}</p>
                                    <p><b>💡 Lời khuyên:</b> {benh.get('loi_khuyen','')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Giọng nói AI
                                txt_read = f"Lúa bị {benh['ten']}. Bà con dùng thuốc {benh['thuoc'][0]}."
                                gTTS(txt_read, lang='vi').save("voice.mp3")
                                st.audio("voice.mp3")
                                
                                # Lưu lịch sử
                                st.session_state.history.append({"time": datetime.now().strftime("%H:%M"), "benh": benh['ten']})
                                
                                # Xuất PDF
                                st.download_button("📥 Tải đơn thuốc PDF", xuat_pdf_don_thuoc(benh), f"Ket_qua_{top['class']}.pdf")
                        else:
                            st.success("🌿 Cây lúa khỏe mạnh! Chúc mừng bà con.")

# TAB 2: CHATBOT AI
with tab_chat:
    st.subheader("💬 Hỏi đáp cùng chuyên gia")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if p := st.chat_input("Hỏi tôi về đạo ôn, bạc lá, thuốc trừ sâu..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        reply = "Bà con hỏi tên bệnh để tôi tư vấn thuốc nhé!"
        if "đạo ôn" in p.lower(): reply = "Đạo ôn bà con dùng Beam hoặc Fuji-one nhé. Nhớ giữ nước ruộng."
        elif "bạc lá" in p.lower(): reply = "Bạc lá bà con ngưng bón đạm, phun Starner ngay."
        
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"): st.write(reply)

# TAB 3: NHẬT KÝ
with tab_nhat_ky:
    st.subheader("📋 Lịch sử chẩn đoán trong ngày")
    if st.session_state.history:
        for h in reversed(st.session_state.history):
            st.write(f"⏰ {h['time']} - Phát hiện: **{h['benh']}**")
    else:
        st.write("Chưa có lượt khám nào.")