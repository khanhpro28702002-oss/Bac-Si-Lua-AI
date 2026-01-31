import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image
import numpy as np
import cv2
from datetime import datetime
from gtts import gTTS
import io
from fpdf import FPDF
import time
import requests
from streamlit_js_eval import get_geolocation
import base64

# ==============================================================================
# 1. CẤU HÌNH HỆ THỐNG & API
# ==============================================================================
MY_API_KEY = "8tf2UvcnEv8h80bV2G0Q"
MY_MODEL_ID = "rice-leaf-disease-twtlz/1"

st.set_page_config(
    page_title="Hệ Thống Bác Sĩ Lúa 4.0",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo bộ nhớ tạm (Session State)
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [
        {"role": "assistant", "content": "🌾 Chào bà con! Tôi là Trợ lý AI nông nghiệp. Bà con cần hỏi về bệnh gì, thuốc gì hay thời tiết hôm nay thế nào?"}
    ]

# ==============================================================================
# 2. CƠ SỞ DỮ LIỆU BỆNH HỌC & THUỐC (CHI TIẾT NHẤT)
# ==============================================================================
TU_DIEN_BENH = {
    "Bacterial Leaf Blight": {
        "vn_name": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "trieu_chung": "Vết bệnh bắt đầu từ chóp lá lan dần xuống dọc theo mép lá. Vết bệnh có màu vàng hoặc trắng xám, rìa gợn sóng. Sáng sớm thường xuất hiện giọt dịch vi khuẩn màu đục như sương.",
        "nguyen_nhan": "Do vi khuẩn Xanthomonas oryzae pv. oryzae gây ra. Bùng phát mạnh sau những trận mưa bão làm rách lá, hoặc ruộng bón thừa phân Đạm (Urê), thiếu Kali.",
        "hoat_chat": "Bismerthiazol, Oxolinic acid, Bronopol, Kasugamycin.",
        "thuoc_goi_y": [
            "💊 Starner 20WP (Sumitomo) - Pha 20g cho bình 25 lít.",
            "💊 Xanthomix 20WP - Đặc trị vi khuẩn cháy bìa lá.",
            "💊 Totan 200WP - Hiệu quả nhanh, lưu dẫn mạnh.",
            "💊 Sasa 25WP - Kháng sinh thực vật an toàn."
        ],
        "luu_y": "Tuyệt đối NGƯNG bón phân Đạm. Rút nước ruộng khô ráo. Phun thuốc vào buổi chiều mát.",
        "icon": "🦠"
    },
    "Blast": {
        "vn_name": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "trieu_chung": "Vết chấm kim hoặc hình thoi (hình mắt én). Tâm vết bệnh màu xám trắng, viền nâu đậm. Nếu nặng, các vết liên kết lại làm lá cháy khô như bị luộc nước sôi.",
        "nguyen_nhan": "Do nấm Pyricularia oryzae. Thường gặp khi trời âm u, sương mù nhiều, chênh lệch nhiệt độ ngày đêm cao, độ ẩm không khí cao.",
        "hoat_chat": "Tricyclazole (hoạt chất vàng), Isoprothiolane, Fenoxanil, Azoxystrobin.",
        "thuoc_goi_y": [
            "💊 Beam 75WP (Bayer) - Gói 10g cho bình 16 lít.",
            "💊 Fuji-one 40EC (Nhật Bản) - Kích thích rễ, trị đạo ôn.",
            "💊 Filia 525SE (Syngenta) - Phòng trừ đạo ôn và lem lép hạt.",
            "💊 Flash 75WP - Đặc trị đạo ôn lá và cổ bông."
        ],
        "luu_y": "Giữ mực nước ruộng 3-5cm. Không để ruộng khô nứt nẻ. Không phun phân bón lá lúc bệnh đang phát.",
        "icon": "🔥"
    },
    "Brown Spot": {
        "vn_name": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "trieu_chung": "Vết bệnh hình tròn hoặc bầu dục, màu nâu, kích thước nhỏ bằng hạt mè. Xuất hiện rải rác trên lá, đôi khi liên kết thành mảng lớn.",
        "nguyen_nhan": "Do nấm Bipolaris oryzae. Chủ yếu do đất nghèo dinh dưỡng, thiếu Kali, ngộ độc hữu cơ hoặc nhiễm phèn.",
        "hoat_chat": "Propiconazole, Difenoconazole, Tebuconazole.",
        "thuoc_goi_y": [
            "💊 Tilt Super 300EC (Syngenta) - Lem lép hạt, đốm nâu.",
            "💊 Anvil 5SC (Syngenta) - Trừ nấm phổ rộng, xanh lá.",
            "💊 Nevo 330EC - Sạch bệnh, sáng hạt, nặng ký."
        ],
        "luu_y": "Cần bón cân đối N-P-K. Bổ sung thêm phân bón lá chứa Silic, Canxi để lá dày cứng.",
        "icon": "🍂"
    },
    "Tungro": {
        "vn_name": "BỆNH VÀNG LỤI (TUNGRO)",
        "trieu_chung": "Cây lúa thấp lùn, lá chuyển màu vàng cam từ chóp xuống. Lá mới mọc ra ngắn, xoắn, cây đẻ nhánh kém.",
        "nguyen_nhan": "Do virus truyền qua côn trùng môi giới là Rầy xanh đuôi đen (Nephotettix virescens).",
        "hoat_chat": "Phải dùng thuốc trừ RẦY MÔI GIỚI (Fenobucarb, Pymetrozine, Buprofezin).",
        "thuoc_goi_y": [
            "💊 Bassa 50EC - Trừ rầy tiếp xúc, xông hơi mạnh.",
            "💊 Chess 50WG - Chống lột xác, hiệu quả kéo dài.",
            "💊 Trebon 10EC - Hạ gục nhanh rầy rệp."
        ],
        "luu_y": "Nhổ bỏ và vùi sâu cây bệnh. Phun thuốc diệt rầy ngay để tránh lây lan sang ruộng khác.",
        "icon": "🦗"
    },
    "Sheath Blight": {
        "vn_name": "BỆNH KHÔ VẰN (ĐỐM VẰN)",
        "trieu_chung": "Vết bệnh dạng vân mây (da hổ), loang lổ ở bẹ lá và phần gốc lúa. Màu xám lục hoặc nâu, lan dần lên lá trên.",
        "nguyen_nhan": "Do nấm Rhizoctonia solani. Do gieo sạ quá dày, bón thừa đạm, ruộng rậm rạp thiếu ánh sáng.",
        "hoat_chat": "Validamycin A, Hexaconazole, Pencycuron.",
        "thuoc_goi_y": [
            "💊 Validacin 5L (Nhật Bản) - Kháng sinh trị nấm.",
            "💊 Anvil 5SC - Chuyên trị khô vằn, lem lép.",
            "💊 Valivithaco 5SL - Giá thành rẻ, hiệu quả ổn định."
        ],
        "luu_y": "Vạch hàng lúa cho thông thoáng. Phun thuốc kỹ vào phần gốc lúa nơi có vết bệnh.",
        "icon": "🍄"
    },
    "Rice Hispa": {
        "vn_name": "SÂU GAI (BỌ GAI)",
        "trieu_chung": "Lá lúa bị cạo lớp biểu bì tạo thành những vệt trắng dài song song gân lá. Đầu lá khô trắng xác xơ.",
        "nguyen_nhan": "Do ấu trùng và thành trùng bọ gai (Dicladispa armigera) cạo ăn diệp lục.",
        "hoat_chat": "Cartap, Dimethoate, Abamectin.",
        "thuoc_goi_y": [
            "💊 Padan 95SP - Đặc trị sâu đục thân, sâu gai.",
            "💊 Reasgant 3.6EC - Thuốc trừ sâu sinh học.",
            "💊 Gà Nòi 95SP - Diệt sâu nhanh, mạnh."
        ],
        "luu_y": "Nên phun vào sáng sớm hoặc chiều mát. Vợt bắt thành trùng vào sáng sớm.",
        "icon": "🐛"
    },
    "Leaf scald": {
        "vn_name": "CHÁY CHÓP LÁ",
        "trieu_chung": "Vết bệnh hình chữ V ngược từ chóp lá lan vào trong. Có các đường vân gợn sóng màu nâu.",
        "nguyen_nhan": "Do nấm Microdochium oryzae gây hại.",
        "hoat_chat": "Carbendazim, Isoprothiolane, Mancozeb.",
        "thuoc_goi_y": [
            "💊 Carbenzim 500FL - Trị nấm phổ rộng.",
            "💊 Fuji-one 40EC - Vừa trị đạo ôn vừa trị cháy chóp lá."
        ],
        "luu_y": "Cắt giảm đạm, tăng cường bón Kali.",
        "icon": "🍂"
    }
}

# Ánh xạ các tên tiếng Anh/Viết tắt về tên chuẩn
TU_DIEN_BENH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"},
    "Rice Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"},
    "Sheathblight": {"ref": "Sheath Blight"},
    "Hispa": {"ref": "Rice Hispa"},
    "Leafscald": {"ref": "Leaf scald"}
})

# ==============================================================================
# 3. CÁC HÀM TIỆN ÍCH (AI, PDF, THỜI TIẾT)
# ==============================================================================

def get_weather(lat, lon):
    """Lấy dữ liệu thời tiết từ Open-Meteo API"""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain,wind_speed_10m&timezone=auto"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()['current']
        return None
    except:
        return None

def get_ai_response(user_query):
    """Logic Chatbot AI (Rule-based)"""
    user_query = user_query.lower()
    
    # Logic tìm kiếm từ khóa
    keywords = {
        "đạo ôn": "Blast", "cháy lá": "Blast", "cổ bông": "Blast", "beam": "Blast",
        "bạc lá": "Bacterial Leaf Blight", "vi khuẩn": "Bacterial Leaf Blight", "cháy bìa": "Bacterial Leaf Blight",
        "đốm nâu": "Brown Spot", "tiêm lửa": "Brown Spot",
        "khô vằn": "Sheath Blight", "đốm vằn": "Sheath Blight", "validacin": "Sheath Blight",
        "vàng lụi": "Tungro", "lùn": "Tungro", "rầy": "Tungro",
        "sâu gai": "Rice Hispa", "bọ gai": "Rice Hispa",
        "cháy chóp": "Leaf scald"
    }
    
    found_key = None
    for kw, key in keywords.items():
        if kw in user_query:
            found_key = key
            break
            
    if found_key:
        data = TU_DIEN_BENH[found_key]
        if "ref" in data: data = TU_DIEN_BENH[data["ref"]]
        
        response = f"""
        **🤖 Bác sĩ Lúa trả lời về: {data['vn_name']}**
        
        1. **Dấu hiệu:** {data['trieu_chung']}
        2. **Nguyên nhân:** {data['nguyen_nhan']}
        3. **🧪 Hoạt chất:** {data['hoat_chat']}
        
        💊 **THUỐC ĐẶC TRỊ GỢI Ý:**
        {chr(10).join(['- ' + t for t in data['thuoc_goi_y']])}
        
        🛡️ **Lưu ý quan trọng:** {data['luu_y']}
        """
        return response
    
    # Các câu hỏi xã giao
    elif "xin chào" in user_query or "chào" in user_query:
        return "Dạ chào bà con! Bà con cần tôi giúp gì về lúa hôm nay ạ? Bà con có thể hỏi về các loại bệnh hoặc cách dùng thuốc."
    elif "thời tiết" in user_query:
        return "Bà con vui lòng nhìn lên phần đầu trang web để xem thời tiết chính xác tại vị trí của mình nhé!"
    elif "cảm ơn" in user_query:
        return "Dạ không có chi! Chúc bà con trúng mùa được giá!"
    else:
        return "Dạ câu hỏi này hơi khó. Bà con hãy thử hỏi tên bệnh cụ thể như: 'trị đạo ôn', 'thuốc trừ sâu gai', hoặc 'bệnh bạc lá' để tôi tra cứu nhé."

def create_pdf(benh_info):
    """Tạo file PDF đơn thuốc"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt="PHIEU KET QUA CHAN DOAN (AI REPORT)", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Ngay tao: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align='C')
    pdf.line(10, 30, 200, 30)
    pdf.ln(10)
    
    # Lưu ý: FPDF mặc định không hỗ trợ tiếng Việt có dấu tốt, nên ta dùng không dấu hoặc latin-1
    pdf.set_font("Arial", 'B', size=14)
    pdf.cell(0, 10, txt=f"KET LUAN: {benh_info['vn_name']}", ln=1)
    
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=f"Trieu chung: {benh_info['trieu_chung']}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Nguyen nhan: {benh_info['nguyen_nhan']}")
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(0, 10, txt="DON THUOC GOI Y:", ln=1)
    pdf.set_font("Arial", size=12)
    for t in benh_info['thuoc_goi_y']:
         pdf.cell(0, 10, txt=f" - {t}", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'I', size=11)
    pdf.multi_cell(0, 10, txt=f"Luu y: {benh_info['luu_y']}")
    
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# ==============================================================================
# 4. GIAO DIỆN NGƯỜI DÙNG (UI/UX)
# ==============================================================================

# CSS tùy chỉnh giao diện xanh mướt
st.markdown("""
<style>
    .main {background-color: #f1f8e9;}
    .stTabs [data-baseweb="tab-list"] {gap: 10px;}
    .stTabs [data-baseweb="tab"] {
        height: 50px; 
        background-color: white; 
        border-radius: 8px; 
        color: #2e7d32; 
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [aria-selected="true"] {background-color: #2e7d32; color: white;}
    
    /* Card thời tiết */
    .weather-card {
        background: linear-gradient(135deg, #43a047, #1b5e20);
        color: white;
        padding: 15px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .metric-label {font-size: 0.9rem; opacity: 0.9;}
    .metric-value {font-size: 1.8rem; font-weight: bold;}
    
    /* Card kết quả */
    .result-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #2e7d32;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .drug-list {background-color: #e8f5e9; padding: 10px; border-radius: 5px;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/6008/6008954.png", width=100)
    st.title("NHẬT KÝ KHÁM")
    st.info("Lịch sử các lần chẩn đoán gần đây:")
    if st.session_state['history']:
        for item in reversed(st.session_state['history']):
            st.caption(f"🕒 {item['time']} - {item['benh']}")
    else:
        st.write("Chưa có dữ liệu.")
    st.markdown("---")
    st.write("© 2026 Rice Doctor AI Project")

# --- HEADER CHÍNH ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("https://cdn-icons-png.flaticon.com/512/3022/3022938.png", width=90)
with col_title:
    st.markdown("<h1 style='color: #1b5e20; margin-bottom: 0;'>HỆ THỐNG BÁC SĨ LÚA AI</h1>", unsafe_allow_html=True)
    st.caption("Công nghệ AI 4.0: Chẩn đoán Hình ảnh - Tư vấn Thuốc - Cảnh báo Thời tiết")

# --- MODULE THỜI TIẾT (AUTO GPS) ---
st.markdown("### 🌤️ Thời Tiết Nông Vụ Tại Chỗ")
location = get_geolocation()

if location:
    lat = location['coords']['latitude']
    lon = location['coords']['longitude']
    weather = get_weather(lat, lon)
    
    if weather:
        temp = weather['temperature_2m']
        hum = weather['relative_humidity_2m']
        rain = weather['rain']
        wind = weather['wind_speed_10m']
        
        # Hiển thị 4 chỉ số đẹp
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="weather-card"><div class="metric-label">🌡️ Nhiệt độ</div><div class="metric-value">{temp}°C</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="weather-card"><div class="metric-label">💧 Độ ẩm</div><div class="metric-value">{hum}%</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="weather-card"><div class="metric-label">🌧️ Lượng mưa</div><div class="metric-value">{rain}mm</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="weather-card"><div class="metric-label">💨 Gió</div><div class="metric-value">{wind}km/h</div></div>', unsafe_allow_html=True)

        # Cảnh báo thông minh
        if rain > 0.5:
            st.error("⚠️ CẢNH BÁO: Trời đang mưa. KHÔNG NÊN phun thuốc BVTV lúc này!", icon="☔")
        elif hum > 85:
            st.warning("⚠️ CẢNH BÁO: Độ ẩm cao (>85%). Nguy cơ cao bùng phát bệnh Đạo ôn và Khô vằn!", icon="🔥")
        elif wind > 15:
            st.warning("⚠️ CẢNH BÁO: Gió mạnh. Hạn chế phun thuốc để tránh thuốc bay lung tung.", icon="💨")
        else:
            st.success("✅ THỜI TIẾT TỐT: Thích hợp để thăm đồng và chăm sóc lúa.", icon="🌤️")
else:
    st.info("📍 Đang dò tìm vị trí GPS... (Vui lòng bấm 'Cho phép/Allow' nếu trình duyệt hỏi)")

st.markdown("---")

# --- TAB CHỨC NĂNG CHÍNH ---
tab_chan_doan, tab_chat_bot, tab_tra_cuu = st.tabs(["📸 CHẨN ĐOÁN HÌNH ẢNH", "💬 TRỢ LÝ AI (CHATBOT)", "📚 TỪ ĐIỂN BỆNH"])

# ==============================================================================
# TAB 1: CHẨN ĐOÁN HÌNH ẢNH (CORE FEATURE)
# ==============================================================================
with tab_chan_doan:
    col_input, col_process = st.columns([1, 1.5], gap="large")
    
    with col_input:
        st.subheader("1. Thu thập hình ảnh")
        st.write("Chọn cách nhập ảnh mẫu bệnh:")
        input_mode = st.radio("Nguồn ảnh:", ["📂 Tải ảnh có sẵn", "📷 Camera trực tiếp"], horizontal=True, label_visibility="collapsed")
        
        final_image = None
        
        if input_mode == "📷 Camera trực tiếp":
            if st.checkbox("🔴 Bật Camera", value=False, help="Bật để chụp ảnh, tắt để tiết kiệm pin"):
                cam_img = st.camera_input("Chụp ảnh lá lúa bị bệnh")
                if cam_img: final_image = cam_img
        else:
            up_img = st.file_uploader("Tải ảnh từ thư viện", type=['jpg', 'png', 'jpeg'])
            if up_img: final_image = up_img

    if final_image:
        # Xử lý ảnh
        pil_image = Image.open(final_image)
        with col_input:
            st.image(pil_image, caption="Ảnh mẫu đầu vào", use_column_width=True)
            analyze_btn = st.button("🔍 BẮT ĐẦU CHẨN ĐOÁN", type="primary", use_container_width=True)

        if analyze_btn:
            with col_process:
                with st.spinner("🤖 AI đang phân tích tế bào lá lúa..."):
                    try:
                        # Gửi ảnh lên API Roboflow
                        pil_image.save("temp.jpg")
                        client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key=MY_API_KEY)
                        result = client.infer("temp.jpg", model_id=MY_MODEL_ID)
                        predictions = result.get('predictions', [])
                        
                        # Fix format dictionary -> list
                        if isinstance(predictions, dict):
                             predictions = [{"class": k, "confidence": v['confidence']} for k, v in predictions.items()]

                        if predictions:
                            # Tìm bệnh có độ tin cậy cao nhất
                            top_pred = max(predictions, key=lambda x: x['confidence'])
                            label = top_pred['class']
                            confidence = top_pred['confidence']
                            
                            # Tra từ điển
                            info = TU_DIEN_BENH.get(label)
                            if info and "ref" in info: info = TU_DIEN_BENH.get(info["ref"])
                            
                            if info:
                                # HIỂN THỊ KẾT QUẢ ĐẸP
                                st.success(f"✅ ĐÃ PHÁT HIỆN: {info['vn_name']} (Độ tin cậy: {confidence*100:.1f}%)")
                                
                                st.markdown(f"""
                                <div class="result-box">
                                    <h3>{info['icon']} Triệu chứng nhận biết:</h3>
                                    <p>{info['trieu_chung']}</p>
                                    <h3>🌪️ Nguyên nhân:</h3>
                                    <p>{info['nguyen_nhan']}</p>
                                    <hr>
                                    <div class="drug-list">
                                        <h3 style="color: #d32f2f;">💊 Đơn thuốc & Biện pháp xử lý:</h3>
                                        <p><b>Hoạt chất:</b> {info['hoat_chat']}</p>
                                        <ul>
                                            {''.join([f'<li>{d}</li>' for d in info['thuoc_goi_y']])}
                                        </ul>
                                        <p><b>⚠️ Lưu ý:</b> {info['luu_y']}</p>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # TÍNH NĂNG ÂM THANH (VOICE)
                                speech_text = f"Kết quả chẩn đoán: Cây lúa bị {info['vn_name']}. Bà con nên sử dụng các loại thuốc sau: {', '.join([t.split('-')[0] for t in info['thuoc_goi_y']])}. Lưu ý: {info['luu_y']}"
                                tts = gTTS(text=speech_text, lang='vi')
                                tts.save("result_voice.mp3")
                                st.audio("result_voice.mp3", format="audio/mp3")
                                
                                # TÍNH NĂNG XUẤT PDF
                                pdf_bytes = create_pdf(info)
                                st.download_button(
                                    label="📥 TẢI PHIẾU KẾT QUẢ (PDF)",
                                    data=pdf_bytes,
                                    file_name=f"Don_thuoc_{label}.pdf",
                                    mime="application/pdf"
                                )
                                
                                # Lưu lịch sử
                                st.session_state['history'].append({
                                    "time": datetime.now().strftime("%H:%M"),
                                    "benh": info['vn_name']
                                })
                                
                            else:
                                st.warning(f"⚠️ Phát hiện: {label} (Dữ liệu đang cập nhật)")
                        else:
                            st.success("🌿 Cây lúa KHỎE MẠNH! Không phát hiện dấu hiệu bệnh.")
                            st.balloons()
                            
                    except Exception as e:
                        st.error(f"Lỗi hệ thống: {e}")

# ==============================================================================
# TAB 2: TRỢ LÝ AI (CHATBOT)
# ==============================================================================
with tab_chat_bot:
    st.subheader("💬 Trò chuyện với Chuyên gia Nông nghiệp AI")
    st.markdown("Bà con có thể hỏi: *thuốc trị đạo ôn là gì?*, *cách phòng bệnh bạc lá*, *dấu hiệu rầy nâu*...")
    
    # Hiển thị lịch sử chat
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Ô nhập liệu
    if prompt := st.chat_input("Nhập câu hỏi của bà con tại đây..."):
        # Hiện câu hỏi user
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI trả lời
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Lấy câu trả lời
            ai_reply = get_ai_response(prompt)
            
            # Hiệu ứng gõ chữ
            for chunk in ai_reply.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})

# ==============================================================================
# TAB 3: TỪ ĐIỂN TRA CỨU (THƯ VIỆN)
# ==============================================================================
with tab_tra_cuu:
    st.subheader("📚 Thư viện Bệnh học Lúa")
    st.write("Tra cứu nhanh thông tin các loại bệnh phổ biến:")
    
    for key, val in TU_DIEN_BENH.items():
        if "ref" not in val: # Chỉ hiện bệnh chính
            with st.expander(f"{val['icon']} {val['vn_name']}"):
                st.write(f"**Dấu hiệu:** {val['trieu_chung']}")
                st.write(f"**Thuốc:** {', '.join(val['thuoc_goi_y'])}")import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image
import numpy as np
import cv2
from datetime import datetime
from gtts import gTTS
import io
from fpdf import FPDF
import time
import requests
from streamlit_js_eval import get_geolocation

# --- 1. CẤU HÌNH HỆ THỐNG ---
MY_API_KEY = "8tf2UvcnEv8h80bV2G0Q"
MY_MODEL_ID = "rice-leaf-disease-twtlz/1"

st.set_page_config(page_title="Bác Sĩ Lúa AI Pro", page_icon="🌾", layout="wide")

# Khởi tạo bộ nhớ
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = [{"role": "assistant", "content": "Chào bà con! Tôi là Trợ lý lúa gạo. Bà con cần hỏi gì ạ?"}]

# --- 2. KHO DỮ LIỆU THUỐC & BỆNH (CHI TIẾT) ---
TU_DIEN_BENH = {
    "Bacterial Leaf Blight": {
        "vn_name": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "trieu_chung": "Vết bệnh từ chóp lá lan xuống dọc mép lá, màu vàng hoặc trắng xám.",
        "nguyen_nhan": "Vi khuẩn Xanthomonas oryzae. Thừa đạm, mưa bão làm rách lá.",
        "hoat_chat": "Oxolinic acid, Bismerthiazol, Bronopol.",
        "thuoc": "Starner 20WP, Xanthomix 20WP, Totan 200WP, Sasa 25WP.",
        "loi_khuyen": "Ngưng bón đạm ngay, rút nước ruộng cho khô ráo.",
        "icon": "🦠"
    },
    "Blast": {
        "vn_name": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "trieu_chung": "Vết hình mắt én, tâm xám trắng, viền nâu đậm.",
        "nguyen_nhan": "Nấm Pyricularia oryzae. Trời âm u, sương mù, đêm lạnh.",
        "hoat_chat": "Tricyclazole, Isoprothiolane, Fenoxanil.",
        "thuoc": "Beam 75WP, Fuji-one 40EC, Filia 525SE, Flash 75WP.",
        "loi_khuyen": "Giữ nước ruộng 3-5cm, không phun phân bón lá lúc này.",
        "icon": "🔥"
    },
    "Brown Spot": {
        "vn_name": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "trieu_chung": "Vết tròn nhỏ màu nâu như hạt mè rải rác trên lá.",
        "nguyen_nhan": "Nấm Bipolaris oryzae. Đất phèn, nghèo dinh dưỡng, thiếu Kali.",
        "hoat_chat": "Propiconazole, Difenoconazole.",
        "thuoc": "Tilt Super 300EC, Anvil 5SC, Nevo 330EC.",
        "loi_khuyen": "Bón bổ sung Kali và vôi để cải tạo đất.",
        "icon": "🍂"
    }
}
# Mapping tên dính liền từ AI
TU_DIEN_BENH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"}, "Rice Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"}, "Sheathblight": {"vn_name": "KHÔ VẰN", "thuoc": "Validacin 5L, Anvil 5SC"},
    "Hispa": {"vn_name": "SÂU GAI", "thuoc": "Padan 95SP"},
    "Leafscald": {"vn_name": "CHÁY CHÓP LÁ", "thuoc": "Carbenzim 500FL"}
})

# --- 3. HÀM TIỆN ÍCH ---
def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain&timezone=auto"
        res = requests.get(url, timeout=5).json()
        return res.get('current')
    except: return None

def create_pdf(info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="PHIEU KET QUA CHAN DOAN", ln=1, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(0, 10, txt=f"BENH: {info['vn_name']}", ln=1)
    pdf.multi_cell(0, 10, txt=f"Nguyen nhan: {info['nguyen_nhan']}")
    pdf.multi_cell(0, 10, txt=f"Thuoc dac tri: {info['thuoc']}")
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 4. GIAO DIỆN ---
st.markdown("""
<style>
    .main {background-color: #f8fff0;}
    .weather-card {background: linear-gradient(135deg, #2e7d32, #1b5e20); color: white; padding: 20px; border-radius: 15px; text-align: center;}
</style>
""", unsafe_allow_html=True)

st.title("🌾 HỆ THỐNG CHUẨN ĐOÁN & TRỢ LÝ LÚA AI")
st.markdown("---")

# --- XỬ LÝ THỜI TIẾT (FIX LỖI KEYERROR) ---
st.subheader("🌦️ Thời Tiết Nông Vụ")
location = get_geolocation()

if location and 'coords' in location:
    lat = location['coords'].get('latitude')
    lon = location['coords'].get('longitude')
    
    if lat and lon:
        w = get_weather(lat, lon)
        if w:
            c1, c2, c3 = st.columns(3)
            c1.metric("🌡️ Nhiệt độ", f"{w['temperature_2m']}°C")
            c2.metric("💧 Độ ẩm", f"{w['relative_humidity_2m']}%")
            c3.metric("🌧️ Lượng mưa", f"{w['rain']} mm")
            
            if w['rain'] > 0: st.error("☔ Trời đang mưa: Bà con tạm ngưng phun thuốc!")
            elif w['relative_humidity_2m'] > 85: st.warning("🔥 Ẩm cao: Nguy cơ Đạo ôn tăng cao!")
            else: st.success("🌤️ Thời tiết thuận lợi để thăm đồng.")
else:
    st.info("📍 Đang chờ xác nhận vị trí... (Vui lòng bấm 'Cho phép/Allow' trên trình duyệt)")

st.markdown("---")

t1, t2 = st.tabs(["📸 CHẨN ĐOÁN HÌNH ẢNH", "💬 HỎI ĐÁP AI"])

with t1:
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        mode = st.radio("Chọn nguồn:", ["Tải ảnh", "Camera"], horizontal=True)
        img_file = st.camera_input("Chụp mẫu") if mode == "Camera" else st.file_uploader("Chọn ảnh", type=['jpg','png'])

    if img_file:
        img = Image.open(img_file)
        with col_l:
            st.image(img, use_column_width=True)
            if st.button("🔍 PHÂN TÍCH", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("Đang soi bệnh..."):
                        img.save("temp.jpg")
                        client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key=MY_API_KEY)
                        res = client.infer("temp.jpg", model_id=MY_MODEL_ID)
                        preds = res.get('predictions', [])
                        if isinstance(preds, dict): preds = [{"class": k, "confidence": v['confidence']} for k, v in preds.items()]

                        if preds:
                            top = max(preds, key=lambda x: x['confidence'])
                            info = TU_DIEN_BENH.get(top['class'])
                            if info and "ref" in info: info = TU_DIEN_BENH.get(info["ref"])
                            
                            if info:
                                st.success(f"🔴 PHÁT HIỆN: {info['vn_name']}")
                                st.write(f"**🧐 Dấu hiệu:** {info.get('trieu_chung','')}")
                                st.warning(f"**💊 Thuốc:** {info.get('thuoc','')}")
                                
                                # Audio
                                txt = f"Lúa bị {info['vn_name']}. Bà con nên dùng thuốc {info['thuoc']}"
                                gTTS(txt, lang='vi').save("v.mp3")
                                st.audio("v.mp3")
                                
                                # PDF
                                st.download_button("📥 Tải đơn thuốc", create_pdf(info), "don.pdf")
                        else: st.success("✅ Cây lúa khỏe mạnh!")

with t2:
    for m in st.session_state.chat_history:
        with st.chat_message(m["role"]): st.write(m["content"])
    if p := st.chat_input("Bà con muốn hỏi gì?"):
        st.session_state.chat_history.append({"role": "user", "content": p})
        with st.chat_message("user"): st.write(p)
        # AI Logic đơn giản
        ans = "Bà con vui lòng hỏi về: đạo ôn, bạc lá, đốm nâu hoặc thuốc trị bệnh để tôi hỗ trợ nhé!"
        if "đạo ôn" in p.lower(): ans = "Đạo ôn bà con dùng Beam 75WP hoặc Fuji-one nhé."
        elif "bạc lá" in p.lower(): ans = "Bạc lá bà con ngưng đạm, phun Starner 20WP ngay."
        st.session_state.chat_history.append({"role": "assistant", "content": ans})
        with st.chat_message("assistant"): st.write(ans)