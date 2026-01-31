import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import os

# Cấu hình trang
st.set_page_config(page_title="Bác Sĩ Lúa AI 4.0", page_icon="🌾", layout="wide")

# CSS tùy chỉnh giao diện
st.markdown("""
<style>
    .main {background-color: #f0f2f6;}
    h1 {color: #2e7d32;}
    .stChatInput {border-radius: 20px;}
    .report-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #2e7d32;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []

# ==============================================================================
# 1. CƠ SỞ DỮ LIỆU TRI THỨC
# ==============================================================================

KIEN_THUC = {
    "đạo ôn": """🔥 **BỆNH ĐẠO ÔN (CHÁY LÁ)**
    
**1. Tác nhân:** Nấm *Pyricularia oryzae*. Phát triển mạnh khi trời âm u, sương mù, ẩm độ cao, bón thừa đạm.

**2. Dấu hiệu nhận biết:** 
- **Trên lá:** Vết bệnh hình thoi (mắt én), tâm màu xám trắng, viền nâu đậm.
- **Trên cổ bông:** Vết nâu xám bao quanh cổ bông, làm bông bị gãy gục, hạt lép (đạo ôn cổ bông).

**3. Biện pháp phòng trừ:**
- **Canh tác:** Gieo sạ mật độ vừa phải, bón cân đối N-P-K, không bón thừa đạm đón đòng.
- **Thuốc đặc trị:** Tricyclazole (Beam 75WP), Isoprothiolane (Fuji-one), Fenoxanil, Azoxystrobin.
- **Lưu ý:** Phun ngừa đạo ôn cổ bông ở giai đoạn trước trổ và sau khi trổ đều.""",

    "khô vằn": """🍂 **BỆNH KHÔ VẰN (ĐỐM VẰN)**
    
**1. Tác nhân:** Nấm *Rhizoctonia solani*. Thường gặp ở ruộng sạ dày, ngập nước lâu.

**2. Dấu hiệu nhận biết:**
- Vết bệnh ở bẹ lá, phiến lá dạng đám mây, vằn da hổ.
- Ban đầu là đốm hình bầu dục màu lục tối, sau chuyển xám trắng, viền nâu.
- Xuất hiện hạch nấm hình tròn dẹt màu nâu.

**3. Biện pháp phòng trừ:**
- **Canh tác:** Vệ sinh đồng ruộng, dọn sạch cỏ bờ (nơi nấm trú ẩn).
- **Thuốc đặc trị:** Hexaconazole (Anvil 5SC), Validamycin (Validacin), Pencycuron, Azoxystrobin.
- **Sinh học:** Sử dụng nấm đối kháng *Trichoderma*.""",

    "lem lép hạt": """⚫ **BỆNH LEM LÉP HẠT**
    
**1. Nguyên nhân:** Do phức hợp nấm (*Fusarium, Curvularia*) và vi khuẩn (*Pseudomonas glumae*) tấn công giai đoạn trổ.

**2. Dấu hiệu:**
- Hạt lúa có đốm nâu, đen, tím hoặc biến màu xám ngoét.
- Hạt lửng hoặc lép hoàn toàn, gạo đục, dễ gãy.

**3. Biện pháp phòng trừ:**
- **Thời điểm vàng:** Phun thuốc 2 lần: (1) Khi lúa trổ lẹt xẹt 5% và (2) Khi lúa trổ đều.
- **Thuốc đặc trị:** Difenoconazole, Propiconazole (Tilt Super), Azoxystrobin + Difenoconazole (Amistar Top).""",

    "bạc lá": """🦠 **BỆNH BẠC LÁ (CHÁY BÌA LÁ)**
    
**1. Tác nhân:** Vi khuẩn *Xanthomonas oryzae*. Lây lan nhanh qua vết thương cơ giới sau mưa bão.

**2. Dấu hiệu nhận biết:**
- Vết bệnh lan từ chóp lá dọc theo hai bên mép lá.
- Vết bệnh màu vàng hoặc trắng xám, ranh giới vết bệnh gợn sóng.
- Sáng sớm có giọt dịch vi khuẩn màu vàng đục trên vết bệnh.

**3. Biện pháp phòng trừ:**
- **Cấp bách:** Khi bệnh chớm xuất hiện, **ngưng bón đạm**, rút nước để khô ruộng 2-3 ngày.
- **Thuốc đặc trị:** Bismerthiazol (Xanthomix), Oxolinic acid (Starner), Bronopol, Kasugamycin.
- **Lưu ý:** Không phun thuốc kèm phân bón lá khi lúa đang bệnh.""",

    "vàng lùn": """⚠️ **BỆNH VÀNG LÙN & LÙN XOẮN LÁ**
    
**1. Tác nhân:** Virus do **Rầy nâu** truyền bệnh. Không có thuốc đặc trị virus.

**2. Dấu hiệu nhận biết:**
- **Vàng lùn:** Lá lúa chuyển vàng từ chóp xuống, cây thấp lùn, đẻ nhánh kém, rễ thối.
- **Lùn xoắn lá:** Lá xanh đậm, ngắn, xoăn tít (như lò xo), gân lá sưng, không trổ bông được.

**3. Biện pháp quản lý:**
- **Tiêu hủy:** Nhổ bỏ, vùi sâu bụi lúa bệnh để cắt nguồn lây.
- **Trừ môi giới:** Phòng trừ rầy nâu triệt để bằng Pymetrozine, Buprofezin.
- **Giống:** Chọn giống kháng rầy, gieo sạ "né rầy".""",

    "rầy nâu": """🦗 **RẦY NÂU (Brown Planthopper)**
    
**1. Tác hại:** Chích hút nhựa làm lúa "cháy rầy", truyền bệnh vàng lùn.

**2. Phòng trừ:**
- Thăm đồng thường xuyên, vạch gốc lúa kiểm tra.
- Phun thuốc khi mật độ > 3 con/tép.
- **Thuốc:** Pymetrozine (Chess), Buprofezin (Applaud), Nitenpyram.
- Áp dụng IPM, bảo vệ thiên địch (nhện, bọ xít nước).""",

    "sâu cuốn lá": """🐛 **SÂU CUỐN LÁ NHỎ**
    
**1. Dấu hiệu:** Sâu nhả tơ cuốn dọc lá lúa thành ống, ăn phần thịt lá để lại lớp biểu bì trắng.

**2. Ngưỡng phòng trừ:** Mật độ 20-50 con/m2 (giai đoạn đẻ nhánh-làm đòng).

**3. Thuốc đặc trị:** Indoxacarb, Chlorantraniliprole (Virtako), Emamectin benzoate. Phun khi sâu còn non (tuổi 1-2).""",

    "bón phân": """🌱 **KỸ THUẬT BÓN PHÂN CÂN ĐỐI (Theo quy trình 3 Giảm 3 Tăng)**
    
**Nguyên tắc:** "Nặng đầu, nhẹ cuối".

1. **Bón lót:** 100% Lân + 30% Đạm.
2. **Bón thúc 1 (7-10 NSS):** 30% Đạm + 30% Kali.
3. **Bón thúc 2 (18-22 NSS):** 40% Đạm còn lại.
4. **Bón đón đòng (40-45 NSS):** 70% Kali còn lại (tùy màu lá lúa mà bổ sung đạm ít hay nhiều - bảng so màu lá).

⚠️ **Lưu ý:** Thừa đạm gây đạo ôn, bạc lá, đổ ngã.""",
    
    "ipm": """🛡️ **QUẢN LÝ DỊCH HẠI TỔNG HỢP (IPM)**
    
**5 Nguyên tắc cơ bản:**
1. Trồng cây khỏe (giống tốt, đất tốt).
2. Bảo vệ thiên địch (không phun thuốc bừa bãi).
3. Thăm đồng thường xuyên.
4. Nông dân trở thành chuyên gia.
5. Phòng trừ dịch hại đúng cách (chỉ phun khi tới ngưỡng kinh tế).""",

    "đốm nâu": """🍂 **BỆNH ĐỐM NÂU (TIÊM LỬA)**
    
**1. Tác nhân:** Nấm *Bipolaris oryzae*. Thường do đất thiếu dinh dưỡng, phèn.

**2. Dấu hiệu:** Vết tròn nhỏ màu nâu như hạt mè, lá vàng.

**3. Biện pháp:** Bón bổ sung Kali, Silic, vôi bột để cải tạo đất. Thuốc: Tilt Super 300EC, Anvil 5SC."""
}

# Mapping từ khóa
KEYWORD_MAPPING = {
    "đốm sọc": "bạc lá",
    "cháy bìa": "bạc lá",
    "cháy bìa lá": "bạc lá",
    "tiêm lửa": "đốm nâu",
    "rầy": "rầy nâu",
    "sâu": "sâu cuốn lá",
    "lúa von": "đạo ôn",
    "cháy lá": "đạo ôn",
    "thuốc sâu": "sâu cuốn lá",
    "phân bón": "bón phân",
    "bón đạm": "bón phân",
    "vàng": "vàng lùn",
    "lùn": "vàng lùn"
}

def tim_tra_loi(cau_hoi):
    """Tìm kiếm câu trả lời trong cơ sở tri thức"""
    cau_hoi = cau_hoi.lower()
    
    # Thêm từ khóa mapping
    for key, mapped_value in KEYWORD_MAPPING.items():
        if key in cau_hoi:
            cau_hoi += " " + mapped_value
            
    # Tìm kiếm trong cơ sở dữ liệu
    for key, value in KIEN_THUC.items():
        if key in cau_hoi:
            return value
            
    return """🌾 **BÁC SĨ LÚA CÓ THỂ TƯ VẤN VỀ:**

🦠 **Bệnh hại:** Đạo ôn, Bạc lá (cháy bìa), Khô vằn, Lem lép hạt, Đốm nâu, Vàng lùn.

🐛 **Sâu hại:** Rầy nâu, Sâu cuốn lá.

🧪 **Thuốc BVTV:** Tên hoạt chất, cách dùng.

🌱 **Kỹ thuật:** Bón phân, IPM.

**Bà con hãy đặt câu hỏi cụ thể. Ví dụ:**
- "Thuốc trị đạo ôn là gì?"
- "Cách phòng rầy nâu"
- "Lúa bị cháy lá dùng thuốc gì?"
- "Kỹ thuật bón phân cho lúa"
"""

# ==============================================================================
# 2. DỮ LIỆU CHẨN ĐOÁN HÌNH ẢNH
# ==============================================================================

DATA_BENH = {
    "Bacterial Leaf Blight": {
        "ten": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "trieu_chung": "Vết bệnh lan dọc mép lá, màu vàng hoặc trắng xám, có giọt dịch vi khuẩn.",
        "nguyen_nhan": "Vi khuẩn *Xanthomonas oryzae*. Do mưa bão, thừa đạm.",
        "thuoc": ["Kasumin 2SL", "Starner 20WP", "Totan 200WP", "Xanthomix 20WP"],
        "loi_khuyen": "Rút nước, tháo nước khô ruộng 2-3 ngày. Ngưng bón đạm."
    },
    "Blast": {
        "ten": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "trieu_chung": "Vết hình thoi (mắt én), tâm xám trắng, viền nâu.",
        "nguyen_nhan": "Nấm *Pyricularia oryzae*. Sương mù nhiều, ẩm độ cao.",
        "thuoc": ["Beam 75WP (Tricyclazole)", "Filia 525SE", "Fuji-one 40EC", "Ninja 35EC"],
        "loi_khuyen": "Giữ nước ruộng. Không được để ruộng khô. Phun thuốc đặc trị nấm."
    },
    "Brown Spot": {
        "ten": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "trieu_chung": "Vết tròn nhỏ màu nâu như hạt mè, lá vàng.",
        "nguyen_nhan": "Nấm *Bipolaris oryzae*. Thường do đất thiếu dinh dưỡng, phèn.",
        "thuoc": ["Tilt Super 300EC", "Anvil 5SC", "Nevado"],
        "loi_khuyen": "Bón bổ sung Kali, Silic, vôi bột để cải tạo đất."
    },
    "Tungro": {
        "ten": "BỆNH VÀNG LÙN/LÙN XOẮN LÁ",
        "trieu_chung": "Lá vàng cam, cây thấp lùn, lá xoắn.",
        "nguyen_nhan": "Virus do Rầy nâu truyền.",
        "thuoc": ["Không có thuốc trị virus", "Phun thuốc trừ rầy: Chess", "Applaud"],
        "loi_khuyen": "Nhổ bỏ cây bệnh. Quản lý rầy nâu chặt chẽ."
    }
}

# Mapping các tên class khác
DATA_BENH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"},
    "Rice Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"},
    "Hispa": {"ref": "Blast"}
})

def ve_bbox(img, predictions):
    """Vẽ bounding box và label lên ảnh"""
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 25)
    except:
        font = ImageFont.load_default()
        
    for i, pred in enumerate(predictions[:3]):
        conf = pred['confidence'] * 100
        if conf < 30:  # Lọc độ tin cậy quá thấp
            continue
        
        label = f"{pred['class']}: {conf:.1f}%"
        
        # Lấy tọa độ (API Roboflow trả về x, y, width, height)
        x = pred.get('x', 100)
        y = pred.get('y', 100)
        w = pred.get('width', 200)
        h = pred.get('height', 200)
        
        # Chuyển sang (x0, y0, x1, y1)
        x0 = x - w/2
        y0 = y - h/2
        x1 = x + w/2
        y1 = y + h/2
        
        # Vẽ khung màu đỏ
        draw.rectangle([x0, y0, x1, y1], outline="red", width=4)
        
        # Vẽ nền label
        text_bbox = draw.textbbox((x0, y0-35), label, font=font)
        draw.rectangle(text_bbox, fill=(255, 0, 0))
        draw.text((x0, y0-35), label, fill="white", font=font)
        
    return img

# ==============================================================================
# 3. GIAO DIỆN ỨNG DỤNG
# ==============================================================================

st.markdown("<h1 style='text-align: center;'>🌾 BÁC SĨ LÚA AI 4.0</h1>", unsafe_allow_html=True)
st.caption("Chẩn đoán bệnh lúa qua ảnh & Tư vấn kỹ thuật canh tác (Dữ liệu cập nhật 2026)")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🔍 CHẨN ĐOÁN HÌNH ẢNH", "💬 CHAT VỚI CHUYÊN GIA", "📋 LỊCH SỬ"])

# --- TAB 1: CHẨN ĐOÁN ---
with tab1:
    col_l, col_r = st.columns([1, 1.3])
    
    with col_l:
        st.subheader("1. Tải ảnh lá lúa bị bệnh")
        st.info("💡 **Mẹo:** Chụp rõ vết bệnh, đủ ánh sáng, tránh bị chói.")
        
        input_type = st.radio("Chọn nguồn ảnh:", ["📁 Tải từ máy", "📸 Chụp trực tiếp"], horizontal=True)
        
        file = None
        if input_type == "📸 Chụp trực tiếp":
            file = st.camera_input("Chụp ảnh lá lúa")
        else:
            file = st.file_uploader("Chọn file ảnh (jpg, png)", type=['jpg','png','jpeg'])

        if file:
            img = Image.open(file).convert("RGB")
            st.image(img, use_column_width=True, caption="Ảnh của bạn")
            
            if st.button("🚀 PHÂN TÍCH BỆNH", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("🔬 AI đang phân tích hình ảnh..."):
                        # Lưu ảnh tạm
                        img.save("process.jpg")
                        
                        # Gọi API Roboflow
                        try:
                            client = InferenceHTTPClient(
                                api_url="https://detect.roboflow.com",
                                api_key="8tf2UvcnEv8h80bV2G0Q"
                            )
                            res = client.infer("process.jpg", model_id="rice-leaf-disease-twtlz/1")
                            preds = res.get('predictions', [])
                            
                            if preds and len(preds) > 0:
                                # Sắp xếp theo confidence
                                top_preds = sorted(preds, key=lambda x: x['confidence'], reverse=True)
                                top_pred = top_preds[0]
                                
                                class_name = top_pred['class']
                                confidence = top_pred['confidence'] * 100
                                
                                # Vẽ bounding box
                                img_annotated = ve_bbox(img.copy(), preds)
                                st.image(img_annotated, caption=f"✅ Kết quả AI: {class_name}", use_column_width=True)
                                
                                # Hiển thị top 3 kết quả
                                st.markdown("### 📊 Độ tin cậy AI:")
                                col1, col2, col3 = st.columns(3)
                                
                                for idx, pred in enumerate(top_preds[:3]):
                                    emoji = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉"
                                    with [col1, col2, col3][idx]:
                                        st.metric(
                                            f"{emoji} {pred['class']}", 
                                            f"{pred['confidence']*100:.1f}%"
                                        )
                                
                                # Tra cứu thông tin bệnh
                                benh_info = DATA_BENH.get(class_name)
                                if benh_info and "ref" in benh_info:
                                    benh_info = DATA_BENH[benh_info["ref"]]
                                
                                if benh_info:
                                    st.markdown(f"""
                                    <div class="report-card">
                                        <h2 style="color: #c62828;">🔍 CHẨN ĐOÁN: {benh_info['ten']}</h2>
                                        <p><strong>Độ tin cậy:</strong> <span style="font-size: 20px; color: #1b5e20;">{confidence:.1f}%</span></p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.markdown(f"""
                                    #### 📋 Triệu chứng điển hình:
                                    {benh_info['trieu_chung']}
                                    
                                    #### 🧬 Nguyên nhân:
                                    {benh_info['nguyen_nhan']}
                                    
                                    #### 💊 Thuốc BVTV đề xuất:
                                    {', '.join(benh_info['thuoc'])}
                                    
                                    #### 🛡️ Giải pháp xử lý (IPM):
                                    {benh_info['loi_khuyen']}
                                    """)
                                    
                                    # Lưu lịch sử
                                    st.session_state.history.append({
                                        "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                        "benh": benh_info['ten'],
                                        "conf": confidence,
                                        "class": class_name
                                    })
                                    
                                    st.success("✅ Đã lưu vào lịch sử chẩn đoán!")
                                    
                                else:
                                    st.warning(f"⚠️ Phát hiện '{class_name}' nhưng chưa có dữ liệu chi tiết tiếng Việt trong hệ thống.")
                                    
                            else:
                                st.info("✅ Không phát hiện bệnh rõ ràng. Cây lúa có vẻ khỏe mạnh hoặc cần chụp ảnh rõ hơn.")
                                
                        except Exception as e:
                            st.error(f"❌ **Lỗi kết nối AI:** {str(e)}")
                            st.info("💡 Vui lòng kiểm tra:")
                            st.markdown("""
                            - Kết nối internet
                            - API key Roboflow còn hiệu lực
                            - Ảnh đầu vào có định dạng hợp lệ
                            """)

# --- TAB 2: CHATBOT ---
with tab2:
    st.subheader("💬 Trợ lý ảo Nông Nghiệp")
    st.markdown("*Hỏi đáp về kỹ thuật trồng lúa, phòng trừ sâu bệnh, thuốc BVTV*")
    st.markdown("---")
    
    # Hiển thị lịch sử chat
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Ô nhập liệu
    if prompt := st.chat_input("💬 Nhập câu hỏi (VD: lúa bị cháy lá dùng thuốc gì?)"):
        # Lưu câu hỏi
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Xử lý trả lời
        response = tim_tra_loi(prompt)
        
        # Lưu và hiển thị câu trả lời
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# --- TAB 3: LỊCH SỬ ---
with tab3:
    st.subheader("📋 Nhật ký chẩn đoán")
    
    if st.session_state.history:
        st.markdown(f"**Tổng số lần chẩn đoán:** {len(st.session_state.history)}")
        st.markdown("---")
        
        for i, h in enumerate(reversed(st.session_state.history)):
            with st.expander(f"🔍 **{i+1}. {h['time']}** - {h['benh']} ({h['conf']:.1f}%)"):
                st.markdown(f"""
                - **Thời gian:** {h['time']}
                - **Bệnh phát hiện:** {h['benh']}
                - **Model class:** `{h.get('class', 'N/A')}`
                - **Độ tin cậy:** {h['conf']:.1f}%
                """)
        
        if st.button("🗑️ Xóa toàn bộ lịch sử"):
            st.session_state.history = []
            st.rerun()
            
    else:
        st.info("📝 Chưa có dữ liệu chẩn đoán nào.")
        st.markdown("Hãy tải ảnh lá lúa lên tab **CHẨN ĐOÁN HÌNH ẢNH** để bắt đầu!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: grey; padding: 20px;'>
    <p>🌾 <strong>Bác Sĩ Lúa AI 4.0</strong> | Phát triển bởi Công nghệ AI Nông nghiệp Việt Nam</p>
    <p>Dữ liệu cập nhật: Tháng 1/2026 | Nguồn: Cục BVTV & Viện Lúa ĐBSCL</p>
</div>
""", unsafe_allow_html=True)
