import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image
import numpy as np
import cv2
from datetime import datetime

# --- 1. CẤU HÌNH API ---
MY_API_KEY = "8tf2UvcnEv8h80bV2G0Q"
MY_MODEL_ID = "rice-leaf-disease-twtlz/1"

# --- 2. CƠ SỞ DỮ LIỆU DƯỢC LÝ (Đã cập nhật đầy đủ tên dính liền) ---
TU_DIEN_BENH = {
    # 1. BẠC LÁ (BACTERIAL BLIGHT)
    "Bacterial Leaf Blight": {
        "vn_name": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "dau_hieu": "Vết bệnh từ chóp lá lan xuống, bìa lá gợn sóng màu vàng/trắng xám. Sáng sớm có giọt dịch đục.",
        "nguyen_nhan": "Do vi khuẩn Xanthomonas oryzae. Bùng phát khi mưa bão rách lá, thừa đạm.",
        "hoat_chat": "Oxolinic acid, Bismerthiazol, Bronopol.",
        "thuoc_tm": "Starner 20WP, Xanthomix 20WP, Totan 200WP, Sasa 25WP.",
        "luu_y": "Tuyệt đối KHÔNG bón Đạm. Phun khi lá khô ráo."
    },
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"}, # Sửa lỗi dính chữ

    # 2. ĐẠO ÔN (BLAST)
    "Blast": {
        "vn_name": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "dau_hieu": "Vết chấm kim hoặc hình thoi (mắt én), tâm trắng xám, viền nâu.",
        "nguyen_nhan": "Do nấm Pyricularia oryzae. Bệnh nặng khi trời âm u, sương mù, lạnh.",
        "hoat_chat": "Tricyclazole (đặc trị), Isoprothiolane, Fenoxanil.",
        "thuoc_tm": "Beam 75WP, Fuji-one 40EC, Filia 525SE, Flash 75WP.",
        "luu_y": "Giữ nước ruộng 3-5cm. Không phun phân bón lá."
    },
    "Leaf Blast": {"ref": "Blast"},
    "Neck_Blast": {"ref": "Blast"},
    "Rice Blast": {"ref": "Blast"},

    # 3. ĐỐM NÂU (BROWN SPOT)
    "Brown Spot": {
        "vn_name": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "dau_hieu": "Vết tròn nhỏ màu nâu như hạt mè, rải rác trên lá.",
        "nguyen_nhan": "Do nấm Bipolaris oryzae. Thường do đất nghèo dinh dưỡng, thiếu Kali/Silic.",
        "hoat_chat": "Propiconazole, Difenoconazole, Azoxystrobin.",
        "thuoc_tm": "Tilt Super 300EC, Anvil 5SC, Amistar Top 325SC.",
        "luu_y": "Bón bổ sung Kali, Silic, Vôi."
    },
    "Brownspot": {"ref": "Brown Spot"}, 

    # 4. TUNGRO (VÀNG LỤI)
    "Tungro": {
        "vn_name": "BỆNH VÀNG LỤI (TUNGRO)",
        "dau_hieu": "Cây thấp lùn, lá vàng cam xoắn lại, đẻ nhánh kém.",
        "nguyen_nhan": "Do virus truyền qua Rầy xanh đuôi đen.",
        "hoat_chat": "Fenobucarb, Pymetrozine (Diệt rầy môi giới).",
        "thuoc_tm": "Bassa 50EC, Chess 50WG, Trebon 10EC.",
        "luu_y": "Nhổ bỏ cây bệnh, tiêu diệt rầy ngay."
    },

    # 5. KHÔ VẰN (SHEATH BLIGHT)
    "Sheath Blight": {
        "vn_name": "BỆNH KHÔ VẰN (ĐỐM VẰN)",
        "dau_hieu": "Vết vằn da hổ/vân mây ở bẹ lá gốc, màu xám lục.",
        "nguyen_nhan": "Do nấm Rhizoctonia solani. Do sạ dày, rậm rạp.",
        "hoat_chat": "Validamycin A, Hexaconazole.",
        "thuoc_tm": "Validacin 5L, Anvil 5SC, Valivithaco.",
        "luu_y": "Phun kỹ vào phần gốc lúa."
    },
    "Sheathblight": {"ref": "Sheath Blight"},

    # 6. SÂU GAI (RICE HISPA)
    "Rice Hispa": {
        "vn_name": "SÂU GAI (BỌ GAI)",
        "dau_hieu": "Lá có vệt trắng dài song song gân, đầu lá khô trắng.",
        "nguyen_nhan": "Do ấu trùng và thành trùng bọ gai cạo ăn biểu bì.",
        "hoat_chat": "Abamectin, Cartap, Dimethoate.",
        "thuoc_tm": "Reasgant 3.6EC, Padan 95SP, Gà Nòi 95SP.",
        "luu_y": "Phun vào sáng sớm hoặc chiều mát."
    },
    "Hispa": {"ref": "Rice Hispa"},

    # 7. CHÁY CHÓP LÁ (LEAF SCALD)
    "Leaf scald": {
        "vn_name": "CHÁY CHÓP LÁ", 
        "dau_hieu": "Cháy từ chóp lá vào hình chữ V, có vân mây.", 
        "nguyen_nhan": "Nấm Microdochium oryzae.", 
        "hoat_chat": "Carbendazim, Isoprothiolane.", 
        "thuoc_tm": "Carbenzim 500FL, Fuji-one 40EC.", 
        "luu_y": "Cắt giảm đạm, tăng Kali."
    },
    "Leafscald": {"ref": "Leaf scald"}
}

# --- 3. GIAO DIỆN (UI) ---
st.set_page_config(page_title="Chuẩn đoán bệnh trên lúa", page_icon="🌾", layout="wide")

st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #006400; text-align: center; font-weight: 800; text-transform: uppercase;}
    .presc-box {background-color: #f0fdf4; padding: 15px; border-radius: 8px; border-left: 5px solid #22c55e; margin-bottom: 10px;}
    .cause-box {background-color: #fff7ed; padding: 15px; border-radius: 8px; border-left: 5px solid #f97316; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2823/2823521.png", width=80)
    st.title("MENU CHỨC NĂNG")
    st.write(f"🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

st.markdown('<div class="main-header">🌾 HỆ THỐNG CHUẨN ĐOÁN BỆNH TRÊN LÚA</div>', unsafe_allow_html=True)
st.markdown("---")

col_left, col_right = st.columns([1, 1.3], gap="large")

input_img = None

with col_left:
    st.subheader("📸 1. Hình ảnh mẫu bệnh")
    tab1, tab2 = st.tabs(["Camera trực tiếp", "Tải ảnh lên"])
    with tab1:
        cam = st.camera_input("Chụp mẫu bệnh")
        if cam: input_img = cam
    with tab2:
        up = st.file_uploader("Chọn file ảnh", type=["jpg", "png"])
        if up: input_img = up

if input_img:
    image = Image.open(input_img)
    
    with col_left:
        if st.button("🔍 BẮT ĐẦU CHUẨN ĐOÁN", type="primary", use_container_width=True):
            with st.spinner("Đang xử lý hình ảnh..."):
                try:
                    # Gửi AI
                    image_np = np.array(image)
                    image.save("temp.jpg")
                    client = InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key=MY_API_KEY)
                    result = client.infer("temp.jpg", model_id=MY_MODEL_ID)
                    predictions = result.get('predictions', [])
                    
                    if isinstance(predictions, dict):
                         temp_list = []
                         for key, val in predictions.items():
                             temp_list.append({'class': key, 'confidence': val['confidence']})
                         predictions = temp_list

                    img_cv = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
                    detected = set()
                    
                    if predictions:
                        for p in predictions:
                            label = p.get('class', 'Unknown')
                            detected.add(label)
                            if 'x' in p:
                                x, y, w, h = p['x'], p['y'], p['width'], p['height']
                                x1, y1 = int(x - w/2), int(y - h/2)
                                x2, y2 = int(x + w/2), int(y + h/2)
                                cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 0, 255), 2)
                                cv2.putText(img_cv, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
                        st.image(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB), caption="Khu vực phát hiện bệnh", use_column_width=True)

                        with col_right:
                            st.subheader("💊 2. Kết quả & Biện pháp xử lý")
                            
                            for label in detected:
                                info = TU_DIEN_BENH.get(label)
                                if info and "ref" in info: info = TU_DIEN_BENH.get(info["ref"])
                                
                                if info:
                                    with st.expander(f"🔴 KẾT QUẢ: {info['vn_name']}", expanded=True):
                                        st.markdown(f"""
                                        <div class="cause-box">
                                            <b>🧐 Dấu hiệu:</b> {info['dau_hieu']}<br>
                                            <b>🌪️ Nguyên nhân:</b> {info['nguyen_nhan']}
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        st.markdown(f"""
                                        <div class="presc-box">
                                            <b>🛡️ BIỆN PHÁP HÓA HỌC & CANH TÁC:</b><br><br>
                                            🧪 <b>Hoạt chất (Active Ingredient):</b><br>
                                            {info['hoat_chat']}<br><br>
                                            💊 <b>Tên thương mại (Thuốc gợi ý):</b><br>
                                            {info['thuoc_tm']}<br><br>
                                            ⚠️ <b>Lưu ý quan trọng:</b> {info['luu_y']}
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    if label == "Healthy":
                                        st.success("✅ Cây lúa khỏe mạnh.")
                                    else:
                                        st.warning(f"Phát hiện: {label} (Đang cập nhật dữ liệu)")
                    else:
                        st.image(image, caption="Ảnh gốc", use_column_width=True)
                        with col_right:
                            st.success("✅ CÂY LÚA KHỎE MẠNH")
                            st.info("Không phát hiện sâu bệnh.")

                except Exception as e:
                    st.error(f"Lỗi hệ thống: {e}")