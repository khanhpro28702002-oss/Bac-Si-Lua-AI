import streamlit as st
import google.generativeai as genai
from inference_sdk import InferenceHTTPClient
from PIL import Image
import requests
from streamlit_js_eval import get_geolocation
from gtts import gTTS
from fpdf import FPDF
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG & AI
# ==========================================

# DÁN MÃ API KEY GEMINI CỦA BẠN VÀO ĐÂY
API_KEY_GEMINI = "DÁN_MÃ_API_KEY_CỦA_BẠN_VÀO_ĐÂY"

# Cấu hình bộ não Gemini (AI Chat)
if API_KEY_GEMINI != "AIzaSyBFYtJFvAAiR3DqqcNtw1-3gHHe2g-2eXA":
    genai.configure(api_key=API_KEY_GEMINI)
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
else:
    model_ai = None

# Cấu hình Roboflow (AI Vision) từ dữ liệu của bạn
ROBO_KEY = "8tf2UvcnEv8h80bV2G0Q"
MODEL_ID = "rice-leaf-disease-twtlz/1"

st.set_page_config(page_title="Bác Sĩ Lúa AI Pro", layout="wide", page_icon="🌾")

# ==========================================
# 2. GIAO DIỆN & THỜI TIẾT GPS
# ==========================================

st.markdown("<h1 style='color: #1b5e20;'>🌾 BÁC SĨ LÚA AI: SIÊU TRỢ LÝ NÔNG NGHIỆP</h1>", unsafe_allow_html=True)
st.caption("Công nghệ AI 4.0: Chẩn đoán Hình ảnh - Tư vấn Thuốc - Cảnh báo Thời tiết")

# Xử lý GPS an toàn để chống lỗi KeyError
st.subheader("🌦️ Thời Tiết Nông Vụ Tại Chỗ")
location = get_geolocation(key='gps_ultimate_fix')

if location and 'coords' in location:
    try:
        lat = location['coords'].get('latitude')
        lon = location['coords'].get('longitude')
        if lat and lon:
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m&timezone=auto"
            weather = requests.get(w_url).json()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🌡️ Nhiệt độ", f"{weather['current']['temperature_2m']}°C")
            c2.metric("💧 Độ ẩm", f"{weather['current']['relative_humidity_2m']}%")
            with c3:
                st.success(f"📍 Vị trí: {round(lat,2)}, {round(lon,2)}")
    except:
        st.write("Đang tải dữ liệu thời tiết...")
else:
    # Thông báo thay vì báo lỗi đỏ
    st.info("📍 Đang chờ GPS... Bà con hãy bấm 'Cho phép' (Allow) trên trình duyệt để xem thời tiết tại ruộng nhé.")

st.markdown("---")

# ==========================================
# 3. CÁC TAB CHỨC NĂNG CHÍNH
# ==========================================

tab1, tab2 = st.tabs(["📸 CHẨN ĐOÁN BỆNH QUA ẢNH", "💬 HỎI ĐÁP CHUYÊN GIA AI"])

# --- TAB 1: AI CHẨN ĐOÁN ---
with tab1:
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        st.write("### 1. Thu thập hình ảnh")
        src = st.radio("Chọn nguồn ảnh:", ["Tải ảnh lên", "Chụp bằng Camera"], horizontal=True)
        img_file = st.camera_input("Chụp mẫu lá") if src == "Chụp bằng Camera" else st.file_uploader("Chọn ảnh từ máy", type=['jpg','png','jpeg'])

    if img_file:
        img_input = Image.open(img_file)
        with col_l:
            st.image(img_input, use_column_width=True, caption="Ảnh mẫu đang soi")
            if st.button("🔍 BẮT ĐẦU PHÂN TÍCH", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("AI đang soi kính hiển vi..."):
                        try:
                            img_input.save("process.jpg")
                            client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key=ROBO_KEY)
                            result = client.infer("process.jpg", model_id=MODEL_ID)
                            preds = result.get('predictions', [])
                            
                            if isinstance(preds, dict):
                                preds = [{"class": k, "confidence": v['confidence']} for k, v in preds.items()]

                            if preds:
                                top_benh = max(preds, key=lambda x: x['confidence'])['class']
                                st.error(f"### 🚩 CẢNH BÁO: PHÁT HIỆN {top_benh.upper()}")
                                
                                if model_ai:
                                    # Gemini tư vấn chi tiết
                                    prompt = f"Lá lúa bị bệnh {top_benh}. Hãy cho biết tên tiếng Việt, triệu chứng và các loại thuốc đặc trị phổ biến tại Việt Nam."
                                    advice = model_ai.generate_content(prompt).text
                                    st.markdown("#### 📖 Hướng dẫn điều trị:")
                                    st.write(advice)
                                    
                                    # Tạo giọng nói
                                    gTTS(f"Phát hiện bệnh {top_benh}. Bà con xem hướng dẫn điều trị bên dưới.", lang='vi').save("v.mp3")
                                    st.audio("v.mp3")
                                else:
                                    st.warning("Bạn chưa dán Gemini API Key để nhận tư vấn chi tiết.")
                            else:
                                st.success("✅ Cây lúa khỏe mạnh, không phát hiện sâu bệnh!")
                                st.balloons()
                        except Exception as e:
                            st.error(f"Lỗi phân tích: {e}")

# --- TAB 2: CHATBOT THÔNG MINH ---
with tab2:
    st.write("### 💬 Trò chuyện cùng Chuyên gia AI")
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if query := st.chat_input("Hỏi tôi về kỹ thuật lúa gạo..."):
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.chat_message("user"): st.write(query)
        
        with st.chat_message("assistant"):
            if model_ai:
                try:
                    response = model_ai.generate_content(query)
                    reply = response.text
                    st.write(reply)
                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                except:
                    # Chống thông báo mạng yếu sai lệch
                    st.error("Dạ, bộ não AI đang bận tí, bà con thử lại sau nhé!")
            else:
                st.warning("Vui lòng dán Gemini API Key vào code để bắt đầu trò chuyện.")
import streamlit as st
import google.generativeai as genai
from inference_sdk import InferenceHTTPClient
from PIL import Image
import requests
from streamlit_js_eval import get_geolocation
from gtts import gTTS
from fpdf import FPDF
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH HỆ THỐNG & AI
# ==========================================

# THAY MÃ API KEY GEMINI CỦA BẠN VÀO ĐÂY
API_KEY_GEMINI = "AIzaSyBFYtJFvAAiR3DqqcNtw1-3gHHe2g-2eXA"

# Cấu hình bộ não Gemini (AI Chat) an toàn
if API_KEY_GEMINI != "AIzaSyBFYtJFvAAiR3DqqcNtw1-3gHHe2g-2eXA":
    try:
        genai.configure(api_key=API_KEY_GEMINI)
        model_ai = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model_ai = None
else:
    model_ai = None

# Cấu hình Roboflow (AI Vision)
ROBO_KEY = "8tf2UvcnEv8h80bV2G0Q"
MODEL_ID = "rice-leaf-disease-twtlz/1"

st.set_page_config(page_title="Bác Sĩ Lúa AI Pro", layout="wide", page_icon="🌾")

# ==========================================
# 2. GIAO DIỆN & XỬ LÝ GPS AN TOÀN
# ==========================================

st.markdown("<h1 style='color: #1b5e20;'>🌾 BÁC SĨ LÚA AI: SIÊU TRỢ LÝ NÔNG NGHIỆP</h1>", unsafe_allow_html=True)

# Chống lỗi DuplicateElementKey bằng cách dùng key duy nhất
location = get_geolocation(key='gps_final_fix_2026')

st.subheader("🌦️ Thời Tiết Nông Vụ Tại Chỗ")

# Chống lỗi KeyError bằng cách kiểm tra dữ liệu trước khi truy cập
if location and 'coords' in location:
    try:
        lat = location['coords'].get('latitude')
        lon = location['coords'].get('longitude')
        if lat and lon:
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m&timezone=auto"
            weather = requests.get(w_url).json()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🌡️ Nhiệt độ", f"{weather['current']['temperature_2m']}°C")
            c2.metric("💧 Độ ẩm", f"{weather['current']['relative_humidity_2m']}%")
            with c3:
                st.success(f"📍 Vị trí: {round(lat,2)}, {round(lon,2)}")
    except:
        st.write("Đang kết nối trạm khí tượng...")
else:
    # Thông báo hướng dẫn thay vì báo lỗi đỏ
    st.info("📍 Đang chờ GPS... Bà con hãy bấm 'Cho phép' (Allow) trên trình duyệt để xem thời tiết nhé.")

st.markdown("---")

# ==========================================
# 3. CÁC TAB CHỨC NĂNG CHÍNH
# ==========================================

tab1, tab2 = st.tabs(["📸 CHẨN ĐOÁN QUA ẢNH", "💬 HỎI ĐÁP CHUYÊN GIA AI"])

# --- TAB 1: AI CHẨN ĐOÁN ---
with tab1:
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        st.write("### 1. Thu thập hình ảnh")
        src = st.radio("Chọn nguồn ảnh:", ["Tải ảnh lên", "Chụp bằng Camera"], horizontal=True)
        img_file = st.camera_input("Chụp mẫu lá") if src == "Chụp bằng Camera" else st.file_uploader("Chọn ảnh từ máy", type=['jpg','png','jpeg'])

    if img_file:
        img_input = Image.open(img_file)
        with col_l:
            st.image(img_input, use_column_width=True)
            if st.button("🔍 BẮT ĐẦU PHÂN TÍCH", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("AI đang soi bệnh..."):
                        try:
                            img_input.save("process.jpg")
                            client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key=ROBO_KEY)
                            result = client.infer("process.jpg", model_id=MODEL_ID)
                            preds = result.get('predictions', [])
                            
                            if isinstance(preds, dict):
                                preds = [{"class": k, "confidence": v['confidence']} for k, v in preds.items()]

                            if preds:
                                top_benh = max(preds, key=lambda x: x['confidence'])['class']
                                st.error(f"### 🚩 PHÁT HIỆN: {top_benh.upper()}")
                                
                                if model_ai:
                                    prompt = f"Lá lúa bị bệnh {top_benh}. Hãy cho biết tên tiếng Việt, triệu chứng và các loại thuốc đặc trị phổ biến tại Việt Nam."
                                    advice = model_ai.generate_content(prompt).text
                                    st.markdown("#### 📖 Tư vấn điều trị:")
                                    st.write(advice)
                                    
                                    gTTS(f"Phát hiện bệnh {top_benh}.", lang='vi').save("v.mp3")
                                    st.audio("v.mp3")
                                else:
                                    st.warning("Vui lòng dán Gemini API Key để nhận tư vấn chi tiết.")
                            else:
                                st.success("✅ Cây lúa khỏe mạnh!")
                        except Exception as e:
                            st.error(f"Lỗi: {e}")

# --- TAB 2: CHATBOT THÔNG MINH ---
with tab_chat:
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if query := st.chat_input("Hỏi tôi về kỹ thuật lúa gạo..."):
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.chat_message("user"): st.write(query)
        
        with st.chat_message("assistant"):
            if model_ai:
                try:
                    response = model_ai.generate_content(query)
                    st.write(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except:
                    st.error("Dạ, bộ não AI đang bận tí, bà con thử lại sau nhé!")
            else:
                st.warning("Vui lòng dán Gemini API Key vào code.")