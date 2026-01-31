import streamlit as st
import google.generativeai as genai
from inference_sdk import InferenceHTTPClient
from PIL import Image
import requests
from streamlit_js_eval import get_geolocation

# ==========================================
# 1. CẤU HÌNH BỘ NÃO AI (GEMINI)
# ==========================================
# DÁN MÃ API KEY CỦA BẠN VÀO GIỮA DẤU NGOẶC KÉP DƯỚI ĐÂY
API_KEY_GEMINI = "DÁN_MÃ_API_KEY_CỦA_BẠN_VÀO_ĐÂY"

if API_KEY_GEMINI != "DÁN_MÃ_API_AIzaSyBFYtJFvAAiR3DqqcNtw1-3gHHe2g-2eXA":
    try:
        genai.configure(api_key=API_KEY_GEMINI)
        model_ai = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model_ai = None
else:
    model_ai = None

st.set_page_config(page_title="Bác Sĩ Lúa AI Pro", layout="wide")

# ==========================================
# 2. XỬ LÝ GIAO DIỆN & THỜI TIẾT AN TOÀN
# ==========================================
st.markdown("<h1 style='color: #1b5e20;'>🌾 BÁC SĨ LÚA AI: SIÊU TRỢ LÝ</h1>", unsafe_allow_html=True)

# Khắc phục lỗi DuplicateElementKey & TypeError: Gọi hàm đơn giản nhất
location = get_geolocation()

st.subheader("🌦️ Thời Tiết Nông Vụ")

# Khắc phục lỗi KeyError: Kiểm tra từng tầng dữ liệu trước khi dùng
if location and 'coords' in location:
    lat = location['coords'].get('latitude')
    lon = location['coords'].get('longitude')
    if lat and lon:
        try:
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m&timezone=auto"
            res = requests.get(w_url, timeout=5).json()
            st.success(f"📍 Vị trí: {round(lat,2)}, {round(lon,2)}")
            st.metric("🌡️ Nhiệt độ hiện tại", f"{res['current']['temperature_2m']}°C")
        except:
            st.write("Đang kết nối trạm khí tượng...")
else:
    st.info("📍 Bà con hãy bấm 'Cho phép' (Allow) vị trí trên trình duyệt để xem thời tiết nhé.")

st.markdown("---")

# ==========================================
# 3. CÁC TAB CHỨC NĂNG
# ==========================================
tab1, tab2 = st.tabs(["📸 CHẨN ĐOÁN BỆNH", "💬 HỎI ĐÁP CHUYÊN GIA AI"])

with tab1:
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        f = st.file_uploader("Chọn ảnh lá lúa bị bệnh", type=['jpg','png','jpeg'])
        if f:
            img = Image.open(f)
            st.image(img, use_column_width=True)
            if st.button("🔍 PHÂN TÍCH", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("Đang soi bệnh..."):
                        img.save("temp.jpg")
                        # Roboflow API Key từ cấu hình của bạn
                        client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key="8tf2UvcnEv8h80bV2G0Q")
                        res = client.infer("temp.jpg", model_id="rice-leaf-disease-twtlz/1")
                        preds = res.get('predictions', [])
                        if preds:
                            ten_benh = preds[0]['class']
                            st.error(f"⚠️ Phát hiện: {ten_benh}")
                            if model_ai:
                                p = f"Lúa bị bệnh {ten_benh}. Tư vấn tên tiếng Việt và thuốc trị cụ thể."
                                st.write(model_ai.generate_content(p).text)
                        else:
                            st.success("✅ Cây lúa khỏe mạnh!")

with tab2:
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    if p := st.chat_input("Hỏi tôi về kỹ thuật lúa gạo..."):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        
        with st.chat_message("assistant"):
            if model_ai:
                try:
                    ans = model_ai.generate_content(p).text
                    st.write(ans)
                    st.session_state.chat_history.append({"role": "assistant", "content": ans})
                except:
                    st.error("Dạ, bộ não AI đang bận tí, bà con thử lại sau nhé!")
            else:
                st.warning("Vui lòng dán mã API Key của Gemini vào code để bắt đầu trò chuyện.")