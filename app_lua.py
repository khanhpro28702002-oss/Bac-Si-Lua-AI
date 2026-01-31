import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image
import numpy as np
import cv2
from datetime import datetime
from gtts import gTTS
import io
from fpdf import FPDF
import requests
from streamlit_js_eval import get_geolocation
import google.generativeai as genai

# ==============================================================================
# 1. CẤU HÌNH HỆ THỐNG & AI BRAIN (GEMINI)
# ==============================================================================

# THAY MÃ API KEY CỦA BẠN VÀO ĐÂY
API_KEY_GEMINI = "AIzaSyBFYtJFvAAiR3DqqcNtw1-3gHHe2g-2eXA"

# Cấu hình "Nhân cách" cho Trợ lý AI
genai.configure(api_key=API_KEY_GEMINI)
model_gemini = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "Bạn là Chuyên gia Nông nghiệp Việt Nam với 30 năm kinh nghiệm về lúa gạo. "
        "Hãy dùng giọng văn gần gũi, chân chất của người miền Tây hoặc miền Bắc để tư vấn cho bà con. "
        "Kiến thức của bạn bao gồm: kỹ thuật canh tác, nhận biết sâu bệnh, cách dùng thuốc BVTV an toàn, "
        "và quản lý nước ruộng. Nếu bà con hỏi về bệnh lúa, hãy tư vấn chi tiết phác đồ điều trị."
    )
)

# Cấu hình Roboflow (Thị giác máy tính)
ROBO_API_KEY = "8tf2UvcnEv8h80bV2G0Q"
MODEL_ID = "rice-leaf-disease-twtlz/1"

st.set_page_config(page_title="Bác Sĩ Lúa AI Pro", page_icon="🌾", layout="wide")

# Khởi tạo bộ nhớ Chat
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# ==============================================================================
# 2. CÁC HÀM XỬ LÝ (HÀM CON)
# ==============================================================================

def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain&timezone=auto"
        return requests.get(url, timeout=5).json().get('current')
    except: return None

def create_pdf(info_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="PHIEU KET QUA TU VAN NONG NGHIEP", ln=1, align='C')
    pdf.ln(10)
    pdf.multi_cell(0, 10, txt=info_text.encode('latin-1', 'ignore').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# ==============================================================================
# 3. GIAO DIỆN NGƯỜI DÙNG (UI)
# ==============================================================================

st.markdown("<h1 style='color: #1b5e20;'>🌾 BÁC SĨ LÚA AI: SIÊU TRỢ LÝ 4.0</h1>", unsafe_allow_html=True)

# --- PHẦN THỜI TIẾT ---
st.subheader("🌦️ Thời Tiết Nông Vụ")
loc = get_geolocation()
if loc and 'coords' in loc:
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    w = get_weather(lat, lon)
    if w:
        c1, c2, c3 = st.columns(3)
        c1.metric("🌡️ Nhiệt độ", f"{w['temperature_2m']}°C")
        c2.metric("💧 Độ ẩm", f"{w['relative_humidity_2m']}%")
        c3.metric("🌧️ Lượng mưa", f"{w['rain']} mm")
        if w['rain'] > 0: st.error("☔ Đang có mưa: Bà con tạm ngưng phun thuốc!")
else:
    st.info("📍 Đang chờ vị trí GPS để dự báo thời tiết tại ruộng...")

st.markdown("---")

# --- TAB CHỨC NĂNG ---
tab_camera, tab_chat = st.tabs(["📸 CHẨN ĐOÁN HÌNH ẢNH", "💬 HỎI ĐÁP CHUYÊN GIA AI"])

# --- TAB 1: CAMERA AI ---
with tab_camera:
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        mode = st.radio("Chọn nguồn ảnh:", ["Tải lên", "Chụp trực tiếp"], horizontal=True)
        input_file = st.camera_input("Chụp lá lúa") if mode == "Chụp trực tiếp" else st.file_uploader("Chọn ảnh", type=['jpg','png'])

    if input_file:
        img = Image.open(input_file)
        with col_l:
            st.image(img, use_column_width=True)
            if st.button("🔍 PHÂN TÍCH MẪU BỆNH", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("AI đang soi bệnh..."):
                        img.save("temp.jpg")
                        client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key=ROBO_API_KEY)
                        res = client.infer("temp.jpg", model_id=MODEL_ID)
                        preds = res.get('predictions', [])
                        
                        if preds:
                            # Nếu có bệnh, dùng Gemini để giải thích chi tiết
                            top_label = preds[0]['class'] if isinstance(preds, list) else list(preds.keys())[0]
                            st.warning(f"⚠️ Phát hiện dấu hiệu: {top_label}")
                            
                            # Dùng "Não bộ" Gemini để tư vấn chi tiết về bệnh này
                            prompt_advice = f"Lá lúa có dấu hiệu bệnh {top_label}. Hãy cho biết tên tiếng Việt, triệu chứng chi tiết, nguyên nhân và danh sách các loại thuốc BVTV đặc trị tại Việt Nam kèm cách dùng."
                            advice = model_gemini.generate_content(prompt_advice).text
                            
                            st.markdown("### 📋 Tư vấn từ Chuyên gia:")
                            st.write(advice)
                            
                            # Giọng nói
                            gTTS(f"Phát hiện bệnh {top_label}. Bà con xem hướng dẫn điều trị bên dưới.", lang='vi').save("v.mp3")
                            st.audio("v.mp3")
                            
                            # PDF
                            st.download_button("📥 Tải hướng dẫn điều trị (PDF)", create_pdf(advice), "Tu_van_lua.pdf")
                        else:
                            st.success("✅ Cây lúa khỏe mạnh! Tiếp tục theo dõi bà con nhé.")

# --- TAB 2: CHATBOT THÔNG MINH (GEMINI) ---
with tab_chat:
    st.subheader("💬 Trò chuyện cùng Chuyên gia Nông nghiệp")
    st.caption("Bà con có thể hỏi bất cứ điều gì: kỹ thuật bón phân, cách trị rầy nâu, giống lúa ST25...")

    # Hiển thị lịch sử chat
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.write(m["content"])

    # Nhập câu hỏi
    if user_p := st.chat_input("Nhập câu hỏi tại đây..."):
        st.session_state.chat_history.append({"role": "user", "content": user_p})
        with st.chat_message("user"): st.write(user_p)
        
        with st.chat_message("assistant"):
            with st.spinner("Chuyên gia đang suy nghĩ..."):
                try:
                    # Gửi câu hỏi cho Gemini
                    response = model_gemini.generate_content(user_p)
                    full_reply = response.text
                    st.write(full_reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": full_reply})
                except Exception as e:
                    st.error("Dạ, mạng hơi yếu bà con đợi xíu ạ!")
import streamlit as st
import google.generativeai as genai
from inference_sdk import InferenceHTTPClient
from PIL import Image
import requests
from streamlit_js_eval import get_geolocation

# --- CẤU HÌNH ---
# DÁN API KEY CỦA BẠN VÀO ĐÂY
GEMINI_KEY = "AIzaSyBFYtJFvAAiR3DqqcNtw1-3gHHe2g-2eXA"

# Khởi tạo Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Bác Sĩ Lúa Pro", layout="wide")

# Kiểm tra GPS an toàn để không bị KeyError
st.subheader("🌦️ Thời Tiết Tại Ruộng")
loc = get_geolocation()
if loc and 'coords' in loc:
    lat = loc['coords'].get('latitude')
    lon = loc['coords'].get('longitude')
    if lat and lon:
        st.success(f"📍 Đã xác định vị trí: {lat}, {lon}")
        # (Phần gọi API thời tiết ở đây...)
else:
    st.info("📌 Bà con vui lòng bấm 'Cho phép' truy cập vị trí để xem thời tiết nhé.")

st.markdown("---")

# --- PHẦN CHAT THÔNG MINH ---
st.subheader("💬 Trò chuyện cùng Chuyên gia AI")
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]): st.write(m["content"])

if p := st.chat_input("Hỏi gì đi bà con..."):
    st.session_state.chat_history.append({"role": "user", "content": p})
    with st.chat_message("user"): st.write(p)
    
    with st.chat_message("assistant"):
        try:
            # Đây là nơi gọi bộ não Gemini thực sự
            response = model.generate_content(p)
            st.write(response.text)
            st.session_state.chat_history.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Lỗi kết nối AI: {e}")