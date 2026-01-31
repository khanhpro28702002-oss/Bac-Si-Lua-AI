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
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []

# ==============================================================================
# 1. CƠ SỞ DỮ LIỆU TRI THỨC (Tổng hợp từ nguồn [2]-[3])
# ==============================================================================

KIEN_THUC = {
    # --- NHÓM BỆNH DO NẤM ---
    "đạo ôn": """🔥 **BỆNH ĐẠO ÔN (CHÁY LÁ)** [4], [5]
    \n**1. Tác nhân:** Nấm *Pyricularia oryzae*. Phát triển mạnh khi trời âm u, sương mù, ẩm độ cao, bón thừa đạm [6].
    \n**2. Dấu hiệu nhận biết:** 
    - **Trên lá:** Vết bệnh hình thoi (mắt én), tâm màu xám trắng, viền nâu đậm [5], [7].
    - **Trên cổ bông:** Vết nâu xám bao quanh cổ bông, làm bông bị gãy gục, hạt lép (đạo ôn cổ bông) [8].
    \n**3. Biện pháp phòng trừ:**
    - **Canh tác:** Gieo sạ mật độ vừa phải, bón cân đối N-P-K, không bón thừa đạm đón đòng [9], [10].
    - **Thuốc đặc trị:** Các hoạt chất *Tricyclazole* (Beam 75WP), *Isoprothiolane* (Fuji-one), *Fenoxanil*, *Azoxystrobin* [11], [12].
    - **Lưu ý:** Phun ngừa đạo ôn cổ bông ở giai đoạn trước trổ và sau khi trổ đều [13].""",

    "khô vằn": """🍂 **BỆNH KHÔ VẰN (ĐỐM VẰN)** [14], [15]
    \n**1. Tác nhân:** Nấm *Rhizoctonia solani*. Thường gặp ở ruộng sạ dày, ngập nước lâu [16].
    \n**2. Dấu hiệu nhận biết:**
    - Vết bệnh ở bẹ lá, phiến lá dạng đám mây, vằn da hổ [17].
    - Ban đầu là đốm hình bầu dục màu lục tối, sau chuyển xám trắng, viền nâu [17].
    - Xuất hiện hạch nấm hình tròn dẹt màu nâu [18].
    \n**3. Biện pháp phòng trừ:**
    - **Canh tác:** Vệ sinh đồng ruộng, dọn sạch cỏ bờ (nơi nấm trú ẩn) [10].
    - **Thuốc đặc trị:** *Hexaconazole* (Anvil 5SC), *Validamycin* (Validacin), *Pencycuron*, *Azoxystrobin* [11], [19].
    - **Sinh học:** Sử dụng nấm đối kháng *Trichoderma* [20], [21].""",

    "lem lép hạt": """⚫ **BỆNH LEM LÉP HẠT** [22], [23]
    \n**1. Nguyên nhân:** Do phức hợp nấm (*Fusarium, Curvularia*...) và vi khuẩn (*Pseudomonas glumae*) tấn công giai đoạn trổ [24].
    \n**2. Dấu hiệu:**
    - Hạt lúa có đốm nâu, đen, tím hoặc biến màu xám ngoét [22].
    - Hạt lửng hoặc lép hoàn toàn, gạo đục, dễ gãy [23].
    \n**3. Biện pháp phòng trừ:**
    - **Thời điểm vàng:** Phun thuốc 2 lần: (1) Khi lúa trổ lẹt xẹt 5% và (2) Khi lúa trổ đều [24], [25].
    - **Thuốc đặc trị:** *Difenoconazole*, *Propiconazole* (Tilt Super), *Azoxystrobin* + *Difenoconazole* (Amistar Top) [11], [12].""",

    # --- NHÓM BỆNH DO VI KHUẨN ---
    "bạc lá": """🦠 **BỆNH BẠC LÁ (CHÁY BÌA LÁ)** [26], [27]
    \n**1. Tác nhân:** Vi khuẩn *Xanthomonas oryzae*. Lây lan nhanh qua vết thương cơ giới sau mưa bão [28].
    \n**2. Dấu hiệu nhận biết:**
    - Vết bệnh lan từ chóp lá dọc theo hai bên mép lá [29].
    - Vết bệnh màu vàng hoặc trắng xám, ranh giới vết bệnh gợn sóng [26].
    - Sáng sớm có giọt dịch vi khuẩn màu vàng đục trên vết bệnh [26], [30].
    \n**3. Biện pháp phòng trừ:**
    - **Cấp bách:** Khi bệnh chớm xuất hiện, **ngưng bón đạm**, rút nước để khô ruộng 2-3 ngày [31], [32].
    - **Thuốc đặc trị:** *Bismerthiazol* (Xanthomix), *Oxolinic acid* (Starner), *Bronopol*, *Kasugamycin* [11], [33].
    - **Lưu ý:** Không phun thuốc kèm phân bón lá khi lúa đang bệnh [27].""",

    # --- NHÓM BỆNH DO VIRUS ---
    "vàng lùn": """⚠️ **BỆNH VÀNG LÙN & LÙN XOẮN LÁ** [34], [35]
    \n**1. Tác nhân:** Virus do **Rầy nâu** truyền bệnh. Không có thuốc đặc trị virus [36].
    \n**2. Dấu hiệu nhận biết:**
    - **Vàng lùn:** Lá lúa chuyển vàng từ chóp xuống, cây thấp lùn, đẻ nhánh kém, rễ thối [37].
    - **Lùn xoắn lá:** Lá xanh đậm, ngắn, xoăn tít (như lò xo), gân lá sưng, không trổ bông được [38], [37].
    \n**3. Biện pháp quản lý:**
    - **Tiêu hủy:** Nhổ bỏ, vùi sâu bụi lúa bệnh để cắt nguồn lây [39].
    - **Trừ môi giới:** Phòng trừ rầy nâu triệt để bằng *Pymetrozine*, *Buprofezin* [40].
    - **Giống:** Chọn giống kháng rầy, gieo sạ "né rầy" [39].""",

    # --- CÔN TRÙNG HẠI ---
    "rầy nâu": """🦗 **RẦY NÂU (Brown Planthopper)** [41]
    \n**1. Tác hại:** Chích hút nhựa làm lúa "cháy rầy", truyền bệnh vàng lùn [41].
    \n**2. Phòng trừ:**
    - Thăm đồng thường xuyên, vạch gốc lúa kiểm tra.
    - Phun thuốc khi mật độ > 3 con/tép [42].
    - **Thuốc:** *Pymetrozine* (Chess), *Buprofezin* (Applaud), *Nitenpyram* [40].
    - Áp dụng IPM, bảo vệ thiên địch (nhện, bọ xít nước) [43].""",

    "sâu cuốn lá": """🐛 **SÂU CUỐN LÁ NHỎ** [44], [45]
    \n**1. Dấu hiệu:** Sâu nhả tơ cuốn dọc lá lúa thành ống, ăn phần thịt lá để lại lớp biểu bì trắng [44].
    \n**2. Ngưỡng phòng trừ:** Mật độ 20-50 con/m2 (giai đoạn đẻ nhánh-làm đòng) [46].
    \n**3. Thuốc đặc trị:** *Indoxacarb*, *Chlorantraniliprole* (Virtako), *Emamectin benzoate* [40], [47]. Phun khi sâu còn non (tuổi 1-2).""",

    # --- KỸ THUẬT CANH TÁC ---
    "bón phân": """🌱 **KỸ THUẬT BÓN PHÂN CÂN ĐỐI (Theo quy trình 3 Giảm 3 Tăng)** [48], [10]
    \n**Nguyên tắc:** "Nặng đầu, nhẹ cuối".
    1. **Bón lót:** 100% Lân + 30% Đạm.
    2. **Bón thúc 1 (7-10 NSS):** 30% Đạm + 30% Kali.
    3. **Bón thúc 2 (18-22 NSS):** 40% Đạm còn lại.
    4. **Bón đón đòng (40-45 NSS):** 70% Kali còn lại (tùy màu lá lúa mà bổ sung đạm ít hay nhiều - bảng so màu lá) [49].
    \n⚠️ **Lưu ý:** Thừa đạm gây đạo ôn, bạc lá, đổ ngã.""",
    
    "ipm": """🛡️ **QUẢN LÝ DỊCH HẠI TỔNG HỢP (IPM)** [2], [50], [51]
    \n**5 Nguyên tắc cơ bản:**
    1. Trồng cây khỏe (giống tốt, đất tốt).
    2. Bảo vệ thiên địch (không phun thuốc bừa bãi).
    3. Thăm đồng thường xuyên.
    4. Nông dân trở thành chuyên gia.
    5. Phòng trừ dịch hại đúng cách (chỉ phun khi tới ngưỡng kinh tế) [51].""",
}

# Mapping từ khóa bổ sung để tìm kiếm tốt hơn
KEYWORD_MAPPING = {
    "đốm sọc": "bạc lá",
    "cháy bìa": "bạc lá",
    "tiêm lửa": "đốm nâu",
    "rầy": "rầy nâu",
    "sâu": "sâu cuốn lá",
    "lúa von": "đạo ôn",
    "bù lạch": "bọ trĩ",
    "thuốc sâu": "sâu cuốn lá",
    "phân bón": "bón phân"
}

def tim_tra_loi(cau_hoi):
    cau_hoi = cau_hoi.lower()
    
    # Kiểm tra mapping từ khóa
    for key, mapped_value in KEYWORD_MAPPING.items():
        if key in cau_hoi:
            cau_hoi += " " + mapped_value
            
    # Tìm kiếm trong cơ sở dữ liệu
    for key, value in KIEN_THUC.items():
        if key in cau_hoi:
            return value
            
    return """🌾 **BÁC SĨ LÚA CÓ THỂ TƯ VẤN VỀ:**
    \n🦠 **Bệnh hại:** Đạo ôn, Bạc lá (cháy bìa), Khô vằn, Lem lép hạt, Vàng lùn.
    \n🐛 **Sâu hại:** Rầy nâu, Sâu cuốn lá, Bọ trĩ.
    \n🧪 **Thuốc BVTV:** Tên hoạt chất, cách dùng.
    \n🌱 **Kỹ thuật:** Bón phân, IPM.
    \n**Bà con hãy đặt câu hỏi cụ thể. Ví dụ: "Thuốc trị đạo ôn là gì?" hoặc "Cách phòng rầy nâu"**"""

# ==============================================================================
# 2. DỮ LIỆU CHẨN ĐOÁN HÌNH ẢNH (Mapping từ Model Class -> Tiếng Việt)
# ==============================================================================

DATA_BENH = {
    "Bacterial Leaf Blight": {
        "ten": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "trieu_chung": "Vết bệnh lan dọc mép lá, màu vàng hoặc trắng xám, có giọt dịch vi khuẩn [26].",
        "nguyen_nhan": "Vi khuẩn *Xanthomonas oryzae*. Do mưa bão, thừa đạm [53].",
        "thuoc": ["Kasumin 2SL", "Starner 20WP", "Totan 200WP", "Xanthomix 20WP"],
        "loi_khuyen": "Rút nước, tháo nước khô ruộng 2-3 ngày. Ngưng bón đạm [33]."
    },
    "Blast": {
        "ten": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "trieu_chung": "Vết hình thoi (mắt én), tâm xám trắng, viền nâu [5], [7].",
        "nguyen_nhan": "Nấm *Pyricularia oryzae*. Sương mù nhiều, ẩm độ cao [7].",
        "thuoc": ["Beam 75WP (Tricyclazole)", "Filia 525SE", "Fuji-one 40EC", "Ninja 35EC"],
        "loi_khuyen": "Giữ nước ruộng. Không được để ruộng khô. Phun thuốc đặc trị nấm [13]."
    },
    "Brown Spot": {
        "ten": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "trieu_chung": "Vết tròn nhỏ màu nâu như hạt mè, lá vàng [54].",
        "nguyen_nhan": "Nấm *Bipolaris oryzae*. Thường do đất thiếu dinh dưỡng, phèn [55].",
        "thuoc": ["Tilt Super 300EC", "Anvil 5SC", "Nevado"],
        "loi_khuyen": "Bón bổ sung Kali, Silic, vôi bột để cải tạo đất [56]."
    },
    "Tungro": {
        "ten": "BỆNH VÀNG LÙN/LÙN XOẮN LÁ",
        "trieu_chung": "Lá vàng cam, cây thấp lùn, lá xoắn [38].",
        "nguyen_nhan": "Virus do Rầy nâu truyền [57].",
        "thuoc": ["Không có thuốc trị virus. Phun thuốc trừ rầy: Chess, Applaud"],
        "loi_khuyen": "Nhổ bỏ cây bệnh. Quản lý rầy nâu chặt chẽ [39]."
    }
}

# Mapping các tên class khác nhau từ model về chuẩn
DATA_BENH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"},
    "Rice Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"},
    "Hispa": {"ref": "Blast"}
})

def ve_bbox(img, predictions):
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
        
    for i, pred in enumerate(predictions[:3]):
        conf = pred['confidence'] * 100
        if conf < 40:
            continue
        
        label = f"{pred['class']}: {conf:.1f}%"
        
        x = pred.get('x', 0)
        y = pred.get('y', 0)
        w = pred.get('width', 100)
        h = pred.get('height', 100)
        
        x0 = x - w/2
        y0 = y - h/2
        x1 = x + w/2
        y1 = y + h/2
        
        draw.rectangle([x0, y0, x1, y1], outline="red", width=3)
        
        bbox = draw.textbbox((x0, y0-30), label, font=font)
        draw.rectangle(bbox, fill=(255, 0, 0))
        draw.text((x0, y0-30), label, fill="white", font=font)
        
    return img

# ==============================================================================
# 3. GIAO DIỆN ỨNG DỤNG
# ==============================================================================

st.markdown("<h1 style='text-align: center;'>🌾 BÁC SĨ LÚA AI 4.0</h1>", unsafe_allow_html=True)
st.caption("Chẩn đoán bệnh lúa qua ảnh & Tư vấn kỹ thuật canh tác (Dữ liệu cập nhật 2025)")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🔍 CHẨN ĐOÁN HÌNH ẢNH", "💬 CHAT VỚI CHUYÊN GIA", "📋 LỊCH SỬ"])

# --- TAB 1: CHẨN ĐOÁN ---
with tab1:
    col_l, col_r = st.columns([1, 1.3])
    
    with col_l:
        st.subheader("1. Tải ảnh lá lúa bị bệnh")
        st.info("💡 Mẹo: Chụp rõ vết bệnh, tránh bị chói sáng.")
        input_type = st.radio("Chọn nguồn ảnh:", ["Tải ảnh từ máy", "Chụp trực tiếp"], horizontal=True)
        
        file = None
        if input_type == "Chụp trực tiếp":
            file = st.camera_input("Chụp ảnh lá lúa")
        else:
            file = st.file_uploader("Chọn file ảnh (jpg, png)", type=['jpg','png','jpeg'])

        if file:
            img = Image.open(file).convert("RGB")
            st.image(img, use_container_width=True, caption="Ảnh của bạn")
            
            if st.button("🚀 PHÂN TÍCH BỆNH", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("Đang phân tích hình ảnh..."):
                        img.save("process.jpg")
                        
                        try:
                            client = InferenceHTTPClient(
                                api_url="https://detect.roboflow.com",
                                api_key="8tf2UvcnEv8h80bV2G0Q"
                            )
                            res = client.infer("process.jpg", model_id="rice-leaf-disease-twtlz/1")
                            preds = res.get('predictions', [])
                            
                            if preds:
                                # Sửa lỗi: sorted() trả về list, cần lấy phần tử đầu
                                top_pred = sorted(preds, key=lambda x: x['confidence'], reverse=True)[0]
                                class_name = top_pred['class']
                                confidence = top_pred['confidence'] * 100
                                
                                img_annotated = ve_bbox(img.copy(), preds)
                                st.image(img_annotated, caption=f"Kết quả AI phát hiện: {class_name}")
                                
                                benh_info = DATA_BENH.get(class_name)
                                if benh_info and "ref" in benh_info:
                                    benh_info = DATA_BENH[benh_info["ref"]]
                                
                                if benh_info:
                                    st.success(f"### CHẨN ĐOÁN: {benh_info['ten']} (Độ tin cậy: {confidence:.1f}%)")
                                    
                                    st.markdown(f"""
                                    #### 📋 Triệu chứng điển hình:
                                    {benh_info['trieu_chung']}
                                    
                                    #### 🧬 Nguyên nhân:
                                    {benh_info['nguyen_nhan']}
                                    
                                    #### 🛡️ Giải pháp xử lý [IPM]:
                                    * **Biện pháp canh tác:** {benh_info['loi_khuyen']}
                                    * **Thuốc BVTV đề xuất:** {', '.join(benh_info['thuoc'])}
                                    """)
                                    
                                    st.session_state.history.append({
                                        "time": datetime.now().strftime("%d/%m %H:%M"),
                                        "benh": benh_info['ten'],
                                        "conf": confidence
                                    })
                                else:
                                    st.warning(f"Phát hiện '{class_name}' nhưng chưa có dữ liệu chi tiết tiếng Việt.")
                            else:
                                st.info("✅ Cây lúa có vẻ khỏe mạnh hoặc không phát hiện bệnh trong cơ sở dữ liệu.")
                                
                        except Exception as e:
                            st.error(f"Lỗi kết nối AI: {str(e)}. Vui lòng kiểm tra lại API key hoặc mạng.")

# --- TAB 2: CHATBOT ---
with tab2:
    st.subheader("💬 Trợ lý ảo Nông Nghiệp")
    st.markdown("*Hỏi đáp về kỹ thuật trồng lúa, phòng trừ sâu bệnh, thuốc BVTV (Dữ liệu từ Cục BVTV & Viện lúa ĐBSCL)*")
    
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Nhập câu hỏi của bạn (VD: lúa bị cháy lá dùng thuốc gì?)"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        response = tim_tra_loi(prompt)
        
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# --- TAB 3: LỊCH SỬ ---
with tab3:
    st.subheader("📋 Nhật ký chẩn đoán")
    if st.session_state.history:
        for i, h in enumerate(reversed(st.session_state.history)):
            st.markdown(f"""
            **{i+1}. {h['time']}** - <span style='color:red'>{h['benh']}</span> - Độ tin cậy: {h['conf']:.1f}%
            """, unsafe_allow_html=True)
            st.divider()
    else:
        st.caption("Chưa có dữ liệu chẩn đoán nào.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: grey;'>Ứng dụng được phát triển dựa trên dữ liệu Nông nghiệp Việt Nam 2024-2025</div>", unsafe_allow_html=True)
