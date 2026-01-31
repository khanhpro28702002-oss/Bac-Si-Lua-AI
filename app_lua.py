import streamlit as st
import google.generativeai as genai
from inference_sdk import InferenceHTTPClient
from PIL import Image
import os

# ================= CONFIG =================
st.set_page_config(page_title="Bác Sĩ Lúa AI Pro", layout="wide")

GEMINI_API_KEY = "AIzaSyAwUoUd1VFGAxHEH1EGOdp44WnbWVJYW_8"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def goi_chuyen_gia_gemini(user_input):
    try:
        prompt = f"""
Bạn là chuyên gia nông nghiệp Việt Nam với 20 năm kinh nghiệm.
Hãy trả lời câu hỏi sau ngắn gọn, dễ hiểu, thực tế:

{user_input}
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi Gemini: {e}"

# ================= UI =================
st.markdown("## 🌾 BÁC SĨ LÚA AI – GEMINI")
st.info("Chẩn đoán bệnh & tư vấn kỹ thuật trồng lúa")

tab1, tab2 = st.tabs(["📸 CHẨN ĐOÁN ẢNH", "💬 HỎI CHUYÊN GIA"])

# ---------- TAB 1 ----------
with tab1:
    f = st.file_uploader("Chọn ảnh lá lúa", type=["jpg", "png", "jpeg"])
    if f:
        img = Image.open(f)
        st.image(img, use_column_width=True)

        if st.button("🔍 PHÂN TÍCH"):
            with st.spinner("Đang phân tích..."):
                img.save("temp.jpg")
                client = InferenceHTTPClient(
                    api_url="https://detect.roboflow.com",
                    api_key="8tf2UvcnEv8h80bV2G0Q"
                )
                res = client.infer("temp.jpg", model_id="rice-leaf-disease-twtlz/1")
                preds = res.get("predictions", [])

                if preds:
                    benh = preds[0]["class"]
                    st.error(f"⚠️ Phát hiện bệnh: **{benh}**")

                    advice = goi_chuyen_gia_gemini(
                        f"Cây lúa bị bệnh {benh}. Cho biết nguyên nhân, thuốc trị và phòng ngừa."
                    )
                    st.success(advice)
                else:
                    st.success("✅ Lá lúa khỏe mạnh")

                os.remove("temp.jpg")

# ---------- TAB 2 ----------
with tab2:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    if q := st.chat_input("Hỏi kỹ thuật trồng lúa..."):
        st.session_state.messages.append({"role": "user", "content": q})
        with st.chat_message("assistant"):
            ans = goi_chuyen_gia_gemini(q)
            st.write(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
