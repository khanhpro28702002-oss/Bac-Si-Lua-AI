import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from gtts import gTTS
import requests
import os

st.set_page_config(page_title="Bác Sĩ Lúa AI 4.0", page_icon="🌾", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f4fdf4; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .report-card { background-color: #ffffff; padding: 20px; border-radius: 15px; border-left: 8px solid #2e7d32; }
    h1 { color: #1b5e20; }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []

# KIẾN THỨC CHAT
KIEN_THUC = {
    "đạo ôn": "🔥 **BỆNH ĐẠO ÔN**\n\n**Triệu chứng:** Vết hình mắt én, tâm xám trắng, viền nâu\n\n**Thuốc:** Beam 75WP (200g/ha), Fuji-one 40EC\n\n**Phòng ngừa:** Giữ nước ổn định, không bón thừa đạm\n\n**Giống kháng:** OM5451, OM6976",
    "bạc lá": "🦠 **BỆNH BẠC LÁ**\n\n**Triệu chứng:** Vết lan dọc mép lá, màu vàng/trắng xám\n\n**Thuốc:** Starner 20WP (50g/20L), Xanthomix\n\n**Nguyên nhân:** Vi khuẩn Xanthomonas\n\n**Khuyến cáo:** Rút nước ruộng, ngưng bón đạm",
    "đốm nâu": "🍂 **BỆNH ĐỐM NÂU**\n\n**Triệu chứng:** Vết tròn màu nâu như hạt mè\n\n**Thuốc:** Tilt Super 300EC, Anvil 5SC\n\n**Nguyên nhân:** Nấm, thiếu dinh dưỡng\n\n**Bổ sung:** Vôi bột 500kg/ha, bón cân đối N-P-K",
    "sâu cuốn lá": "🐛 **SÂU CUỐN LÁ**\n\n**Triệu chứng:** Lá bị cuộn thành ống\n\n**Thuốc:** Coragen (125ml/ha) phun khi sâu non\n\n**Phòng trừ:** Bật đèn bắt sâu, thả ong ký sinh\n\n**Thời điểm:** Sâu non 1-2 tuổi hiệu quả nhất",
    "bón phân": "🌱 **BÓN PHÂN LÚA**\n\n**Đạm (Urê 46%):** 120kg/ha chia 3 lần\n- Lúc cày: 40kg\n- Đẻ nhánh: 50kg\n- Làm đòng: 30kg\n\n**Lân (SP36):** 60kg/ha lúc cày\n\n**Kali (KCl):** 40kg/ha lúc đẻ nhánh\n\n**Lưu ý:** Không bón thừa đạm giai đoạn cuối → dễ đổ",
    "om5451": "🌾 **GIỐNG OM5451**\n\n**Năng suất:** 7-8 tấn/ha\n\n**Thời gian:** 95 ngày (vừa sớm)\n\n**Ưu điểm:**\n- Kháng đạo ôn tốt\n- Chịu hạn\n- Chất lượng gạo khá\n\n**Thời vụ:** Phù hợp cả Đông Xuân và Hè Thu",
    "om6976": "🌾 **GIỐNG OM6976**\n\n**Năng suất:** 6.5-7 tấn/ha\n\n**Thời gian:** 100 ngày\n\n**Ưu điểm:**\n- Gạo thơm, chất lượng cao\n- Thích hợp xuất khẩu\n- Giá bán cao hơn OM5451",
    "gieo sạ": "🚜 **GIEO SẠ LÚA**\n\n**Mật độ giống:** 120-150kg/ha\n\n**Thời vụ:**\n- Đông Xuân: tháng 11-12\n- Hè Thu: tháng 5-6\n\n**Chuẩn bị:**\n- Ủ nước 3-5 ngày\n- Diệt cỏ trước khi gieo\n- Đất phải bằng phẳng",
    "thời vụ": "📅 **THỜI VỤ LÚA MIỀN BẮC**\n\n**Vụ Đông Xuân:**\n- Gieo: 11-12\n- Thu: 3-4\n- Nhiệt độ thấp, ít sâu bệnh\n\n**Vụ Hè Thu:**\n- Gieo: 5-6\n- Thu: 8-9\n- Nắng nóng, nhiều sâu bệnh hơn"
}

def tim_tra_loi(cau_hoi):
    cau_hoi = cau_hoi.lower()
    for key, value in KIEN_THUC.items():
        if key in cau_hoi:
            return value
    return "🌾 **TÔI CÓ THỂ TƯ VẤN VỀ:**\n\n• Bệnh: đạo ôn, bạc lá, đốm nâu\n• Sâu hại: sâu cuốn lá\n• Dinh dưỡng: bón phân\n• Giống lúa: OM5451, OM6976\n• Kỹ thuật: gieo sạ, thời vụ\n\n**Hãy hỏi cụ thể hơn nhé!**"

DATA_BENH = {
    "Bacterial Leaf Blight": {
        "ten": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "trieu_chung": "Vết bệnh lan dọc mép lá từ chóp xuống, màu vàng hoặc trắng xám.",
        "nguyen_nhan": "Vi khuẩn Xanthomonas oryzae. Thừa đạm, mưa bão.",
        "thuoc": ["Starner 20WP", "Xanthomix 20WP", "Totan 200WP"],
        "loi_khuyen": "Ngưng bón đạm, bón Kali. Rút nước ruộng."
    },
    "Blast": {
        "ten": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "trieu_chung": "Vết bệnh hình mắt én, tâm xám trắng, viền nâu đậm.",
        "nguyen_nhan": "Nấm Pyricularia oryzae. Độ ẩm cao, sương mù.",
        "thuoc": ["Beam 75WP", "Fuji-one 40EC", "Filia 525SE"],
        "loi_khuyen": "Giữ nước ruộng ổn định. Không phun lá khi bệnh."
    },
    "Brown Spot": {
        "ten": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "trieu_chung": "Vết tròn nhỏ màu nâu như hạt mè.",
        "nguyen_nhan": "Nấm. Thiếu dinh dưỡng, đất phèn.",
        "thuoc": ["Tilt Super 300EC", "Anvil 5SC"],
        "loi_khuyen": "Bón cân đối N-P-K, bổ sung vôi."
    }
}
DATA_BENH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"},
    "Rice Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"}
})

def ve_bbox(img, predictions):
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 25)
    except:
        font = ImageFont.load_default()
    for i, pred in enumerate(predictions[:3]):
        conf = pred['confidence'] * 100
        label = f"{pred['class']}: {conf:.1f}%"
        x, y = 20, 20 + i * 35
        bbox = draw.textbbox((x, y), label, font=font)
        draw.rectangle(bbox, fill=(0, 128, 0, 200))
        draw.text((x, y), label, fill=(255, 255, 255), font=font)
    return img

# HEADER
st.markdown("<h1>🌾 BÁC SĨ LÚA AI 4.0</h1>", unsafe_allow_html=True)
st.caption("Chẩn đoán bệnh lúa + Chat tư vấn thông minh")
st.markdown("---")

# TABS
tab1, tab2, tab3 = st.tabs(["🔍 CHẨN ĐOÁN HÌNH ẢNH", "💬 CHAT CHUYÊN GIA", "📋 LỊCH SỬ"])

# TAB 1: CHẨN ĐOÁN
with tab1:
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        st.subheader("1. Chụp/Tải ảnh lá lúa")
        input_type = st.radio("Chọn nguồn:", ["Tải ảnh từ máy", "Chụp bằng Camera"], horizontal=True)
        if input_type == "Chụp bằng Camera":
            file = st.camera_input("Chụp ảnh lá lúa")
        else:
            file = st.file_uploader("Chọn file ảnh", type=['jpg','png','jpeg'])

    if file:
        img = Image.open(file).convert("RGB")
        with col_l:
            st.image(img, use_column_width=True, caption="Ảnh đầu vào")
            
            if st.button("🚀 BẮT ĐẦU CHẨN ĐOÁN", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("AI đang phân tích..."):
                        img.save("process.jpg")
                        client = InferenceHTTPClient(
                            api_url="https://detect.roboflow.com", 
                            api_key="8tf2UvcnEv8h80bV2G0Q"
                        )
                        res = client.infer("process.jpg", model_id="rice-leaf-disease-twtlz/1")
                        preds = res.get('predictions', [])
                        
                        if preds:
                            top3 = sorted(preds, key=lambda x: x['confidence'], reverse=True)[:3]
                            img_annotated = ve_bbox(img.copy(), top3)
                            st.image(img_annotated, caption="Kết quả AI")
                            
                            st.subheader("📊 Độ tin cậy")
                            c1, c2, c3 = st.columns(3)
                            for i, pred in enumerate(top3):
                                with [c1, c2, c3][i]:
                                    emoji = ["🟢", "🟡", "🟠"][i]
                                    st.metric(f"{emoji} {pred['class']}", f"{pred['confidence']*100:.1f}%")
                            
                            top = top3[0]
                            benh = DATA_BENH.get(top['class'])
                            if benh and "ref" in benh:
                                benh = DATA_BENH[benh["ref"]]
                            
                            if benh:
                                st.markdown(f"### ✅ {benh['ten']} ({top['confidence']*100:.1f}%)")
                                st.markdown(f"""
                                <div class="report-card">
                                    <p><b>🧐 Triệu chứng:</b> {benh['trieu_chung']}</p>
                                    <p><b>🌪️ Nguyên nhân:</b> {benh['nguyen_nhan']}</p>
                                    <p style="color: #d32f2f;"><b>💊 Thuốc:</b> {', '.join(benh['thuoc'])}</p>
                                    <p><b>💡 Khuyến cáo:</b> {benh['loi_khuyen']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                st.session_state.history.append({
                                    "time": datetime.now().strftime("%H:%M"),
                                    "benh": benh['ten'],
                                    "conf": top['confidence']*100
                                })
                        else:
                            st.success("🌿 Cây lúa khỏe mạnh!")

# TAB 2: CHAT
with tab2:
    st.subheader("💬 Hỏi đáp với chuyên gia AI")
    st.caption("Kiến thức offline - Không cần API - Trả lời ngay lập tức")
    
    # Hiển thị lịch sử chat
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Input chat
    if prompt := st.chat_input("Ví dụ: Lúa bị đạo ôn phải làm sao?"):
        # Hiển thị câu hỏi
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Tìm câu trả lời
        response = tim_tra_loi(prompt)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# TAB 3: LỊCH SỬ
with tab3:
    st.subheader("📋 Lịch sử chẩn đoán hôm nay")
    if st.session_state.history:
        for h in reversed(st.session_state.history):
            st.write(f"⏰ {h['time']} - **{h['benh']}** ({h['conf']:.1f}%)")
    else:
        st.info("Chưa có lượt khám nào.")

st.markdown("---")
st.caption("🌾 Bác Sĩ Lúa AI 4.0 - Hỗ trợ nông dân Việt Nam")
