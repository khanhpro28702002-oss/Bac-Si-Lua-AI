import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image
import os
import re

# ==========================================
# KIẾN THỨC NỀN TẢNG (Knowledge Base)
# ==========================================
KIEN_THUC_NONG_NGHIEP = {
    # Bệnh lúa phổ biến
    "đạo ôn": {
        "ten_viet": "Bệnh đạo ôn lúa",
        "trieu_chung": "Đốm màu nâu xám trên lá, cổ bông gãy đổ, hạt lép",
        "nguyen_nhan": "Nấm Pyricularia oryzae, thời tiết ẩm ướt, nhiều đạm",
        "thuoc": "Tricyclazole (Beam 75WP), Tebuconazole (Folicur 250EC)",
        "lieu_luong": "Beam: 200g/ha, Folicur: 300ml/ha",
        "phong_ngua": "Gieo giống lành, bón phân cân đối, thoát nước tốt"
    },
    "bạc lá": {
        "ten_viet": "Bệnh bạc lá",
        "trieu_chung": "Lá có vệt trắng bạc, cuộn lại, cây vàng chết",
        "nguyen_nhan": "Virus do rầy nâu truyền bệnh",
        "thuoc": "Không có thuốc đặc trị virus. Phòng trừ rầy nâu: Buprofezin, Imidacloprid",
        "lieu_luong": "Đốc Hại Plus 200ml/ha",
        "phong_ngua": "Trồng giống kháng bệnh, diệt rầy sớm"
    },
    "khô vằn": {
        "ten_viet": "Bệnh khô vằn (Bacterial leaf blight)",
        "trieu_chung": "Lá có vệt vàng từ mép lá, khô dần vào trong",
        "nguyen_nhan": "Vi khuẩn Xanthomonas oryzae",
        "thuoc": "Oxolinic acid, Bismerthiazol",
        "lieu_luong": "Starner 20WP: 50g/20L nước",
        "phong_ngua": "Tưới nước sạch, không ngập úng"
    },
    
    # Sâu hại
    "sâu cuốn lá": {
        "ten_viet": "Sâu cuốn lá nhỏ",
        "trieu_chung": "Lá bị cuộn lại, có ống lá, ảnh hưởng quang hợp",
        "nguyen_nhan": "Côn trùng Cnaphalocrocis medinalis",
        "thuoc": "Chlorantraniliprole (Coragen), Indoxacarb",
        "lieu_luong": "Coragen 125ml/ha, phun khi sâu non",
        "phong_ngua": "Bật đèn bắt sâu, thả thiên địch (ong ký sinh)"
    },
    
    # Dinh dưỡng
    "bón phân": {
        "loi_ich": "Cung cấp dinh dưỡng N-P-K cho cây phát triển",
        "linh_dan": "Phân đạm (Urê 46%): 3 lần - Lúc cày, đẻ nhánh, làm đòng",
        "lieu_luong": "Tổng 120kg N/ha, chia 40kg lúc cày, 50kg đẻ nhánh, 30kg làm đòng",
        "luu_y": "Không bón quá nhiều đạm giai đoạn cuối -> dễ đổ"
    },
    
    # Kỹ thuật trồng
    "gieo sạ": {
        "uu_diem": "Tiết kiệm công, phù hợp diện tích lớn",
        "thoi_vu": "Vụ đông xuân: tháng 11-12, vụ hè thu: tháng 5-6",
        "mat_do": "120-150kg giống/ha",
        "luu_y": "Đất phải ủ nước 3-5 ngày, diệt cỏ trước khi gieo"
    },
    
    # Giống lúa
    "giống lúa": {
        "pho_bien": "OM5451, OM6976, Jasmine 85, VNR20, OM4218",
        "om5451": "Năng suất cao (7-8 tấn/ha), chống đạo ôn tốt, 95 ngày",
        "om6976": "Chất lượng gạo tốt, thơm, 100 ngày, 6.5-7 tấn/ha",
        "jasmine": "Gạo thơm cao cấp, xuất khẩu, 105 ngày"
    }
}

# ==========================================
# HỆ THỐNG TRẢ LỜI THÔNG MINH
# ==========================================
def tim_tu_khoa(cau_hoi):
    """Tìm từ khóa trong câu hỏi"""
    cau_hoi = cau_hoi.lower()
    tu_khoa_tim_thay = []
    
    for tu_khoa in KIEN_THUC_NONG_NGHIEP.keys():
        if tu_khoa in cau_hoi or any(word in cau_hoi for word in tu_khoa.split()):
            tu_khoa_tim_thay.append(tu_khoa)
    
    return tu_khoa_tim_thay

def tao_cau_tra_loi(tu_khoa):
    """Tạo câu trả lời từ knowledge base"""
    if tu_khoa not in KIEN_THUC_NONG_NGHIEP:
        return None
    
    thong_tin = KIEN_THUC_NONG_NGHIEP[tu_khoa]
    tra_loi = f"### Về **{tu_khoa.upper()}**:\n\n"
    
    for key, value in thong_tin.items():
        key_viet = {
            "ten_viet": "📌 Tên đầy đủ",
            "trieu_chung": "🔍 Triệu chứng",
            "nguyen_nhan": "⚠️ Nguyên nhân",
            "thuoc": "💊 Thuốc điều trị",
            "lieu_luong": "⚖️ Liều lượng",
            "phong_ngua": "🛡️ Phòng ngừa",
            "loi_ich": "✅ Lợi ích",
            "linh_dan": "📋 Hướng dẫn",
            "luu_y": "⚡ Lưu ý",
            "uu_diem": "⭐ Ưu điểm",
            "thoi_vu": "🗓️ Thời vụ",
            "mat_do": "🌾 Mật độ",
            "pho_bien": "🏆 Giống phổ biến",
            "om5451": "🌱 OM5451",
            "om6976": "🌱 OM6976",
            "jasmine": "🌱 Jasmine 85"
        }.get(key, key)
        
        tra_loi += f"**{key_viet}:** {value}\n\n"
    
    return tra_loi

def chatbot_thong_minh(cau_hoi):
    """Chatbot trả lời dựa trên kiến thức có sẵn"""
    # Tìm từ khóa
    tu_khoa_list = tim_tu_khoa(cau_hoi)
    
    if not tu_khoa_list:
        # Câu trả lời mặc định nếu không tìm thấy
        return """Xin lỗi, tôi chưa có thông tin về câu hỏi này trong cơ sở dữ liệu.

**Tôi có thể tư vấn về:**
- Bệnh lúa: đạo ôn, bạc lá, khô vằn
- Sâu hại: sâu cuốn lá
- Dinh dưỡng: bón phân
- Kỹ thuật: gieo sạ
- Giống lúa: OM5451, OM6976, Jasmine

Hãy hỏi cụ thể hơn nhé!"""
    
    # Trả lời từng chủ đề tìm thấy
    cau_tra_loi = ""
    for tu_khoa in tu_khoa_list:
        cau_tra_loi += tao_cau_tra_loi(tu_khoa) + "\n---\n\n"
    
    return cau_tra_loi

# ==========================================
# GIAO DIỆN STREAMLIT
# ==========================================
st.set_page_config(page_title="Bác Sĩ Lúa AI", layout="wide")
st.markdown("<h1 style='color: #2e7d32;'>🌾 BÁC SĨ LÚA: KIẾN THỨC OFFLINE</h1>", unsafe_allow_html=True)
st.info("💡 Chatbot thông minh không cần kết nối API - Kiến thức từ chuyên gia nông nghiệp Việt Nam")

st.markdown("---")
tab1, tab2 = st.tabs(["📸 CHẨN ĐOÁN ẢNH", "💬 CHUYÊN GIA AI"])

# TAB 1: CHẨN ĐOÁN
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
                        benh = preds[0]['class'].lower()
                        st.error(f"⚠️ Phát hiện: **{benh}**")
                        
                        # Tìm thông tin bệnh từ knowledge base
                        thong_tin = chatbot_thong_minh(benh)
                        st.success("**Tư vấn điều trị:**")
                        st.markdown(thong_tin)
                    else:
                        st.success("✅ Cây lúa khỏe mạnh!")
                    
                    if os.path.exists("temp.jpg"):
                        os.remove("temp.jpg")
                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")

# TAB 2: CHATBOT
with tab2:
    st.write("### 💡 Hỏi về:")
    col1, col2 = st.columns(2)
    with col1:
        st.write("- 🦠 Bệnh lúa (đạo ôn, bạc lá, khô vằn)")
        st.write("- 🐛 Sâu hại (sâu cuốn lá)")
        st.write("- 🌱 Giống lúa (OM5451, Jasmine...)")
    with col2:
        st.write("- 💚 Bón phân, dinh dưỡng")
        st.write("- 🚜 Kỹ thuật trồng (gieo sạ)")
        st.write("- 📅 Thời vụ, mùa vụ")
    
    # Lịch sử chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input
    if query := st.chat_input("Ví dụ: Lúa bị đạo ôn phải làm sao?"):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)
        
        with st.chat_message("assistant"):
            response = chatbot_thong_minh(query)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("---")
st.caption("🌾 Bác Sĩ Lúa - Kiến thức offline | Không cần API")
