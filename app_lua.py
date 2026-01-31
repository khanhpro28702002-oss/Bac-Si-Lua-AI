import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Cấu hình trang
st.set_page_config(page_title="Chuyên Gia Bệnh Lúa AI", page_icon="🌾", layout="wide")

# CSS tùy chỉnh giao diện
st.markdown("""
<style>
    .main {background-color: #f4f6f9;}
    h1 {color: #1b5e20; text-align: center;}
    .stChatInput {border-radius: 20px;}
    div.stMarkdown h3 {color: #2e7d32; border-bottom: 2px solid #a5d6a7; padding-bottom: 10px;}
    div.stMarkdown h4 {color: #d32f2f; margin-top: 20px;}
    .reportview-container .markdown-text-container {font-family: 'Arial';}
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []

# ==============================================================================
# 1. CƠ SỞ DỮ LIỆU TRI THỨC BỆNH HẠI (Chi tiết chuyên sâu)
# ==============================================================================

KIEN_THUC_BENH = {
    "đạo ôn": """🔥 **BỆNH ĐẠO ÔN (CHÁY LÁ)**
    \n**1. Tác nhân & Điều kiện:**
    - Do nấm *Pyricularia oryzae* gây ra. Nấm tiết độc tố Pyricularin kìm hãm hô hấp cây.
    - Phát triển mạnh khi trời âm u, sương mù nhiều, ẩm độ cao, nhiệt độ mát (20-28°C), chênh lệch nhiệt độ ngày đêm lớn.
    - Ruộng bón thừa đạm, sạ dày là điều kiện lý tưởng cho nấm bùng phát.
    \n**2. Triệu chứng nhận biết:**
    - **Trên lá:** Vết bệnh ban đầu là chấm nhỏ xanh xám, sau chuyển thành hình thoi (mắt én), tâm màu xám trắng, viền nâu đậm. Nhiều vết liên kết làm lá cháy khô (cháy đạo ôn).
    - **Trên cổ bông:** Vết nâu xám hoặc đen bao quanh cổ bông, làm tắc mạch dẫn dinh dưỡng, khiến bông bạc trắng (nếu bị sớm) hoặc gãy cổ bông, hạt lép lửng.
    - **Trên đốt thân:** Vết nâu bao quanh đốt, làm đốt teo lại, cây dễ gãy gục.
    \n**3. Biện pháp phòng trừ:**
    - **Canh tác:** Không bón thừa đạm, bón cân đối N-P-K. Khi bệnh chớm xuất hiện phải **ngưng bón đạm** và thuốc kích thích sinh trưởng ngay. Giữ nước ruộng, không để ruộng khô hạn.
    - **Thuốc đặc trị:** Phun các hoạt chất *Tricyclazole* (Beam 75WP, Trizole), *Isoprothiolane* (Fuji-one 40EC), *Fenoxanil*, *Azoxystrobin* (Amistar Top).
    - **Lưu ý:** Với đạo ôn cổ bông, bắt buộc phun phòng 2 lần: (1) Khi lúa trổ lẹt xẹt 5% và (2) Khi lúa trổ đều.""",

    "khô vằn": """🍂 **BỆNH KHÔ VẰN (ĐỐM VẰN)**
    \n**1. Tác nhân & Điều kiện:**
    - Do nấm đất *Rhizoctonia solani* gây ra. Nấm tồn tại dạng hạch nấm trong đất và rơm rạ rất lâu.
    - Phát triển mạnh ở nhiệt độ cao (28-32°C), ẩm độ cao (96-100%), ruộng sạ dày, rậm rạp, bón nhiều đạm.
    \n**2. Triệu chứng nhận biết:**
    - Xuất hiện đầu tiên ở bẹ lá sát mặt nước. Vết bệnh hình bầu dục hoặc đám mây, màu lục tối hoặc xám nhạt, sau chuyển sang vằn da hổ (viền nâu, tâm xám trắng).
    - Bệnh lan dần lên lá đòng và bông. Xuất hiện các hạch nấm hình tròn dẹt (như hạt cải), ban đầu trắng sau chuyển nâu rơi xuống nước lây lan.
    \n**3. Biện pháp phòng trừ:**
    - **Canh tác:** Vệ sinh đồng ruộng, dọn sạch tàn dư sau thu hoạch. Cày lật đất để vùi hạch nấm. Sạ thưa hợp lý.
    - **Thuốc đặc trị:** Sử dụng các hoạt chất *Hexaconazole* (Anvil 5SC, VK-Hexa), *Validamycin* (Validacin, Valivithaco), *Pencycuron*, *Propiconazole* (Tilt Super).
    - **Lưu ý:** Phun thuốc tập trung vào phần gốc lúa nơi bệnh phát sinh.""",

    "bạc lá": """🦠 **BỆNH BẠC LÁ (CHÁY BÌA LÁ)**
    \n**1. Tác nhân & Điều kiện:**
    - Do vi khuẩn *Xanthomonas oryzae* gây ra.
    - Vi khuẩn xâm nhập qua khí khổng hoặc vết thương cơ giới (do mưa to gió lớn va đập lá).
    - Bệnh nặng khi bón thừa đạm, sau các đợt mưa bão, gió lốc.
    \n**2. Triệu chứng nhận biết:**
    - Vết bệnh lan từ chóp lá hoặc hai bên mép lá vào trong.
    - Vết bệnh có màu xanh tái (úng nước) sau chuyển sang vàng hoặc trắng xám (bạc lá). Ranh giới giữa phần bệnh và phần khỏe gợn sóng.
    - Sáng sớm thường có giọt dịch vi khuẩn (keo vi khuẩn) màu vàng đục ở mép vết bệnh.
    \n**3. Biện pháp phòng trừ:**
    - **Nguyên tắc vàng:** Khi bệnh xuất hiện, TUYỆT ĐỐI KHÔNG bón đạm, không phun phân bón lá hay thuốc kích thích.
    - **Quản lý nước:** Rút nước để ruộng khô ráo 2-3 ngày nhằm hạn chế vi khuẩn lây lan trong nước.
    - **Thuốc đặc trị:** Vi khuẩn rất khó trị, cần phun sớm các hoạt chất kháng khuẩn như *Bismerthiazol* (Xanthomix), *Oxolinic acid* (Starner), *Bronopol* (Totan), *Kasugamycin* (Kasumin), *Ningnanmycin*.""",

    "lem lép hạt": """⚫ **BỆNH LEM LÉP HẠT**
    \n**1. Nguyên nhân phức hợp:**
    - Do Nấm: *Fusarium, Curvularia, Alternaria, Bipolaris*... gây vết đốm nâu, tím, đen.
    - Do Vi khuẩn: *Burkholderia glumae* (gây lép vàng, thối hạt), *Xanthomonas* (thối đen hạt).
    - Điều kiện: Mưa nhiều, độ ẩm cao giai đoạn trổ bông.
    \n**2. Triệu chứng:**
    - Vỏ trấu bị đổi màu (nâu, đen, tím, xám). Hạt lúa bên trong bị lửng hoặc lép hoàn toàn.
    - **Lép vàng:** Vỏ trấu không biến màu hoặc vàng rơm nhưng hạt lép kẹp, nhánh gié đứng thẳng (bắn máy bay).
    - **Than vàng:** Khối bào tử nấm màu vàng cam (như nhung) bao phủ hạt, sau chuyển xanh đen.
    \n**3. Giải pháp phòng trị:**
    - Đây là bệnh cần **phòng** hơn trị. Phun thuốc vào 2 thời điểm cực trọng:
        1. Lúa trổ lẹt xẹt (khoảng 5%).
        2. Lúa trổ đều (sau lần 1 khoảng 7 ngày).
    - **Thuốc phối hợp:** Nên dùng thuốc hỗn hợp trừ nấm và khuẩn.
        - Trừ nấm: *Azoxystrobin + Difenoconazole* (Amistar Top), *Propiconazole* (Tilt Super), *Tebuconazole*.
        - Trừ khuẩn: *Kasugamycin, Bismerthiazol*.""",

    "vàng lùn": """⚠️ **BỆNH VÀNG LÙN & LÙN XOẮN LÁ (VIRUS)**
    \n**1. Tác nhân:**
    - Bệnh do Virus gây ra (Virus lùn xoắn lá RRSV, Virus vàng lùn RGSV).
    - **Môi giới truyền bệnh:** Rầy nâu (*Nilaparvata lugens*). Rầy chích hút cây bệnh rồi bay sang chích cây khỏe để truyền virus.
    \n**2. Triệu chứng:**
    - **Vàng lùn:** Lá lúa chuyển vàng từ chóp xuống, cây thấp lùn, đẻ nhánh kém, rễ thối đen. Các lá xòe ngang.
    - **Lùn xoắn lá:** Cây lùn, lá xanh đậm, ngắn, bị xoăn tít (như lò xo), gân lá sưng (có bướu sọc), lúa không trổ bông được hoặc trổ bị nghẹn, hạt lép.
    \n**3. Giải pháp quản lý (Không có thuốc trị virus):**
    - **Tiêu hủy:** Nhổ bỏ và vùi sâu những khóm lúa bị bệnh để cắt nguồn lây.
    - **Diệt môi giới:** Phòng trừ rầy nâu triệt để. Sử dụng thuốc trừ rầy như *Pymetrozine* (Chess), *Nitenpyram*, *Dinotefuran*, *Buprofezin*.
    - **Giống:** Chọn giống kháng rầy, né rầy.""",

    "đốm sọc": """📏 **BỆNH ĐỐM SỌC VI KHUẨN**
    \n**1. Tác nhân:** Vi khuẩn *Xanthomonas oryzicola*.
    \n**2. Triệu chứng:**
    - Xuất hiện các sọc nhỏ, ngắn, chạy dọc giữa các gân lá.
    - Ban đầu vết sọc xanh trong (giọt dầu), sau chuyển màu nâu đỏ.
    - Khi ẩm ướt, trên bề mặt sọc tiết ra các giọt dịch vi khuẩn màu vàng đục (như trứng cá).
    \n**3. Phòng trị:**
    - Tương tự bệnh Bạc lá vi khuẩn. Sử dụng các thuốc gốc đồng hoặc kháng sinh như *Kasugamycin, Bismerthiazol*.
    - Tránh làm rách lá lúa trong quá trình chăm sóc.""",

    "lúa von": """🎋 **BỆNH LÚA VON (MẠ ĐỰC)**
    \n**1. Tác nhân:** Nấm *Fusarium moniliforme*. Bệnh chủ yếu lây qua hạt giống.
    \n**2. Triệu chứng:**
    - Cây lúa phát triển chiều cao vọt, cao hơn hẳn so với cây bình thường.
    - Thân mảnh khảnh, lá xanh nhạt hoặc vàng gạch cua, giòn, dễ gãy.
    - Cây thường chết sớm hoặc nếu sống thì trổ bông hạt lép. Ở đốt thân có thể thấy lớp phấn nấm màu hồng.
    \n**3. Phòng trị:**
    - **Xử lý hạt giống:** Đây là biện pháp quan trọng nhất. Ngâm ủ hạt giống với nước nóng 54°C hoặc thuốc xử lý giống như *Thiram, Benomyl*.
    - Nhổ bỏ cây bệnh trên ruộng và tiêu hủy.""",

    "nghẹt rễ": """🥀 **BỆNH NGHẸT RỄ (BỆNH SINH LÝ)**
    \n**1. Nguyên nhân:** Do đất bị ngộ độc hữu cơ (rơm rạ chưa phân hủy), đất thiếu oxy, tích tụ khí độc H2S, CH4.
    \n**2. Triệu chứng:**
    - Cây lúa sinh trưởng kém, lá vàng đỏ, khô từ chóp lá xuống.
    - Nhổ lên thấy rễ thối đen, không có rễ trắng mới, có mùi hôi tanh.
    \n**3. Khắc phục:**
    - Tháo cạn nước, phơi ruộng nứt chân chim để đất thoáng khí.
    - Bón vôi bột (20-25kg/sào) kết hợp làm cỏ sục bùn.
    - Phun phân bón lá chứa Lân (P) và Kali (K) để giải độc. Không bón đạm lúc này.""",
    
    "đốm nâu": """🟤 **BỆNH ĐỐM NÂU (TIÊM LỬA)**
    \n**1. Tác nhân:** Nấm *Bipolaris oryzae*. Thường xuất hiện trên đất phèn, đất nghèo dinh dưỡng (thiếu Kali, Silic).
    \n**2. Triệu chứng:**
    - Vết bệnh hình tròn hoặc bầu dục, màu nâu, kích thước như hạt mè.
    - Xuất hiện rải rác trên lá, vỏ trấu.
    \n**3. Phòng trị:**
    - Cải tạo đất, bón vôi, bón đầy đủ Kali và Silic để lá dày, cứng.
    - Phun các thuốc trừ nấm phổ rộng như *Propiconazole, Iprodione*."""
}

# Mapping từ khóa để tìm kiếm tốt hơn
KEYWORD_MAPPING = {
    "cháy lá": "đạo ôn",
    "cổ bông": "đạo ôn",
    "thối cổ gié": "đạo ôn",
    "đốm vằn": "khô vằn",
    "lở cổ rễ": "khô vằn",
    "cháy bìa": "bạc lá",
    "bìa lá": "bạc lá",
    "lép hạt": "lem lép hạt",
    "lép vàng": "lem lép hạt",
    "đen hạt": "lem lép hạt",
    "xoăn lá": "vàng lùn",
    "lùn lúa": "vàng lùn",
    "mạ đực": "lúa von",
    "ngộ độc hữu cơ": "nghẹt rễ",
    "tiêm lửa": "đốm nâu"
}

def tim_tra_loi(cau_hoi):
    cau_hoi = cau_hoi.lower()
    
    # Kiểm tra mapping từ khóa
    search_terms = [cau_hoi]
    for key, mapped_value in KEYWORD_MAPPING.items():
        if key in cau_hoi:
            search_terms.append(mapped_value)
            
    # Tìm kiếm trong cơ sở dữ liệu
    for term in search_terms:
        for key, value in KIEN_THUC_BENH.items():
            if key in term:
                return value
            
    return """⚠️ **Bác Sĩ Lúa chưa rõ câu hỏi của bạn.**
    \nTôi chuyên sâu về các bệnh hại lúa. Bạn hãy thử hỏi về:
    \n- Bệnh Đạo ôn (Cháy lá)
    \n- Bệnh Khô vằn (Đốm vằn)
    \n- Bệnh Bạc lá (Cháy bìa lá)
    \n- Bệnh Lem lép hạt
    \n- Bệnh Vàng lùn, Lùn xoắn lá
    \n- Bệnh Lúa von, Đốm nâu...
    \n*Ví dụ: "Triệu chứng bệnh đạo ôn là gì?" hoặc "Thuốc trị bạc lá vi khuẩn"*"""

# ==============================================================================
# 2. DỮ LIỆU CHẨN ĐOÁN HÌNH ẢNH
# ==============================================================================

DATA_HINH_ANH = {
    "Bacterial Leaf Blight": {
        "ten": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "trieu_chung": "Vết bệnh là các sọc thấm nước ở mép lá, sau chuyển sang vàng hoặc trắng xám. Rìa vết bệnh lượn sóng. Thường thấy giọt dịch vi khuẩn vào buổi sáng.",
        "nguyen_nhan": "Vi khuẩn *Xanthomonas oryzae*. Lây lan mạnh qua mưa gió, vết thương cơ giới.",
        "giai_phap": "Ngưng bón đạm. Rút nước khô ruộng. Phun thuốc: Bismerthiazol (Xanthomix), Oxolinic acid (Starner), Kasugamycin."
    },
    "Blast": {
        "ten": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "trieu_chung": "Vết bệnh hình thoi (mắt én), tâm màu xám trắng, viền nâu đậm. Nếu nặng lá bị cháy khô.",
        "nguyen_nhan": "Nấm *Pyricularia oryzae*. Do trời âm u, sương mù, thừa đạm.",
        "giai_phap": "Giữ nước ruộng. Phun: Tricyclazole (Beam), Isoprothiolane (Fuji-one), Azoxystrobin."
    },
    "Brown Spot": {
        "ten": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "trieu_chung": "Nhiều đốm tròn nhỏ màu nâu như hạt mè rải rác trên lá.",
        "nguyen_nhan": "Nấm *Bipolaris oryzae*. Thường do đất thiếu dinh dưỡng, phèn, thiếu Kali/Silic.",
        "giai_phap": "Bón bổ sung Kali, Silic, vôi. Phun thuốc: Tilt Super, Anvil."
    },
    "Tungro": {
        "ten": "BỆNH DO VIRUS (VÀNG LÙN/TUNGRO)",
        "trieu_chung": "Lá biến vàng cam từ chóp, cây thấp lùn, lá xòe ngang hoặc xoắn.",
        "nguyen_nhan": "Virus do Rầy nâu hoặc Rầy xanh truyền bệnh.",
        "giai_phap": "Nhổ bỏ cây bệnh. Phun thuốc trừ Rầy môi giới (Chess, Applaud, Bassa)."
    }
}

# Mapping các label khác từ model AI về chuẩn
DATA_HINH_ANH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"},
    "Rice Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"},
    "Hispa": {"ref": "Blast"} # Xử lý tạm thời nếu model nhận diện sai
})

def ve_bbox(img, predictions):
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
        
    for i, pred in enumerate(predictions[:3]):
        conf = pred['confidence'] * 100
        if conf < 40: continue 
        
        label = f"{pred['class']}: {conf:.1f}%"
        x = pred.get('x', 0)
        y = pred.get('y', 0)
        w = pred.get('width', 100)
        h = pred.get('height', 100)
        
        x0 = x - w/2
        y0 = y - h/2
        x1 = x + w/2
        y1 = y + h/2
        
        draw.rectangle([x0, y0, x1, y1], outline="#ff0000", width=4)
        bbox = draw.textbbox((x0, y0-35), label, font=font)
        draw.rectangle(bbox, fill=(255, 0, 0))
        draw.text((x0, y0-35), label, fill="white", font=font)
        
    return img

# ==============================================================================
# 3. GIAO DIỆN ỨNG DỤNG
# ==============================================================================

st.markdown("<h1 style='text-align: center;'>🌾 BÁC SĨ LÚA - CHUYÊN GIA BỆNH HỌC</h1>", unsafe_allow_html=True)
st.caption("Hệ thống chẩn đoán và tư vấn phòng trừ bệnh hại lúa (Dữ liệu cập nhật 2025 - Không bao gồm sâu hại)")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🔍 CHẨN ĐOÁN QUA ẢNH", "💬 CHAT VỚI CHUYÊN GIA", "📋 NHẬT KÝ"])

# --- TAB 1: CHẨN ĐOÁN ---
with tab1:
    col_l, col_r = st.columns([1, 1.2])
    
    with col_l:
        st.subheader("📸 Tải ảnh lá lúa bị bệnh")
        st.info("Hệ thống nhận diện tốt nhất các bệnh: Đạo ôn, Bạc lá, Đốm nâu.")
        input_type = st.radio("Nguồn ảnh:", ["Tải lên", "Chụp ảnh"], horizontal=True)
        
        file = None
        if input_type == "Chụp ảnh":
            file = st.camera_input("Chụp ảnh lá bệnh")
        else:
            file = st.file_uploader("Chọn ảnh (jpg, png)", type=['jpg','png','jpeg'])

        if file:
            img = Image.open(file).convert("RGB")
            st.image(img, use_column_width=True, caption="Ảnh đầu vào")
            
            if st.button("PHÂN TÍCH NGAY", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("Đang phân tích tế bào vết bệnh..."):
                        img.save("temp.jpg")
                        try:
                            # API Key mẫu (Thay bằng key của bạn nếu cần)
                            client = InferenceHTTPClient(
                                api_url="https://detect.roboflow.com",
                                api_key="8tf2UvcnEv8h80bV2G0Q"
                            )
                            res = client.infer("temp.jpg", model_id="rice-leaf-disease-twtlz/1")
                            preds = res.get('predictions', [])
                            
                            if preds:
                                top_pred = sorted(preds, key=lambda x: x['confidence'], reverse=True)
                                class_name = top_pred['class']
                                confidence = top_pred['confidence'] * 100
                                
                                img_annotated = ve_bbox(img.copy(), preds)
                                st.image(img_annotated, caption=f"Phát hiện: {class_name}")
                                
                                # Lấy thông tin bệnh
                                info = DATA_HINH_ANH.get(class_name)
                                if info and "ref" in info:
                                    info = DATA_HINH_ANH[info["ref"]]
                                
                                if info:
                                    st.success(f"### KẾT QUẢ: {info['ten']}")
                                    st.markdown(f"**Độ tin cậy:** {confidence:.1f}%")
                                    st.error("🛑 **Triệu chứng:** " + info['trieu_chung'])
                                    st.warning("🧬 **Nguyên nhân:** " + info['nguyen_nhan'])
                                    st.info("🛡️ **Giải pháp xử lý:** " + info['giai_phap'])
                                    
                                    st.session_state.history.append({
                                        "time": datetime.now().strftime("%d/%m %H:%M"),
                                        "result": info['ten']
                                    })
                                else:
                                    st.warning(f"Phát hiện '{class_name}' nhưng chưa có dữ liệu chi tiết.")
                            else:
                                st.success("✅ Không phát hiện dấu hiệu bệnh lý rõ ràng trên lá.")
                                
                        except Exception as e:
                            st.error("Lỗi kết nối server AI. Vui lòng thử lại sau.")

# --- TAB 2: CHATBOT ---
with tab2:
    st.subheader("💬 Hỏi đáp bệnh hại lúa")
    st.markdown("*Chuyên sâu về: Đạo ôn, Khô vằn, Bạc lá, Lem lép hạt, Lúa von, Vàng lùn...*")
    
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("VD: Lúa bị cháy chóp lá là bệnh gì?"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        response = tim_tra_loi(prompt)
        
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# --- TAB 3: LỊCH SỬ ---
with tab3:
    st.subheader("📋 Lịch sử chẩn đoán")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history)):
            st.text(f"{i+1}. {item['time']} - {item['result']}")
    else:
        st.caption("Chưa có dữ liệu.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Dữ liệu tổng hợp từ Cục Bảo vệ Thực vật & Các tài liệu khuyến nông 2024-2025</div>", unsafe_allow_html=True)