import streamlit as st
import requests
from inference_sdk import InferenceHTTPClient
from PIL import Image
import os

# ==========================================
# 1. CẤU HÌNH HUGGING FACE (BỘ NÃO AI)
# ==========================================
# DÁN MÃ TOKEN CỦA BẠN VÀO GIỮA DẤU NGOẶC KÉP
HF_TOKEN = "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"  # ⚠️ QUAN TRỌNG: Thay token mới sau khi revoke token cũ
# Mô hình Qwen2.5 hỗ trợ tiếng Việt rất tốt
MODEL_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"

def goi_chuyen_gia_hf(user_input):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    # Cấu hình lời nhắc (Prompt) để AI đóng vai chuyên gia
    system_prompt = f"<|im_start|>system\nBạn là chuyên gia nông nghiệp Việt Nam. Hãy tư vấn cho nông dân ngắn gọn, dễ hiểu.<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n<|im_start|>assistant\n"
    
    payload = {
        "inputs": system_prompt,
        "parameters": {"max_new_tokens": 512, "temperature": 0.7}
    }
    
    try:
        response = requests.post(MODEL_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        result = response.json()
        # Xử lý văn bản trả về
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get('generated_text', '')
            return text.split("<|im_start|>assistant\n")[-1].strip()
        else:
            return "Không nhận được phản hồi từ AI. Vui lòng thử lại."
    except Exception as e:
        return f"Dạ, chuyên gia AI đang bận tí (Lỗi: {str(e)}). Bà con thử lại sau nhé!"

# ==========================================
# 2. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="Bác Sĩ Lúa AI Pro", layout="wide")
st.markdown("<h1 style='color: #2e7d32;'>🌾 BÁC SĨ LÚA AI: HUGGING FACE EDITION</h1>", unsafe_allow_html=True)

# ✅ SỬA LỖI: Loại bỏ get_geolocation() để tránh lỗi
# Nếu muốn GPS, cài: pip install streamlit-js-eval
# Nhưng để đơn giản, tôi tắt tính năng này
st.info("📌 Ứng dụng chẩn đoán bệnh lúa và tư vấn nông nghiệp")

st.markdown("---")
tab1, tab2 = st.tabs(["📸 CHẨN ĐOÁN ẢNH", "💬 CHUYÊN GIA AI"])

# --- TAB CHẨN ĐOÁN (Sử dụng Roboflow) ---
with tab1:
    f = st.file_uploader("Chọn ảnh lá lúa bị bệnh", type=['jpg','png','jpeg'])
    if f:
        img = Image.open(f)
        st.image(img, use_column_width=True)
        if st.button("🔍 PHÂN TÍCH BỆNH", type="primary"):
            with st.spinner("Đang soi bệnh..."):
                try:
                    # Lưu ảnh tạm
                    img.save("temp.jpg")
                    # Roboflow API
                    client = InferenceHTTPClient(
                        api_url="https://detect.roboflow.com", 
                        api_key="8tf2UvcnEv8h80bV2G0Q"
                    )
                    res = client.infer("temp.jpg", model_id="rice-leaf-disease-twtlz/1")
                    preds = res.get('predictions', [])
                    
                    if preds:
                        benh = preds[0]['class']
                        confidence = preds[0].get('confidence', 0) * 100
                        st.error(f"⚠️ Phát hiện: **{benh}** (Độ tin cậy: {confidence:.1f}%)")
                        
                        # Dùng Hugging Face để tư vấn phác đồ
                        st.write("🤖 **Tư vấn từ AI:**")
                        advice = goi_chuyen_gia_hf(f"Lúa bị bệnh {benh}. Hãy cho biết tên tiếng Việt và thuốc đặc trị cụ thể.")
                        st.write(advice)
                    else:
                        st.success("✅ Cây lúa khỏe mạnh!")
                    
                    # Xóa file tạm
                    if os.path.exists("temp.jpg"):
                        os.remove("temp.jpg")
                        
                except Exception as e:
                    st.error(f"Lỗi phân tích: {str(e)}")

# --- TAB CHATBOT AI ---
with tab2:
    st.write("💡 **Hỏi bất kỳ câu hỏi nào về trồng lúa, chăm sóc cây, dinh dưỡng...**")
    
    # Khởi tạo lịch sử chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Hiển thị lịch sử chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Input chat
    if query := st.chat_input("Hỏi chuyên gia về kỹ thuật lúa gạo..."):
        # Hiển thị câu hỏi
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)
        
        # Lấy câu trả lời từ AI
        with st.chat_message("assistant"):
            with st.spinner("Đang suy luận..."):
                response = goi_chuyen_gia_hf(query)
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
