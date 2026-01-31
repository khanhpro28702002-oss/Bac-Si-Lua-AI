import streamlit as st
import requests
from inference_sdk import InferenceHTTPClient
from PIL import Image
from streamlit_js_eval import get_geolocation

# ==========================================
# 1. CẤU HÌNH HUGGING FACE (BỘ NÃO AI)
# ==========================================
# DÁN MÃ TOKEN CỦA BẠN VÀO GIỮA DẤU NGOẶC KÉP
HF_TOKEN = "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"
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
        response = requests.post(MODEL_URL, headers=headers, json=payload, timeout=10)
        result = response.json()
        # Xử lý văn bản trả về
        text = result[0]['generated_text']
        return text.split("<|im_start|>assistant\n")[-1].strip()
    except Exception as e:
        return f"Dạ, chuyên gia AI đang bận tí (Lỗi: {e}). Bà con thử lại sau nhé!"

# ==========================================
# 2. GIAO DIỆN CHÍNH
# ==========================================
st.set_page_config(page_title="Bác Sĩ Lúa AI Pro", layout="wide")
st.markdown("<h1 style='color: #2e7d32;'>🌾 BÁC SĨ LÚA AI: HUGGING FACE EDITION</h1>", unsafe_allow_html=True)

# Lấy GPS an toàn (Chống lỗi DuplicateElementKey và KeyError)
loc = get_geolocation(key='gps_hf_fix')

if loc and 'coords' in loc:
    st.success(f"📍 Vị trí ruộng: {round(loc['coords']['latitude'], 4)}, {round(loc['coords']['longitude'], 4)}")
else:
    st.info("📌 Bà con hãy bấm 'Cho phép' (Allow) vị trí để xem thời tiết nhé.")

st.markdown("---")
tab1, tab2 = st.tabs(["📸 CHẨN ĐOÁN ẢNH", "💬 CHUYÊN GIA AI"])

# --- TAB CHẨN ĐOÁN (Sử dụng Roboflow từ dữ liệu của bạn) ---
with tab1:
    f = st.file_uploader("Chọn ảnh lá lúa bị bệnh", type=['jpg','png','jpeg'])
    if f:
        img = Image.open(f)
        st.image(img, use_column_width=True)
        if st.button("🔍 PHÂN TÍCH BỆNH", type="primary"):
            with st.spinner("Đang soi bệnh..."):
                img.save("temp.jpg")
                # Thông tin từ ảnh cấu hình của bạn
                client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key="8tf2UvcnEv8h80bV2G0Q")
                res = client.infer("temp.jpg", model_id="rice-leaf-disease-twtlz/1")
                preds = res.get('predictions', [])
                if preds:
                    benh = preds[0]['class']
                    st.error(f"⚠️ Phát hiện: {benh}")
                    # Dùng Hugging Face để tư vấn phác đồ
                    advice = goi_chuyen_gia_hf(f"Lúa bị bệnh {benh}. Hãy cho biết tên tiếng Việt và thuốc đặc trị cụ thể.")
                    st.write(advice)
                else: st.success("✅ Cây lúa khỏe mạnh!")

# --- TAB CHATBOT AI ---
with tab2:
    if query := st.chat_input("Hỏi chuyên gia về kỹ thuật lúa gạo..."):
        with st.chat_message("user"): st.write(query)
        with st.chat_message("assistant"):
            with st.spinner("Đang suy luận..."):
                st.write(goi_chuyen_gia_hf(query))