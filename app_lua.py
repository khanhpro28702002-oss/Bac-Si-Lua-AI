import streamlit as st
import google.generativeai as genai
from inference_sdk import InferenceHTTPClient
from PIL import Image
import os

# ==========================================
# CẤU HÌNH GOOGLE GEMINI (MIỄN PHÍ)
# ==========================================
GEMINI_API_KEY = "AIzaSyAwUoUd1VFGAxHEH1EGOdp44WnbWVJYW_8"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def goi_chuyen_gia_gemini(user_input):
    """Gọi Google Gemini - Miễn phí, thông minh, nhanh"""
    try:
        prompt = f"""Bạn là chuyên gia nông nghiệp Việt Nam với 20 năm kinh nghiệm. 
        Hãy trả lời câu hỏi sau một cách chi tiết, thực tế và dễ hiểu:
        
        {user_input}
        
        Trả lời bằng tiếng Việt, ngắn gọn nhưng đầy đủ thông tin."""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Xin lỗi, có lỗi xảy ra: {str(e)}"

# ==========================================
# GIAO DIỆN
# ==========================================
st.set_page_config(page_title="Bác Sĩ Lúa AI Pro", layout="wide")
st.markdown("<h1 style='color: #2e7d32;'>🌾 BÁC SĨ LÚA AI: GEMINI EDITION</h1>", unsafe_allow_html=True)
st.info("✨ Sử dụng Google Gemini - AI thông minh nhất hiện nay")

tab1, tab2 = st.tabs(["📸 CHẨN ĐOÁN ẢNH", "💬 CHUYÊN GIA AI"])

# TAB CHẨN ĐOÁN
with tab1:
    f = st.file_uploader("Chọn ảnh lá lúa", type=['jpg','png','jpeg'])
    if f:
        img = Image.open(f)
        st.image(img, use_column_width=True)
        if st.button("🔍 PHÂN TÍCH", type="primary"):
            with st.spinner("Đang phân tích..."):
                try:
                    img.save("temp.jpg")
                    client = InferenceHTTPClient(
                        api_url="https://detect.roboflow.com",
                        api_key="8tf2UvcnEv8h80bV2G0Q"
                    )
                    res = client.infer("temp.jpg", model_id="rice-leaf-disease-twtlz/1")
                    preds = res.get('predictions', [])
                    
                    if preds:
                        benh = preds[0]['class']
                        st.error(f"⚠️ Phát hiện: **{benh}**")
                        
                        # Dùng Gemini để tư vấn
                        advice = goi_chuyen_gia_gemini(
                            f"Cây lúa bị bệnh {benh}. Hãy cho biết:\n"
                            f"1. Tên tiếng Việt của bệnh\n"
                            f"2. Nguyên nhân\n"
                            f"3. Thuốc điều trị cụ thể (tên thương mại)\n"
                            f"4. Cách phòng ngừa"
                        )
                        st.success("**Tư vấn từ chuyên gia AI:**")
                        st.write(advice)
                    else:
                        st.success("✅ Cây lúa khỏe mạnh!")
                    
                    if os.path.exists("temp.jpg"):
                        os.remove("temp.jpg")
                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")

# TAB CHATBOT
with tab2:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    if query := st.chat_input("Hỏi về trồng lúa, bệnh hại, dinh dưỡng..."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)
        
        with st.chat_message("assistant"):
            with st.spinner("Đang suy nghĩ..."):
                response = goi_chuyen_gia_gemini(query)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
