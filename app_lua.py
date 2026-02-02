import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import requests
import pandas as pd

# Cấu hình trang
st.set_page_config(page_title="Chuẩn đoán bệnh đạo ôn .." , page_icon="👨‍⚕️", layout="wide")

# CSS tùy chỉnh giao diện
st.markdown("""
<style>
    .main {background-color: #f4f6f9;}
    h1 {color: #1b5e20; text-align: center;}
    .stChatInput {border-radius: 20px;}
    div.stMarkdown h3 {color: #2e7d32; border-bottom: 2px solid #a5d6a7; padding-bottom: 10px;}
    div.stMarkdown h4 {color: #d32f2f; margin-top: 20px;}
    .reportview-container .markdown-text-container {font-family: 'Arial';}
    .weather-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

import streamlit.components.v1 as components

# Khởi tạo session state
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []
if 'location' not in st.session_state:
    st.session_state['location'] = None

# ==============================================================================
# HÀM LẤY THÔNG TIN THỜI TIẾT THANH HÓA
# ==============================================================================

def lay_thoi_tiet(city="Can Tho"):
    """Lấy thông tin thời tiết từ API OpenWeatherMap"""
    try:
        api_key = "c7debdc7ac4deefb232ab3da884f152d"
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": f"{city},VN",
            "appid": api_key,
            "units": "metric",
            "lang": "vi"
        }
            
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "thanh_pho": data.get('name', city),
                "nhiet_do": round(data['main']['temp'], 1),
                "cam_giac": round(data['main']['feels_like'], 1),
                "do_am": data['main']['humidity'],
                "ap_suat": data['main']['pressure'],
                "mo_ta": data['weather'][0]['description'].capitalize(),
                "gio": round(data['wind']['speed'] * 3.6, 1),
                "may": data['clouds']['all'],
                "nguon": "🌍 Dữ liệu vệ tinh (Live)"
            }
        else:
            print(f"⚠️ API Weather lỗi: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Lỗi kết nối Weather: {str(e)}")
    
    # Dữ liệu mặc định nếu API lỗi
    return {
        "thanh_pho": city,
        "nhiet_do": 28.0,
        "cam_giac": 30.0,
        "do_am": 85,  # Tăng độ ẩm để có thể cảnh báo nguy cơ
        "ap_suat": 1012,
        "mo_ta": "Nhiều mây",
        "gio": 12.0,
        "may": 60,
        "nguon": "🌍 Dữ liệu mô phỏng"
    }

# ==============================================================================
# 1. CƠ SỞ DỮ LIỆU TRI THỨC BỆNH HẠI (Chi tiết chuyên sâu + Thời tiết)
# ==============================================================================
úp  = {
    "đạo ôn": """🔥 **BỆNH ĐẠO ÔN (CHÁY LÁ) - *Pyricularia oryzae***

**I. TÁC NHÂN & ĐIỀU KIỆN THỜI TIẾT:**

**1. Nấm gây bệnh:**
- Tên khoa học: *Pyricularia oryzae* (syn. *Magnaporthe oryzae*)
- Nấm tiết độc tố Pyricularin ức chế quá trình hô hấp tế bào cây
- Bào tử nấm phát tán qua gió, mưa phùn, sương mù

**2. Điều kiện thời tiết thuận lợi (RẤT QUAN TRỌNG):**

**Nhiệt độ tối ưu:** 20-28°C
- **Dưới 16°C**: Nấm phát triển chậm
- **20-25°C**: Nấm phát triển mạnh nhất, bào tử nảy mầm nhanh
- **Trên 32°C**: Nấm bị ức chế

**Độ ẩm không khí:** >90% (cực kỳ quan trọng)
- **85-90%**: Bệnh phát triển trung bình
- **>92%**: Bệnh bùng phát nghiêm trọng
- Sương mù, mưa phùn kéo dài 2-3 đêm liên tục = Nguy cơ CAO

**Ánh sáng:**
- Trời âm u, ít nắng 3-5 ngày liên tục → Bệnh nặng
- Nắng gắt, khô hanh → Bệnh giảm

**Chênh lệch nhiệt độ ngày-đêm:**
- Chênh lệch >10°C (VD: Ngày 30°C, đêm 18°C) → Nguy cơ cao
- Sương mù đọng nhiều vào sáng sớm

**Gió:**
- Gió nhẹ: Lan truyền bào tử
- Gió mạnh: Gây vết thương, nấm xâm nhập dễ dàng

**Mưa:**
- Mưa phùn: Bệnh lan nhanh
- Mưa to: Rửa trôi bào tử, giảm bệnh tạm thời

**3. Điều kiện đất đai & canh tác:**
- Ruộng bón **THỪA ĐẠM** (đặc biệt giai đoạn làm đòng): Lá mềm, nhạy cảm
- Gieo sạ dày, tán lá rậm: Ẩm độ vi khí hậu cao
- Giống lúa nhạy cảm
- Ruộng khô hạn: Cây stress, dễ nhiễm bệnh

**II. TRIỆU CHỨNG NHẬN BIẾT CHI TIẾT:**

**1. Đạo ôn lá:**
- **Giai đoạn đầu**: Chấm nhỏ màu xanh xám hoặc nâu nhạt (2-3mm)
- **Giai đoạn phát triển**: Vết mở rộng thành hình **thoi** (mắt én):
  + Chiều dài: 1-1.5cm
  + Chiều rộng: 0.3-0.5cm
  + **Tâm**: Màu xám trắng (mô chết)
  + **Viền**: Nâu đậm hoặc nâu đỏ (ranh giới bệnh)
- **Giai đoạn nặng**: 
  + Nhiều vết liên kết → Lá cháy khô hoàn toàn
  + Khi ẩm độ cao, trên vết bệnh có lớp phấn bào tử màu xám xanh
- **Vị trí**: Thường xuất hiện trên lá già trước, sau lan sang lá non

**2. Đạo ôn cổ bông (NGUY HIỂM NHẤT):**
- **Thời điểm**: 7-10 ngày trước trổ đến chín sữa
- **Triệu chứng**:
  + Vết màu **nâu xám hoặc đen** bao quanh cổ bông (ngay dưới bông)
  + Chiều dài vết: 2-5cm
  + Vết cắt ngang mạch dẫn → Bông thiếu dinh dưỡng
- **Hậu quả**:
  + Bông bạc trắng (nếu bệnh xảy ra sớm giai đoạn làm chắc)
  + Cổ bông gãy, bông rủ xuống
  + Hạt lép lửng 60-100%
  + **Thiệt hại**: 20-80% năng suất (có thể mất trắng)

**3. Đạo ôn đốt thân:**
- Vết nâu đen ở đốt thân (gần mặt đất hoặc đốt trên)
- Thân yếu, dễ gãy đổ
- Ít gặp hơn đạo ôn lá và cổ bông

**III. BIỆN PHÁP PHÒNG TRỪ TÍCH HỢP:**

**A. CANH TÁC (Nền tảng):**

**1. Chọn giống kháng bệnh:**
- **Kháng cao**: Jasmine 85, VNR 20, OM 6976, OM 18
- **Kháng trung bình**: ST25, IR50404, Khang dân
- **Luân canh giống**: Không trồng cùng giống liên tục (tránh nấm kháng)

**2. Bón phân cân đối (QUAN TRỌNG):**
- **CÔNG THỨC**: 90-60-60 kg/ha (N-P2O5-K2O) cho năng suất 5-6 tấn
- **QUY TẮC VÀNG**: 
  + ❌ **TUYỆT ĐỐI KHÔNG** bón thừa đạm giai đoạn làm đòng
  + ✅ Bón **nặng đầu, nhẹ cuối**
  + ✅ Tăng Kali, Silic → Lá cứng, khó nhiễm bệnh
- **KHI BỆNH XUẤT HIỆN**: 
  + 🛑 **NGƯNG BÓN ĐẠM** ngay lập tức
  + 🛑 Không phun thuốc kích thích sinh trưởng, phân bón lá chứa N

**3. Mật độ gieo sạ hợp lý:**
- Sạ dặm: 80-100 kg/ha
- Cấy: 20-25 khóm/m2, mỗi khóm 2-3 cây
- **Mục đích**: Tán lá thoáng → Giảm ẩm độ → Giảm bệnh

**4. Quản lý nước:**
- **KHI BỆNH XUẤT HIỆN**: 
  + ✅ **GIỮ NƯỚC RUỘNG** (3-5cm)
  + ❌ **TUYỆT ĐỐI KHÔNG** để ruộng khô (cây stress nặng thêm)
- Tưới sáng sớm, tránh tưới chiều tối (tăng ẩm đêm)

**5. Vệ sinh đồng ruộng:**
- Thu gom rơm rạ vụ cũ (nấm trú đông trong rơm)
- Tiêu hủy gốc rạ bệnh (đốt hoặc vùi sâu)
- Không để rơm rạ bệnh gần ruộng lúa mới

**B. HÓA HỌC - THUỐC ĐẶC TRỊ:**

**1. ĐẠO ÔN LÁ:**

**Ngưỡng phun**: 1-2 vết bệnh/m2

**Thuốc chính:**

a) **Tricyclazole 75%WP** (Beam 75WP, Trizole 75WP):
- **Liều**: 300-400g/ha
- **Cơ chế**: Ức chế tổng hợp melanin của nấm
- **Ưu điểm**: Hiệu quả cao, chống đạo ôn cổ bông tốt
- **Lưu ý**: Phun phòng ngừa, không chờ bệnh nặng

b) **Isoprothiolane 40%EC** (Fuji-one 40EC):
- **Liều**: 1.5-2 lít/ha
- **Cơ chế**: Ức chế sinh trưởng nấm
- **Ưu điểm**: Tác dụng nhanh, kéo dài 10-14 ngày

c) **Tebuconazole 25%EC** (Folicur 250EC):
- **Liều**: 400-500ml/ha
- **Nhóm**: Triazole - phổ rộng
- **Ưu điểm**: Trị cả đạo ôn, khô vằn, đốm nâu

d) **Azoxystrobin 25%SC** (Amistar 25SC):
- **Liều**: 500ml/ha
- **Nhóm**: Strobilurin - hệ thống
- **Ưu điểm**: Di chuyển trong cây, bảo vệ tốt

**Lịch phun đạo ôn lá:**
- **Lần 1**: Khi xuất hiện 1-2 vết/m2
- **Lần 2**: Sau lần 1 khoảng 7-10 ngày (nếu còn bệnh)
- **Luân phiên hoạt chất**: Tránh kháng thuốc

**2. ĐẠO ÔN CỔ BÔNG (QUAN TRỌNG NHẤT):**

**Quy tắc VÀNG: PHUN PHÒNG NGỪA (không chờ thấy bệnh)**

**Lịch phun BẮT BUỘC 2 lần:**

**🎯 LẦN 1: Khi lúa trổ lẹt xẹt 5-10%**
- **Thời điểm**: Khoảng 7-10 ngày trước khi lúa trổ đều
- **Dấu hiệu**: Một số bông bắt đầu lộ lẹt ra khỏi bẹ lá
- **Thuốc**: 
  + Tricyclazole 75%WP: 400-500g/ha (tăng 30% so với đạo ôn lá)
  + Hoặc: Tebuconazole 400ml/ha + Tricyclazole 300g/ha (kết hợp)

**🎯 LẦN 2: Khi lúa trổ đều 40-60%**
- **Thời điểm**: Sau lần 1 khoảng 7-10 ngày
- **Dấu hiệu**: Phần lớn bông đã trổ
- **Thuốc**: Lặp lại lần 1 hoặc thay đổi hoạt chất

**Lưu ý khi phun:**
- Phun **buổi sáng sớm** (6-9h) hoặc **chiều mát** (16-18h)
- Tránh phun trời nắng gắt, mưa, gió
- Dùng vòi phun áp lực cao, tia nhỏ
- Phun **tập trung vào cổ bông và bẹ lá trên**
- Lượng nước: 200-300 lít/ha

**C. DỰ BÁO VÀ CẢNH BÁO:**

**Điều kiện BẮT BUỘC phun phòng ngừa:**
- Nhiệt độ đêm 18-22°C, ngày 26-30°C
- Độ ẩm >90% kéo dài 2-3 đêm
- Sương mù dày đặc buổi sáng
- Trời âm u, ít nắng
- Lúa giai đoạn làm đòng - trổ bông

**⚠️ CẢNH BÁO ĐỎ (Nguy cơ cực cao):**
- Vụ trước có đạo ôn nặng
- Giống nhạy cảm
- Bón thừa đạm
- Thời tiết âm u, sương mù 3-5 ngày
→ **PHUN NGAY** không cần chờ xuất hiện bệnh

**KẾT LUẬN:**
Đạo ôn là "ung thư" của lúa. Phòng bệnh QUAN TRỌNG hơn chữa bệnh. Đặc biệt đạo ôn cổ bông phải phun phòng ngừa 2 lần bắt buộc.""",

    "khô vằn": """🍂 **BỆNH KHÔ VẰN (ĐỐM VẰN) - *Rhizoctonia solani***

**I. TÁC NHÂN & ĐIỀU KIỆN THỜI TIẾT:**

**1. Nấm gây bệnh:**
- Tên khoa học: *Rhizoctonia solani* Kühn (AG1-IA)
- **Đặc điểm**: Nấm đất, tồn tại dạng **hạch nấm** (sclerotia) trong đất, rơm rạ
- Tuổi thọ hạch: **2-3 năm** trong đất
- Lây lan: Hạch nổi trên mặt nước, dính vào bẹ lá

**2. Điều kiện thời tiết thuận lợi:**

**Nhiệt độ:** 28-32°C (tối ưu 30°C)
- **Dưới 25°C**: Bệnh phát triển chậm
- **28-32°C**: Bệnh phát triển CỰC MẠNH
- **Trên 35°C**: Bệnh giảm

**Độ ẩm không khí:** 96-100%
- **85-95%**: Bệnh nhẹ đến trung bình
- **>96%**: Bệnh bùng phát
- Mưa nhiều, ngập úng kéo dài → Bệnh NẶNG

**Thời tiết đặc trưng:**
- **Nóng ẩm** liên tục 5-7 ngày
- Nhiệt độ ban đêm vẫn cao (>25°C)
- Mưa rải rác, độ ẩm luôn cao
- **Mùa thuận lợi**: Hè Thu (tháng 6-8)

**3. Điều kiện canh tác:**
- Ruộng **sạ dày, cấy dày** → Tán lá rậm, không thoáng
- Mực nước ruộng **ngập sâu** (>10cm), không thoát nước
- Bón **thừa đạm, thiếu kali** → Lá mềm, mô tế bào yếu
- Đất nhiều rơm rạ chưa phân hủy (nơi hạch nấm trú ẩn)
- Cỏ dại bờ ruộng nhiều (nguồn bệnh)

**II. TRIỆU CHỨNG NHẬN BIẾT:**

**1. Giai đoạn đầu:**
- Xuất hiện ở **bẹ lá dưới** sát mặt nước
- Vết bệnh hình **bầu dục**, màu **lục tối thẫm** (thấm nước)
- Kích thước: 0.5-1cm

**2. Giai đoạn phát triển:**
- Vết mở rộng, hình **đám mây** không đều, ranh giới mờ
- Màu sắc: Tâm chuyển **xám trắng**, viền **nâu** rõ ràng
- Hình dạng đặc trưng: **Vằn da hổ** (xám trắng xen lẫn nâu)
- Lan từ bẹ lá lên phiến lá

**3. Dấu hiệu đặc trưng - QUAN TRỌNG:**
- **Hạch nấm**: 
  + Hình tròn dẹt, kích thước 2-5mm
  + Màu: Ban đầu **trắng**, sau chuyển **nâu sẫm đến đen**
  + Vị trí: Dính chặt trên vết bệnh (bẹ lá, phiến lá)
  + Số lượng: Vài hạch đến hàng chục hạch/vết bệnh

**4. Giai đoạn nặng:**
- Toàn bộ bẹ lá và lá chuyển **xám khô**
- Bẹ lá thối, dễ bong ra khỏi thân
- Cây yếu, không đứng vững
- Giảm số bông chắc, hạt lép tăng

**III. TÁC HẠI:**
- Giảm diện tích quang hợp 30-50%
- Giảm số hạt chắc/bông
- **Năng suất giảm**: 10-30% (có thể đến 50% nếu bệnh từ sớm)

**IV. BIỆN PHÁP PHÒNG TRỪ TÍCH HỢP:**

**A. CANH TÁC (Nền tảng - quan trọng nhất):**

**1. Vệ sinh đồng ruộng (BẮT BUỘC):**
- **Dọn cỏ bờ ruộng**: Cỏ là nơi nấm trú ẩn
- **Thu gom rơm rạ cũ**: 
  + Đốt hoặc ủ compost kỹ
  + KHÔNG để rơm rạ bệnh phơi gần ruộng lúa mới
- **Cày lật đất**: Vùi hạch nấm xuống sâu (>15cm)

**2. Quản lý nước (QUYẾT ĐỊNH):**
- **Tưới nước nông**: 2-3cm (không ngập sâu)
- **Thoát nước tốt**: Không để nước đọng lâu
- **KHI BỆNH XUẤT HIỆN**:
  + 🚨 **THÁO NƯỚC** ruộng
  + Để ruộng **khô ráo 3-5 ngày**
  + Hạch nấm và nấm sợi sẽ khô chết
  + Sau đó tưới lại nước nông

**3. Mật độ hợp lý:**
- Sạ dặm: 80-100 kg/ha (KHÔNG sạ quá dày)
- Cấy: 20-25 khóm/m2
- **Mục đích**: Tán lá thoáng → Giảm ẩm độ vi khí hậu

**4. Bón phân cân đối:**
- **Giảm đạm**: Không bón thừa đạm (làm lá mềm)
- **Tăng kali**: 
  + Liều khuyến cáo: 60-80 kg K2O/ha
  + Bón 2 lần: 30% lúc gieo + 70% làm đòng
  + Tác dụng: Lá cứng, chống bệnh
- **Bón silic**:
  + Liều: 100-150 kg/ha (xỉ thép, tro trấu)
  + Thời điểm: Bón lót hoặc thúc 1
  + Tác dụng: Thành tế bào cứng, nấm khó xâm nhập

**B. SINH HỌC:**

**Sử dụng nấm đối kháng *Trichoderma harzianum*:**

**Xử lý hạt giống:**
- Liều: 8-10g bào tử *Trichoderma* /kg hạt
- Cách làm: Trộn đều hạt với bào tử, để 12h rồi gieo

**Tưới vào gốc:**
- Liều: 1-1.5 kg *Trichoderma* /ha
- Pha với phân hữu cơ vi sinh
- Thời điểm: 2 lần
  + Lần 1: 15 ngày sau gieo sạ
  + Lần 2: 30 ngày sau gieo sạ

**Ưu điểm:**
- An toàn, không độc
- Ức chế *Rhizoctonia* trong đất
- Tăng cường sức đề kháng cây

**C. HÓA HỌC - THUỐC ĐẶC TRỊ:**

**Ngưỡng phun**: 5-10% diện tích xuất hiện bệnh

**1. Hexaconazole 5%SC** (Anvil 5SC, VK-Hexa 5SC):
- **Liều**: 500-600ml/ha
- **Cơ chế**: Triazole - ức chế sinh tổng hợp ergosterol của nấm
- **Ưu điểm**: Hiệu quả cao với khô vằn, phổ rộng
- **Thời gian tác dụng**: 15-20 ngày

**2. Validamycin 3%SL** (Validacin 3SL, Valivithaco 3SL):
- **Liều**: 1-1.5 lít/ha
- **Cơ chế**: Kháng sinh sinh học
- **Ưu điểm**: 
  + Đặc trị *Rhizoctonia*
  + An toàn với người, môi trường
  + Không ảnh hưởng thiên địch

**3. Azoxystrobin 25%SC + Difenoconazole 12.5%SC** (Amistar Top 325SC):
- **Liều**: 600-800ml/ha
- **Ưu điểm**: 
  + Phối hợp 2 hoạt chất
  + Trị cả khô vằn, đạo ôn, đốm nâu
  + Hệ thống, bảo vệ toàn cây

**4. Pencycuron 25%SC**:
- **Liều**: 800ml/ha
- **Đặc trị**: *Rhizoctonia*
- **Ưu điểm**: Tác dụng nhanh, kéo dài

**Lịch phun thuốc:**
- **Lần 1**: Khi 5-10% diện tích có bệnh
- **Lần 2**: Sau lần 1 khoảng 7-10 ngày
- **Luân phiên**: Thay đổi hoạt chất giữa các lần

**KỸ THUẬT PHUN (RẤT QUAN TRỌNG):**
- **Phun tập trung vào GỐC LÚA, BẸ LÁ DƯỚI** (nơi nấm sinh sống)
- Không phun lan tràn lên lá
- Vòi phun hướng xuống, áp lực cao
- Lượng nước: 250-300 lít/ha (nhiều hơn phun đạo ôn lá)
- Thời gian: Buổi sáng sớm hoặc chiều mát

**D. DỰ BÁO:**

**Điều kiện CẢNH BÁO bệnh khô vằn:**
- Nhiệt độ 28-32°C kéo dài 5-7 ngày
- Độ ẩm >95%
- Mưa nhiều, ruộng ngập
- Tán lá rậm, kín
- Giai đoạn làm đòng

→ **HÀNH ĐỘNG**: Tháo nước, phun phòng ngừa

**KẾT LUẬN:**
Khô vằn phòng dễ hơn trị. Chìa khóa: **Vệ sinh ruộng + Quản lý nước + Tháo nước khi bệnh xuất hiện**.""",

    "bạc lá": """🦠 **BỆNH BẠC LÁ (CHÁY BÌA LÁ) - *Xanthomonas oryzae***

**I. TÁC NHÂN & ĐIỀU KIỆN THỜI TIẾT:**

**1. Vi khuẩn gây bệnh:**
- Tên khoa học: *Xanthomonas oryzae* pv. *oryzae* (Xoo)
- **Hình dạng**: Hình que, có tiên mao vận động
- **Đặc tính**: Ưa ẩm, sinh sản nhanh ở 25-30°C
- **Nơi trú ẩn**: Hạt giống, rơm rạ, cỏ dại, nước tưới nhiễm bệnh

**2. Con đường xâm nhập:**
- **Qua khí khổng** (thủy khẩu) ở mép lá
- **Qua vết thương cơ giới**: 
  + Do mưa to gió lớn, lá va đập nhau
  + Do côn trùng chích hút (rầy, bọ rùa, nhện gié)
  + Do dụng cụ nông nghiệp (hái lá, băng ruộng)

**3. Điều kiện thời tiết:**

**Nhiệt độ:** 25-30°C (tối ưu 28°C)
- Dưới 20°C: Bệnh phát triển chậm
- 25-30°C: Bệnh phát triển mạnh nhất
- Trên 35°C: Vi khuẩn bị ức chế

**Độ ẩm:** >80%
- 80-90%: Bệnh phát triển trung bình
- >90%: Bệnh bùng phát nhanh

**Thời tiết đặc trưng gây bệnh:**
- **SAU MƯA BÃO, GIÓ LỐC**: 
  + Lá bị rách, vết thương nhiều
  + Vi khuẩn xâm nhập dễ dàng
  + Bệnh xuất hiện sau bão 3-5 ngày
- Mưa rải rác kéo dài
- Độ ẩm cao liên tục

**4. Điều kiện canh tác:**
- **Bón THỪA ĐẠM** (quan trọng nhất):
  + Lá mềm, mô tế bào yếu
  + Vi khuẩn sinh sản mạnh trong mô giàu N
- Nước tưới nhiễm vi khuẩn
- Dụng cụ làm đất không sạch
- Giống lúa nhạy cảm

**II. TRIỆU CHỨNG NHẬN BIẾT:**

**1. Giai đoạn đầu:**
- Xuất hiện các **vệt nhỏ màu xanh tái** (thấm nước) ở **chóp lá** hoặc **hai mép lá**
- Dài 1-2cm, rộng 2-3mm
- Khi chạm thấy ướt, dính

**2. Giai đoạn phát triển:**
- Vệt lan dài theo **hai bên mép lá**, từ chóp xuống gốc
- Màu sắc thay đổi:
  + Vàng nhạt (giai đoạn giữa)
  + **Trắng xám** (giai đoạn muộn) → Gọi là "bạc lá"
- **Ranh giới**: Gợn sóng đặc trưng (KHÔNG thẳng)
- Chiều dài vết: 5-20cm (có thể cả lá)

**3. Dấu hiệu ĐẶC TRƯNG (Chẩn đoán chắc chắn):**
- **Giọt dịch vi khuẩn** (bacterial ooze):
  + **Thời điểm**: Sáng sớm (5-7h), khi có sương
  + **Vị trí**: Ở mép vết bệnh, đầu lá
  + **Hình dạng**: Giọt nhỏ màu **vàng đục** (như keo, sữa)
  + **Cảm giác**: Dính, nhờn
  + **Ý nghĩa**: Đây là khối vi khuẩn tiết ra, lây lan qua nước

**4. Giai đoạn nặng:**
- Toàn bộ lá chuyển trắng bạc, khô héo
- Nhiều lá bị bệnh → Cây yếu
- Giảm khả năng quang hợp
- **Năng suất giảm**: 10-50%

**III. BIỆN PHÁP PHÒNG TRỪ:**

**A. BIỆN PHÁP CẤP BÁCH (KHI BỆNH MỚI XUẤT HIỆN):**

**🚨 BƯỚC 1: NGƯNG BÓN ĐẠM NGAY (BẮT BUỘC)**
- **TUYỆT ĐỐI KHÔNG** bón thêm đạm dưới bất kỳ hình thức nào:
  + Không bón ure
  + Không phun phân bón lá chứa N
  + Không phun thuốc kích thích sinh trưởng
- **Lý do**: Đạm làm mô mềm, vi khuẩn sinh sản nhanh gấp đôi

**🚨 BƯỚC 2: RÚT NƯỚC - KHÔ RUỘNG**
- **Tháo cạn nước ruộng**
- Để ruộng **khô ráo 2-3 ngày**
- **Mục đích**:
  + Giảm độ ẩm → Kìm hãm vi khuẩn
  + Cắt đường lây lan qua nước
  + Lúa sẽ hơi ngả màu vàng nhẹ (bình thường, không sao)
- **Sau đó**: Tưới lại nước nông 2-3cm

**🚨 BƯỚC 3: PHUN THUỐC ĐẶC TRỊ**

**B. CANH TÁC PHÒNG NGỪA:**

**1. Chọn giống kháng bệnh:**
- **Kháng cao**: OM 6976, IR64, Jasmine 85
- **Kháng trung bình**: VNR 20, ST25
- Luân canh giống

**2. Xử lý hạt giống:**
- **Ngâm thuốc Kasugamycin 2%**:
  + Liều: 20ml/lít nước
  + Thời gian: Ngâm hạt 24h
  + Phơi khô rồi gieo
- **Mục đích**: Diệt vi khuẩn trên hạt

**3. Bón phân cân đối:**
- **KHÔNG bón thừa đạm** (quan trọng nhất)
- Tăng kali, silic: Lá cứng, khó nhiễm bệnh
- Bón theo công thức 3 giảm 3 tăng

**4. Vệ sinh:**
- Khử trùng dụng cụ nông nghiệp
- Dọn sạch cỏ dại bờ ruộng
- Không dùng nước tưới từ ruộng bệnh

**C. HÓA HỌC - THUỐC ĐẶC TRỊ VI KHUẨN:**

**1. Bismerthiazol 20%WP** (Xanthomix 20WP, Totan 200WP):
- **Liều**: 500-600g/ha
- **Cơ chế**: Kháng sinh đặc trị *Xanthomonas*
- **Ưu điểm**: Hiệu quả cao nhất với bạc lá
- **Thời gian**: Phun 2-3 lần, cách 7-10 ngày

**2. Oxolinic acid 20%WP** (Starner 20WP):
- **Liều**: 400-500g/ha
- **Cơ chế**: Kháng sinh nhóm Quinolone
- **Ưu điểm**: Hệ thống, di chuyển trong cây

**3. Kasugamycin 2%SL** (Kasumin 2SL):
- **Liều**: 1-1.5 lít/ha
- **Cơ chế**: Kháng sinh aminoglycoside
- **Ưu điểm**: An toàn, có thể xử lý hạt

**4. Copper hydroxide 77%WP** (Kocide 77WP):
- **Liều**: 1kg/ha
- **Cơ chế**: Thuốc đồng, diệt khuẩn tiếp xúc
- **Ưu điểm**: Rẻ, dễ kiếm

**5. Ningnanmycin 8%AS**:
- **Liều**: 300ml/ha
- **Cơ chế**: Kháng sinh thực vật
- **Ưu điểm**: Tăng sức đề kháng cây

**Lịch phun:**
- **Lần 1**: Ngay khi phát hiện bệnh
- **Lần 2**: Sau lần 1 khoảng 7 ngày
- **Lần 3**: Sau lần 2 khoảng 7 ngày (nếu còn bệnh)
- **Luân phiên hoạt chất**: Tránh kháng thuốc

**KỸ THUẬT PHUN:**
- Phun buổi sáng sớm (6-9h) hoặc chiều mát
- Áp lực cao, phun đều cả 2 mặt lá
- Lượng nước: 200-300 lít/ha

**⚠️ LƯU Ý CỰC KỲ QUAN TRỌNG:**
- ❌ **TUYỆT ĐỐI KHÔNG** phun phân bón lá khi lúa đang bị bạc lá
- ❌ Không phun thuốc kích thích sinh trưởng
- ❌ Không tưới nước sâu ngập cây
- ✅ **BẮT BUỘC** kết hợp: Rút nước + Ngưng đạm + Phun thuốc

**D. DỰ BÁO:**

**Điều kiện CẢNH BÁO bệnh bạc lá:**
- Sau bão, gió lớn 3-5 ngày
- Nhiệt độ 25-30°C, độ ẩm >85%
- Ruộng bón nhiều đạm
- Giai đoạn đẻ nhánh - làm đòng

→ **HÀNH ĐỘNG**: Kiểm tra ruộng hàng ngày, sẵn sàng phun thuốc

**KẾT LUẬN:**
Bạc lá vi khuẩn khó trị nhưng dễ phòng. Chìa khóa: **Không thừa đạm + Rút nước khi bệnh + Phun thuốc kháng sinh sớm**.""",

    "lem lép hạt": """⚫ **BỆNH LEM LÉP HẠT (HẠT ĐEN, HẠT LÉP)**

**I. NGUYÊN NHÂN PHỨC HỢP:**

**1. Nhóm Nấm gây bệnh:**

a) ***Fusarium graminearum*** (chủ yếu):
- Gây vết đốm **hồng tím** trên hạt
- Tiết độc tố DON (Deoxynivalenol) - độc với người và vật nuôi
- Phát triển mạnh ở 25-30°C, ẩm độ cao

b) ***Curvularia lunata***:
- Gây vết đốm **nâu đen** hình vòng cung
- Hạt chuyển màu xám đen

c) ***Alternaria padwickii***:
- Gây vết đốm **đen** rải rác
- Hạt đen hoàn toàn

d) ***Bipolaris oryzae***:
- Gây đốm nâu nhỏ như hạt mè
- Thường đi kèm bệnh đốm nâu lá

**2. Nhóm Vi khuẩn gây bệnh:**

a) ***Burkholderia glumae*** (lép vàng):
- Gây **lép vàng**: Vỏ trấu vàng rơm, hạt lép kẹp
- Nhánh gié đứng thẳng (bắn máy bay)
- Hạt có mùi hôi tanh

b) ***Burkholderia gladioli***:
- Gây thối hạt
- Vỏ trấu nâu đen, hạt thối

c) ***Xanthomonas oryzae***:
- Gây **thối đen hạt**
- Vỏ trấu đen, hạt đen

**3. Điều kiện thời tiết:**

**Giai đoạn nhạy cảm**: **Trổ bông - làm chắc hạt**

**Nhiệt độ:**
- **>32°C** giai đoạn trổ bông: Vi khuẩn phát triển mạnh (lép vàng)
- **25-30°C** + ẩm độ cao: Nấm phát triển (hạt đen)
- **Chênh lệch nhiệt độ ngày-đêm lớn**: Stress, dễ nhiễm bệnh

**Độ ẩm & mưa:**
- **Mưa nhiều** giai đoạn trổ bông: Nấm lây lan qua giọt mưa
- **Độ ẩm >90%** khi làm chắc hạt: Nấm xâm nhập hạt
- **Nắng nóng xen mưa**: Lý tưởng cho vi khuẩn

**Gió:**
- Gió lan truyền bào tử nấm
- Gió mạnh làm hoa không thụ phấn → Hạt lép cơ học (không phải bệnh)

**4. Điều kiện canh tác:**
- Bón **thừa đạm** cuối vụ: Hạt mềm, dễ nhiễm
- **Thiếu nước** giai đoạn làm chắc: Cây stress
- Giống nhạy cảm
- Hạt giống nhiễm bệnh

**II. TRIỆU CHỨNG PHÂN BIỆT:**

**1. Hạt đen (do nấm):**
- Vỏ trấu có đốm **nâu, tím, đen** rải rác hoặc toàn bộ
- **Hình dạng đốm**: 
  + *Fusarium*: Hồng tím, thường ở đầu hạt
  + *Curvularia*: Nâu đen hình vòng cung
  + *Alternaria*: Đen toàn bộ hạt
- **Hạt bên trong**: Lép hoặc lửng, gạo đục, dễ vỡ
- **Mùi**: Hơi mốc

**2. Lép vàng (do vi khuẩn *Burkholderia*):**
- Vỏ trấu **vàng rơm** bình thường (KHÔNG đổi màu bất thường)
- Hạt **lép kẹp** hoàn toàn
- Nhánh gié **đứng thẳng** (không rủ xuống như bình thường)
- **Mùi hôi tanh** đặc trưng (khi bóp hạt)
- Thường xuất hiện thành đám trên ruộng

**3. Thối hạt (do vi khuẩn *Burkholderia gladioli*, *Xanthomonas*):**
- Vỏ trấu **nâu đen**, mục nát
- Hạt bên trong **thối**, có dịch nhầy
- Mùi hôi nồng

**4. Than vàng (do nấm *Ustilaginoidea virens*):**
- Hạt biến thành **khối bào tử** to như hạt ngô
- Màu **vàng cam** (giai đoạn non)
- Chuyển **xanh đen** (giai đoạn già)
- Dễ phân biệt, không nhầm với lem lép

**III. BIỆN PHÁP PHÒNG TRỪ:**

**A. NGUYÊN TẮC VÀNG:**
**"PHÒNG" quan trọng hơn "TRỊ" gấp 100 lần**

**Bệnh lem lép hạt KHÔNG THỂ chữa khi đã xuất hiện, chỉ có thể PHÒNG NGỪA**

**B. CANH TÁC:**

**1. Lịch thời vụ:**
- Gieo sạ **đúng thời vụ**
- Tránh giai đoạn trổ trùng:
  + Mưa nhiều (tháng 7-8 miền Bắc)
  + Nắng nóng gay gắt (>35°C)

**2. Quản lý nước:**
- **Giai đoạn trổ - làm chắc**: 
  + Giữ nước ruộng **đầy đủ** (3-5cm)
  + **KHÔNG để ruộng khô hạn** (cây stress, vi khuẩn phát triển)
- Tưới nước **buổi sáng sớm**, tránh tưới chiều tối

**3. Bón phân:**
- **TUYỆT ĐỐI KHÔNG** bón đạm cuối vụ (sau làm đòng)
- Bón đủ **Kali**: 60-80 kg K2O/ha (hạt chắc, cứng)
- Bón **Silic**: Tăng sức đề kháng

**4. Xử lý hạt giống:**
- Chọn hạt no, chắc từ ruộng không bệnh
- Ngâm hạt với thuốc:
  + *Thiram* hoặc *Mancozeb*: 2g/kg hạt
  + Phơi khô rồi gieo

**C. HÓA HỌC - PHUN PHÒNG NGỪA (QUAN TRỌNG NHẤT):**

**🎯 THỜI ĐIỂM VÀNG - BẮT BUỘC PHUN 2 LẦN:**

**LẦN 1: Khi lúa trổ lẹt xẹt 5-10%**
- **Thời điểm**: Khoảng 7 ngày trước khi lúa trổ đều
- **Dấu hiệu**: 5-10% bông bắt đầu lộ ra
- **MỤC ĐÍCH**: 
  + Bảo vệ hoa khỏi nhiễm nấm/khuẩn khi thụ phấn
  + Phòng ngừa TRƯỚC, không chờ thấy bệnh

**LẦN 2: Khi lúa trổ đều 50-60%**
- **Thời điểm**: Sau lần 1 khoảng 7-10 ngày
- **Dấu hiệu**: Phần lớn bông đã trổ
- **MỤC ĐÍCH**: 
  + Bảo vệ hạt non đang làm chắc
  + Diệt nấm/khuẩn còn tồn dư

**CÔNG THỨC THUỐC - PHỐI HỢP TRỪ NẤM & KHUẨN:**

**Phương án 1 (Khuyến cáo):**
- **Azoxystrobin 25%SC + Difenoconazole 12.5%SC** (Amistar Top 325SC): 600ml/ha
  + Trị nấm phổ rộng (*Fusarium, Curvularia, Alternaria*)
- **+** **Kasugamycin 2%SL**: 1 lít/ha
  + Trị vi khuẩn (*Burkholderia, Xanthomonas*)

**Phương án 2:**
- **Propiconazole 25%EC** (Tilt Super 300EC): 500ml/ha
  + Trị nấm
- **+** **Bismerthiazol 20%WP** (Xanthomix): 500g/ha
  + Trị vi khuẩn

**Phương án 3:**
- **Tebuconazole 25%EC**: 500ml/ha
  + Trị nấm
- **+** **Oxolinic acid 20%WP** (Starner): 400g/ha
  + Trị vi khuẩn

**KỸ THUẬT PHUN:**
- Phun vào **buổi sáng sớm** (6-8h) hoặc **chiều mát** (16-18h)
- **TUYỆT ĐỐI TRÁNH** phun trời nắng gắt, mưa
- Phun **tập trung vào bông** (nơi hạt đang hình thành)
- Vòi phun hướng lên, áp lực cao
- Lượng nước: 200-300 lít/ha
- Dùng nước sạch

**⚠️ LƯU Ý CỰC KỲ QUAN TRỌNG:**
- ✅ **PHUN PHÒNG NGỪA** (không chờ thấy bệnh mới phun)
- ✅ **2 LẦN BẮT BUỘC** (thiếu lần nào cũng giảm hiệu quả 50%)
- ❌ Không phun khi hạt đã chín (vô dụng)
- ❌ Không phun 1 lần rồi bỏ (hiệu quả thấp)

**D. LUÂN PHIÊN HOẠT CHẤT:**

**Vụ 1**: Azoxystrobin + Difenoconazole + Kasugamycin
**Vụ 2**: Tebuconazole + Bismerthiazol
**Vụ 3**: Propiconazole + Oxolinic acid
**Vụ 4**: Trở lại Vụ 1

**IV. DỰ BÁO VÀ CẢNH BÁO:**

**Điều kiện CẢNH BÁO ĐỎ (Nguy cơ cực cao):**
- Nhiệt độ >32°C giai đoạn trổ bông
- Mưa nhiều, ẩm độ >90% khi làm chắc hạt
- Vụ trước có lem lép nặng
- Hạt giống từ ruộng bệnh
- Giống nhạy cảm

→ **HÀNH ĐỘNG**: 
- Phun phòng ngừa 2 lần BẮT BUỘC
- Tăng liều thuốc 20-30%
- Có thể phun lần 3 (khi trổ 80%)

**V. TÁC HẠI:**
- **Giảm tỷ lệ hạt chắc**: 15-40% (có thể đến 60%)
- **Giảm khối lượng 1000 hạt**: 10-30%
- **Giảm chất lượng gạo**: 
  + Gạo đục, dễ gãy
  + Độ xát trắng kém
  + Giá bán giảm 10-20%
- **Độc tố**: Nấm *Fusarium* tiết DON độc với người

**KẾT LUẬN:**
Lem lép hạt = "sát thủ thầm lặng" của năng suất. Không thể chữa, chỉ có thể **phòng ngừa bằng cách phun thuốc 2 lần đúng thời điểm (trổ 5-10% và trổ 50-60%)**. Đây là **BẮT BUỘC**, không phải khuyến cáo.""",

    "vàng lùn": """⚠️ **BỆNH VÀNG LÙN & LÙN XOẮN LÁ (VIRUS)**

**⚠️ CẢNH BÁO: KHÔNG CÓ THUỐC ĐẶC TRỊ VIRUS**

**I. TÁC NHÂN:**

**1. Virus gây bệnh:**

a) **Rice Grassy Stunt Virus (RGSV)** - Virus vàng lùn:
- Nhóm: Tenuivirus
- Hạt virus hình que, kích thước 3-10 nm

b) **Rice Ragged Stunt Virus (RRSV)** - Virus lùn xoắn lá:
- Nhóm: Oryzavirus  
- Hạt virus hình cầu đa diện, kích thước 65-70 nm

**2. Côn trùng truyền bệnh (Môi giới - Vector):**

**Rầy nâu** (*Nilaparvata lugens*) - MÔI GIỚI CHÍNH:
- **Cách lây**: 
  + Rầy chích hút cây lúa bệnh → Virus vào cơ thể rầy
  + Virus nhân lên trong cơ thể rầy
  + Rầy bay sang cây khỏe, chích hút → Truyền virus vào lúa
- **Thời gian ủ bệnh trong rầy**: 7-14 ngày
- **Khả năng lây**: 1 con rầy nhiễm virus có thể lây bệnh **suốt đời**
- **Giai đoạn lúa nhạy cảm**: Sạ - đẻ nhánh (nếu nhiễm sớm = mất trắng 100%)

**Rầy xanh** (*Nephotettix virescens*) - Môi giới phụ:
- Truyền RRSV (lùn xoắn lá)
- Ít gặp hơn rầy nâu

**II. TRIỆU CHỨNG PHÂN BIỆT:**

**1. BỆNH VÀNG LÙN (RGSV):**

**Lá:**
- Chuyển màu **vàng nhạt đến vàng cam** (khác với vàng do thiếu đạm - vàng xanh)
- Vàng từ **chóp lá** lan dần xuống gốc
- Lá **xòe ngang** (không đứng như lá khỏe)
- Lá **mềm, nhão**, không cứng
- Có thể có **sọc vàng** dọc theo gân lá

**Thân:**
- Cây **thấp lùn** so với cây bình thường (chênh lệch 20-40cm)
- **Đẻ nhánh bất thường**: 
  + Nhiều nhánh nhỏ, yếu (đẻ nhánh vô hiệu)
  + Nhánh mọc lộn xộn, không đều
- Thân **mềm, dễ gãy**

**Rễ:**
- **Rễ thối màu nâu đen** (dấu hiệu quan trọng)
- Hệ rễ kém phát triển, ngắn
- Không có rễ trắng mới

**Bông:**
- **Không trổ bông** hoặc trổ rất muộn, bông lùn
- Nếu trổ thì hạt **lép 100%**

**Thời điểm xuất hiện:** 20-30 ngày sau nhiễm virus

**2. BỆNH LÙN XOẮN LÁ (RRSV):**

**Lá:**
- Màu **xanh đậm BẤT THƯỜNG** (KHÔNG vàng như vàng lùn)
- Lá **ngắn, xoăn tít** như lò xo
- **Gân lá sưng phồng**, nhấp nhô (dấu hiệu đặc trưng - gọi là "gân lá bướu")
- Lá mọc **không đều**, lệch phía
- Lá **cứng, giòn** (khác vàng lùn - lá mềm)

**Thân:**
- Cây **lùn** (thấp hơn 30-50% so với bình thường)
- Đẻ nhánh **lộn xộn**, không đều
- Thân **cứng hơn** vàng lùn

**Bông:**
- **Không trổ bông** (phổ biến nhất)
- Hoặc trổ nhưng bông **lùn, xấu, hạt lép**

**Thời điểm xuất hiện:** 15-25 ngày sau nhiễm virus

**3. BẢNG SO SÁNH:**

| Đặc điểm | Vàng lùn (RGSV) | Lùn xoắn lá (RRSV) |
|----------|-----------------|---------------------|
| Màu lá | Vàng cam | Xanh đậm |
| Hình dạng lá | Vàng, mềm, xòe ngang | Xoắn tít, cứng |
| Gân lá | Bình thường | Sưng phồng (bướu sọc) |
| Rễ | Thối nâu đen | Ít thối hơn |
| Thân | Mềm, dễ gãy | Cứng hơn |

**III. ĐIỀU KIỆN PHÁT TRIỂN:**

**1. Nguồn bệnh:**
- Cây lúa bệnh vụ trước (virus tồn tại trong cây)
- Cỏ dại họ Lúa (virus trú ẩn)
- Rầy nâu mang virus bay nhập cư từ vùng khác

**2. Thời tiết:**
- Nhiệt độ 25-30°C: Rầy phát triển mạnh
- Gió Tây Nam (tháng 4-6): Rầy bay nhập cư hàng loạt
- **VỤ MÙA (Hè Thu)**: Bệnh nặng nhất (rầy nhiều)
- **Vụ Đông Xuân**: Bệnh nhẹ hơn (rầy ít)

**3. Canh tác:**
- Gieo sạ sớm hoặc muộn (trùng đợt rầy bay về)
- Giống nhạy cảm với rầy
- Bón thừa đạm (rầy ưa thích)

**IV. BIỆN PHÁP QUẢN LÝ (KHÔNG CÓ THUỐC TRỊ):**

**⚠️ LƯU Ý: Virus KHÔNG CÓ THUỐC TRỊ, chỉ có thể:**
1. Tiêu hủy cây bệnh (cắt nguồn lây)
2. Diệt rầy nâu (diệt môi giới)
3. Phòng ngừa (giống kháng, thời vụ)

**A. TIÊU HỦY NGUỒN BỆNH (QUAN TRỌNG NHẤT):**

**QUY TRÌNH BẮT BUỘC:**

**Bước 1: Phát hiện cây bệnh**
- Thăm đồng **2 lần/tuần**
- Phát hiện **1 cây bệnh** = Hành động ngay

**Bước 2: Nhổ bỏ cây bệnh**
- **Nhổ cả rễ** (không để gốc rạ)
- Nhổ cả **khóm lân cận** (bán kính 0.5m) - có thể đã nhiễm nhưng chưa biểu hiện

**Bước 3: Cho vào bao nilon kín**
- **MỤC ĐÍCH**: Không để rầy bay ra (rầy trên cây bệnh mang virus)
- **CẤM tuyệt đối**: Để cây bệnh phơi ngoài đồng, vứt bờ ruộng

**Bước 4: Tiêu hủy**
- **Cách 1**: Vùi sâu dưới đất **>50cm**
- **Cách 2**: Đốt (nếu được phép)
- **KHÔNG**: Ủ compost (virus còn sống lâu)

**Tần suất:** Kiểm tra và nhổ bỏ **LIêN TỤC** suốt vụ

**B. PHÒNG TRỪ RẦY NÂU (MÔI GIỚI):**

**1. Giám sát rầy:**
- **Cách kiểm tra**: Vạch gốc lúa, quan sát bẹ lá dưới
- **Tần suất**: 2 lần/tuần
- **Ngưỡng phun**: 
  + Giai đoạn sạ - đẻ nhánh: >5 con/khóm
  + Giai đoạn làm đòng - trổ: >3 con/khóm

**2. Thuốc trừ rầy:**

**Nhóm 1: Ức chế sinh trưởng (An toàn, ưu tiên):**

a) **Pymetrozine 50%WG** (Chess 50WG):
- **Liều**: 200-300g/ha
- **Cơ chế**: Rầy ngừng hút nhực sau 2-4h → Chết đói sau 3-5 ngày
- **Ưu điểm**: 
  + An toàn cho thiên địch (nhện, bọ rùa, ong)
  + Không gây kháng nhanh
- **Thời điểm**: Khi rầy mật độ trung bình

b) **Buprofezin 25%SC** (Applaud 25SC):
- **Liều**: 600-800ml/ha
- **Cơ chế**: Ức chế lột xác → Rầy non chết
- **Ưu điểm**: Bảo vệ thiên địch
- **Kết hợp**: Dùng cùng Chess (Chess diệt rầy trưởng thành, Applaud diệt rầy non)

**Nhóm 2: Diệt nhanh (Khi rầy quá nhiều - khẩn cấp):**

a) **Nitenpyram 10%SL** (Satori 10SL):
- **Liều**: 300-400ml/ha
- **Cơ chế**: Tác động thần kinh → Rầy chết trong vài giờ
- **Thời điểm**: Mật độ rầy cao >5 con/khóm

b) **Dinotefuran 20%SG**:
- **Liều**: 200g/ha
- **Ưu điểm**: Hệ thống, di chuyển nhanh trong cây

c) **Imidacloprid 25%WP**:
- **Liều**: 150-200g/ha
- **Lưu ý**: Có thể giết thiên địch, dùng khi cần thiết

**Lịch phun rầy (Vụ Hè Thu - nhiều rầy):**
- **Lần 1 (Sạ 15-20 NSS)**: Chess 200g/ha
- **Lần 2 (Sạ 30-35 NSS)**: Applaud 600ml/ha
- **Lần 3 (Nếu rầy còn nhiều)**: Nitenpyram 400ml/ha

**Kỹ thuật phun:**
- Phun **dồn xuống gốc lúa** (rầy ở bẹ lá dưới)
- Phun buổi **chiều** (15-17h) - rầy hoạt động
- Áp lực cao, nước sạch
- **Luân phiên hoạt chất** (tránh kháng thuốc)

**C. KỸ THUẬT "NÉ RẦY":**

**Nguyên lý:** Tránh gieo sạ trùng đợt rầy bay nhập cư cao điểm

**Lịch thời vụ an toàn (Miền Bắc):**

**Vụ Đông Xuân:**
- **Gieo sạ**: Tháng 12 - Tháng 1
- **Nguy cơ rầy**: THẤP (rầy ít, nhiệt độ thấp)

**Vụ Hè Thu:**
- **Gieo sạ SỚM**: Trước ngày **20/4**
  + Lúa trổ trước khi rầy bay về
- **Gieo sạ MUỘN**: Sau ngày **15/5**
  + Lúa còn nhỏ khi rầy bay về
- **⚠️ TRÁNH**: **25/4 - 10/5** 
  + Cao điểm rầy bay nhập cư theo gió Tây Nam
  + Lúa giai đoạn đẻ nhánh (nhạy cảm nhất)

**D. CHỌN GIỐNG KHÁNG RẦY:**

**Giống kháng rầy nâu cao:**
- IR64, IR42, IR50404
- OM 9577, OM 9582
- Khang dân 18

**Giống kháng trung bình:**
- ST25, VNR 20, DT8
- Jasmine 85

**Nguyên tắc:** Luân canh giống (không trồng cùng giống liên tục - tránh rầy kháng)

**V. PHƯƠNG ÁN TỔNG HỢP IPM:**

**Trước gieo (Chuẩn bị):**
- Chọn giống kháng rầy
- Tính toán thời vụ "né rầy"
- Dọn sạch cỏ dại họ Lúa (nguồn virus)

**Gieo 10-20 NSS:**
- Kiểm tra rầy lần đầu
- Phun Chess nếu >5 con/khóm

**20-40 NSS (Giai đoạn nguy hiểm):**
- Tuần tra **2 lần/tuần**
- Phát hiện cây vàng lùn/lùn xoắn → Nhổ ngay
- Kiểm tra rầy, phun nếu cần

**40 NSS - Trổ:**
- Tiếp tục kiểm tra rầy
- Phun phòng ngừa nếu mật độ cao

**Sau thu hoạch:**
- Vùi gốc rạ sâu (không đốt - mất hữu cơ)
- Không để rầy trú ẩn qua vụ

**VI. TÁC HẠI:**
- Cây nhiễm sớm (sạ - đẻ nhánh): **Mất trắng 100%**
- Cây nhiễm muộn (làm đòng): Giảm năng suất 30-60%
- Lây lan nhanh: 1 cây bệnh → 100 cây sau 2 tuần (nếu rầy nhiều)

**KẾT LUẬN:**
Bệnh virus = **KHÔNG CÓ THUỐC TRỊ**. Giải pháp duy nhất: 
1. **NHỔ BỎ cây bệnh** ngay (cắt nguồn lây)
2. **TRỪ RẦY NÂU** triệt để (diệt môi giới)
3. **CHỌN GIỐNG + THỜI VỤ** phù hợp (phòng ngừa)

**Phát hiện sớm = Cứu vụ mùa**.""",

    "đốm nâu": """🟤 **BỆNH ĐỐM NÂU (TIÊM LỬA) - *Bipolaris oryzae***

**I. TÁC NHÂN & ĐIỀU KIỆN:**

**1. Nấm gây bệnh:**
- Tên khoa học: *Bipolaris oryzae* (syn. *Helminthosporium oryzae*)
- Nấm bào tử, lây lan qua gió, mưa

**2. Điều kiện thời tiết:**
- Nhiệt độ: 25-30°C
- Độ ẩm: >85%
- Mưa nhiều, ẩm ướt kéo dài

**3. Điều kiện đất đai (QUAN TRỌNG NHẤT):**
- **Đất nghèo dinh dưỡng**: Thiếu NPK, đặc biệt **thiếu Kali**
- **Đất phèn, chua**: pH < 5.5
- **Đất thiếu Silic**: Lá mỏng, yếu
- **Đất thiếu vi lượng**: Thiếu Zn, Mn, Fe

**II. TRIỆU CHỨNG:**
- Vết bệnh hình **tròn hoặc bầu dục**, màu **nâu đậm**
- Kích thước: Nhỏ như **hạt mè** (2-3mm) đến 1cm
- Viền vết: Màu **vàng nhạt**
- Nhiều vết → Lá vàng, khô
- Hạt bị nhiễm: Đốm nâu đen, gạo đục

**III. BIỆN PHÁP PHÒNG TRỪ:**

**A. Cải tạo đất (NỀN TẢNG):**

**1. Bón vôi (đất chua):**
- Liều: **300-500 kg vôi bột/ha**
- Thời điểm: **15-20 ngày TRƯỚC gieo sạ**
- Rải đều, bừa trộn đất

**2. Bón phân hữu cơ:**
- Liều: **2-3 tấn phân chuồng/ha**
- Cải thiện cấu trúc đất, tăng độ phì

**3. Bón Kali:**
- **TĂNG 20-30%** so với khuyến cáo
- Công thức: 80-90 kg K2O/ha (thay vì 60)
- Bón 2 lần: 30% lúc gieo + 70% làm đòng

**4. Bón Silic:**
- Nguồn: Xỉ thép, tro trấu, phân silic
- Liều: **100-150 kg/ha**
- Thời điểm: Bón lót hoặc thúc 1
- **Tác dụng**: Lá dày, cứng → Nấm khó xâm nhập

**B. Thuốc trị:**
- **Propiconazole**: 400-500ml/ha
- **Difenoconazole**: 300-400ml/ha
- **Tebuconazole**: 500ml/ha

**KẾT LUẬN:**
Đốm nâu = Dấu hiệu **đất nghèo**. Giải pháp: Cải tạo đất (vôi + Kali + Silic)."""
}

# Mapping từ khóa để tìm kiếm tốt hơn
KEYWORD_MAPPING = {
    "cháy lá": "đạo ôn",
    "cổ bông": "đạo ôn",
    "thối cổ gié": "đạo ôn",
    "mắt én": "đạo ôn",
    "đốm vằn": "khô vằn",
    "lở cổ rễ": "khô vằn",
    "cháy bìa": "bạc lá",
    "bìa lá": "bạc lá",
    "lép hạt": "lem lép hạt",
    "lép vàng": "lem lép hạt",
    "đen hạt": "lem lép hạt",
    "hạt đen": "lem lép hạt",
    "xoăn lá": "vàng lùn",
    "lùn lúa": "vàng lùn",
    "virus": "vàng lùn",
    "tiêm lửa": "đốm nâu",
    "nhiệt độ": "thời tiết",
    "thời tiết": "thời tiết",
    "độ ẩm": "thời tiết",
    "mưa": "thời tiết"
}

def tim_tra_loi(cau_hoi):
    """Tìm kiếm câu trả lời trong cơ sở tri thức"""
    cau_hoi = cau_hoi.lower()
    
    # Kiểm tra yêu cầu thời tiết
    if any(word in cau_hoi for word in ["thời tiết", "nhiệt độ", "độ ẩm", "mưa", "gió", "khí hậu"]):
        thoi_tiet = lay_thoi_tiet()
            
        return f"""🌤️ **THÔNG TIN THỜI TIẾT {thoi_tiet['thanh_pho'].upper()}**
        
📍 **Vị trí:** {thoi_tiet['thanh_pho']}, Việt Nam
🕐 **Thời gian:** {datetime.now().strftime("%d/%m/%Y %H:%M")}

🌡️ **Nhiệt độ:** {thoi_tiet['nhiet_do']}°C (Cảm giác như {thoi_tiet['cam_giac']}°C)
💧 **Độ ẩm:** {thoi_tiet['do_am']}%
🌪️ **Gió:** {thoi_tiet['gio']} km/h
☁️ **Mây:** {thoi_tiet['may']}%
🔽 **Áp suất:** {thoi_tiet['ap_suat']} hPa
📝 **Tình trạng:** {thoi_tiet['mo_ta']}

---

**🌾 ĐÁNH GIÁ NGUY CƠ BỆNH HẠI:**

**Đạo ôn:**
- Nhiệt độ tối ưu: 20-28°C (Hiện tại: {thoi_tiet['nhiet_do']}°C)
- Độ ẩm cần: >90% (Hiện tại: {thoi_tiet['do_am']}%)
- **Nguy cơ:** {"CAO" if 20 <= thoi_tiet['nhiet_do'] <= 28 and thoi_tiet['do_am'] > 90 else "TRUNG BÌNH" if thoi_tiet['do_am'] > 85 else "THẤP"}

**Khô vằn:**
- Nhiệt độ tối ưu: 28-32°C (Hiện tại: {thoi_tiet['nhiet_do']}°C)
- Độ ẩm cần: >96% (Hiện tại: {thoi_tiet['do_am']}%)
- **Nguy cơ:** {"CAO" if 28 <= thoi_tiet['nhiet_do'] <= 32 and thoi_tiet['do_am'] > 96 else "TRUNG BÌNH" if thoi_tiet['do_am'] > 85 else "THẤP"}

**Bạc lá:**
- Nhiệt độ tối ưu: 25-30°C (Hiện tại: {thoi_tiet['nhiet_do']}°C)
- Độ ẩm cần: >80% (Hiện tại: {thoi_tiet['do_am']}%)
- **Nguy cơ:** {"CAO" if 25 <= thoi_tiet['nhiet_do'] <= 30 and thoi_tiet['do_am'] > 80 else "TRUNG BÌNH" if thoi_tiet['do_am'] > 70 else "THẤP"}

💡 **Khuyến nghị:** {
    "Điều kiện thuận lợi cho bệnh phát triển. Kiểm tra ruộng hàng ngày, chuẩn bị thuốc phun phòng ngừa." 
    if thoi_tiet['do_am'] > 85 else 
    "Thời tiết ổn định. Tiếp tục theo dõi."
}"""
    
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
    
🔬 **Tôi chuyên sâu về các bệnh hại lúa:**
- Bệnh Đạo ôn (Cháy lá, Mắt én)
- Bệnh Khô vằn (Đốm vằn)
- Bệnh Bạc lá (Cháy bìa lá)
- Bệnh Lem lép hạt (Hạt đen, Lép vàng)
- Bệnh Vàng lùn & Lùn xoắn lá (Virus)
- Bệnh Đốm nâu (Tiêm lửa)

🌤️ **Thông tin thời tiết:**
- Hỏi: "Thời tiết hôm nay thế nào?"

💬 **Ví dụ câu hỏi:**
- "Triệu chứng bệnh đạo ôn là gì?"
- "Thuốc trị bạc lá vi khuẩn?"
- "Cách phòng khô vằn?"
- "Thời tiết Thanh Hóa?"
    
📚 **Nguồn:** Cục BVTV, Viện Lúa ĐBSCL, IRRI, Tài liệu 2024-2025"""

# ==============================================================================
# 2. DỮ LIỆU CHẨN ĐOÁN HÌNH ẢNH
# ==============================================================================

DATA_HINH_ANH = {
    "Bacterial Leaf Blight": {
        "ten_viet": "BỆNH BẠC LÁ (CHÁY BÌA LÁ)",
        "ten_khoa_hoc": "Xanthomonas oryzae pv. oryzae",
        "mo_ta_ngan": "Vết bệnh là các sọc thấm nước ở mép lá, sau chuyển sang vàng hoặc trắng xám. Rìa vết bệnh lượn sóng. Sáng sớm thường thấy giọt dịch vi khuẩn màu vàng đục.",
        "xu_ly_cap_cuu": "🚨 **HÀNH ĐỘNG KHẨN CẤP:** Ngưng bón đạm ngay, tháo cạn nước ruộng để khô 2-3 ngày nhằm kìm hãm vi khuẩn lây lan.",
        "thuoc_dac_tri": "Bismerthiazol (Xanthomix 500g/ha), Oxolinic acid (Starner 400g/ha), Kasugamycin (Kasumin 1 lít/ha)",
        "luu_y": "Tuyệt đối không phun phân bón lá hoặc thuốc kích thích khi đang có bệnh."
    },
    "Blast": {
        "ten_viet": "BỆNH ĐẠO ÔN (CHÁY LÁ)",
        "ten_khoa_hoc": "Pyricularia oryzae",
        "mo_ta_ngan": "Vết bệnh hình thoi (mắt én), tâm màu xám trắng, viền nâu đậm. Đạo ôn cổ bông gây vết nâu xám bao quanh cổ bông, làm bông gãy gục.",
        "xu_ly_cap_cuu": "🛑 **LƯU Ý:** Giữ nước ruộng ổn định, ngưng bón đạm. Tuyệt đối không để ruộng bị khô hạn khi đang nhiễm bệnh.",
        "thuoc_dac_tri": "Tricyclazole (Beam 300-400g/ha), Isoprothiolane (Fuji-one 1.5 lít/ha), Tebuconazole (Folicur 400ml/ha)",
        "luu_y": "Phun phòng ngừa đạo ôn cổ bông 2 lần: khi lúa trổ lẹt xẹt 5% và khi trổ đều."
    },
    "Brown Spot": {
        "ten_viet": "BỆNH ĐỐM NÂU (TIÊM LỬA)",
        "ten_khoa_hoc": "Bipolaris oryzae",
        "mo_ta_ngan": "Nhiều đốm tròn nhỏ màu nâu như hạt mè rải rác trên lá. Viền vết màu vàng nhạt. Hạt bị nhiễm có đốm nâu đen.",
        "xu_ly_cap_cuu": "🚜 **CẢI TẠO ĐẤT:** Bón vôi (300-500kg/ha) để hạ phèn, bón bổ sung Kali và Silic để tăng sức đề kháng cho cây.",
        "thuoc_dac_tri": "Propiconazole (Tilt Super 500ml/ha), Difenoconazole (300ml/ha), Tebuconazole (500ml/ha)",
        "luu_y": "Bệnh thường là dấu hiệu của đất nghèo dinh dưỡng hoặc đất phèn mặn."
    },
    "Tungro": {
        "ten_viet": "BỆNH DO VIRUS (VÀNG LÙN/LÙN XOẮN LÁ)",
        "ten_khoa_hoc": "Rice Grassy Stunt Virus (RGSV) & Rice Ragged Stunt Virus (RRSV)",
        "mo_ta_ngan": "Lá vàng cam, cây thấp lùn, lá xòe ngang (vàng lùn) hoặc lá xanh đậm, xoăn tít, gân lá sưng phồng (lùn xoắn lá).",
        "xu_ly_cap_cuu": "⚠️ **KHÔNG CÓ THUỐC TRỊ:** Nhổ bỏ khóm bệnh ngay lập tức, cho vào bao kín và vùi sâu hoặc đốt để tránh rầy lây lan.",
        "thuoc_dac_tri": "Chỉ có thuốc trừ Rầy nâu (môi giới): Pymetrozine (Chess), Buprofezin (Applaud).",
        "luu_y": "Virus lây qua môi giới là Rầy nâu. Diệt rầy là cách duy nhất bảo vệ ruộng."
    }
}

# Mapping các label khác từ model AI về chuẩn
DATA_HINH_ANH.update({
    "Bacterialblight": {"ref": "Bacterial Leaf Blight"},
    "Leaf Blast": {"ref": "Blast"},
    "Rice Blast": {"ref": "Blast"},
    "Brownspot": {"ref": "Brown Spot"},
    "Hispa": {"ref": "Blast"}
})

def ve_bbox_voi_confidence(img, predictions):
    """Vẽ bounding box VÀ hiển thị tỉ lệ chính xác lên ảnh (To hơn, không hiện tên)"""
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Load font to hơn cho %
    try:
        font_path = "C:/Windows/Fonts/arial.ttf"
        font_big = ImageFont.truetype(font_path, 36) # Tăng size lên 36
    except:
        try:
            font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            font_big = ImageFont.load_default()
        
    for i, pred in enumerate(predictions[:3]):
        conf = pred['confidence'] * 100
        if conf < 30:
            continue 
        
        confidence_label = f"{conf:.1f}%"
        
        # Tọa độ
        x, y, w, h = pred.get('x', 0), pred.get('y', 0), pred.get('width', 100), pred.get('height', 100)
        x0, y0, x1, y1 = int(x - w/2), int(y - h/2), int(x + w/2), int(y + h/2)
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(width, x1), min(height, y1)
        
        # Màu theo độ tin cậy
        color = "#00ff00" if conf >= 80 else "#ffff00" if conf >= 60 else "#ff0000"
        
        # Vẽ khung
        draw.rectangle([x0, y0, x1, y1], outline=color, width=5) # Khung dầy hơn chút
        
        # Vẽ nhãn % TO
        text_y = y0 - 45 if y0 > 50 else y1 + 5
        try:
            bbox_conf = draw.textbbox((x0, text_y), confidence_label, font=font_big)
            draw.rectangle(bbox_conf, fill=color)
            draw.text((x0, text_y), confidence_label, fill="black", font=font_big)
        except:
            draw.text((x0, text_y), confidence_label, fill=color)
        
    return img

# ==============================================================================
# 3. GIAO DIỆN ỨNG DỤNG
# ==============================================================================

st.markdown("<h1>Chuẩn Đoán Bệnh Trên Cây Lúa</h1>", unsafe_allow_html=True)
st.caption("Hệ thống chẩn đoán và tư vấn phòng trừ bệnh hại lúa - Dữ liệu cập nhật 2025 (Không bao gồm sâu hại)")

# ==============================================================================
# LẤY DỮ LIỆU THỜI TIẾT (Dùng chung cho cả trang)
# ==============================================================================
thoi_tiet = lay_thoi_tiet(city="Can Tho")

# Hiển thị thời tiết ở sidebar
with st.sidebar:
    st.markdown("### 🌤️ THỜI TIẾT")
    
    st.markdown(f"""
    <div class="weather-box">
        <h4 style='color: white; margin: 0;'>📍 {thoi_tiet['thanh_pho']}</h4>
        <p style='font-size: 11px; opacity: 0.8; margin-bottom: 10px;'>{thoi_tiet['nguon']}</p>
        <p style='font-size: 32px; margin: 10px 0;'>{thoi_tiet['nhiet_do']}°C</p>
        <p style='margin: 5px 0;'>💧 Độ ẩm: {thoi_tiet['do_am']}%</p>
        <p style='margin: 5px 0;'>🌪️ Gió: {thoi_tiet['gio']} km/h</p>
        <p style='margin: 5px 0;'>📝 {thoi_tiet['mo_ta']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cảnh báo nguy cơ
    st.markdown("### ⚠️ NGUY CƠ BỆNH")
    if thoi_tiet['do_am'] > 90:
        st.error("🔴 NGUY CƠ CAO: Độ ẩm rất cao, thuận lợi cho bệnh phát triển!")
    elif thoi_tiet['do_am'] > 80:
        st.warning("🟡 NGUY CƠ TRUNG BÌNH: Theo dõi chặt chẽ ruộng lúa")
    else:
        st.success("🟢 NGUY CƠ THẤP: Thời tiết ổn định")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🔍 CHẨN ĐOÁN QUA ẢNH", "💬 CHAT VỚI CHUYÊN GIA", "📋 NHẬT KÝ"])
# --- TAB 1: CHẨN ĐOÁN ---
with tab1:
    col_l, col_r = st.columns([1, 1.2])
    
    with col_l:
        st.subheader("📸 Tải ảnh lá lúa bệnh")
        
        # Chọn nguồn ảnh
        input_method = st.radio(
            "Chọn nguồn ảnh:",
            ["📤 Tải lên từ máy", "📷 Chụp ảnh trực tiếp"],
            horizontal=True
        )
        
        uploaded_file = None
        if input_method == "📷 Chụp ảnh trực tiếp":
            uploaded_file = st.camera_input("Chụp ảnh lá lúa")
        else:
            uploaded_file = st.file_uploader(
                "Chọn ảnh lá lúa",
                type=['jpg', 'jpeg', 'png'],
                help="Hỗ trợ: JPG, PNG"
            )
        
        if uploaded_file is not None:
            # Hiển thị ảnh gốc
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, caption="✅ Ảnh đã tải lên", use_container_width=True)
            
            # Nút phân tích
            if st.button("🔍 PHÂN TÍCH BỆNH (ROBOFLOW)", type="primary", use_container_width=True):
                with col_r:
                    with st.spinner("🤖 Đang phân tích bằng Roboflow AI..."):
                        # Lưu ảnh tạm
                        image.save("temp_image.jpg")
                        
                        # Gọi API Roboflow
                        try:
                            client = InferenceHTTPClient(
                                api_url="https://detect.roboflow.com",
                                api_key="8tf2UvcnEv8h80bV2G0Q"
                            )
                            
                            result = client.infer("temp_image.jpg", model_id="rice-leaf-disease-twtlz/1")
                            predictions = result.get('predictions', [])
                            
                            if len(predictions) > 0:
                                # Lấy kết quả có confidence cao nhất
                                top_prediction = sorted(predictions, key=lambda x: x['confidence'], reverse=True)[0]
                                
                                # Vẽ bounding box lên ảnh
                                img_with_bbox = ve_bbox_voi_confidence(image.copy(), predictions)
                                st.image(img_with_bbox, caption="✅ Kết quả phân tích (% trên ảnh)", use_container_width=True)
                                
                                # Lấy thông tin bệnh
                                class_name = top_prediction['class']
                                confidence = top_prediction['confidence'] * 100
                                
                                disease_info = DATA_HINH_ANH.get(class_name, {})
                                if "ref" in disease_info:
                                    disease_info = DATA_HINH_ANH.get(disease_info["ref"], {})
                                
                                # Hiển thị kết quả
                                st.success(f"### 🎯 {disease_info.get('ten_viet', class_name)}")
                                st.metric("📊 Độ chính xác", f"{confidence:.1f}%")
                                
                                if confidence >= 75:
                                    st.success("✅ Kết quả đáng tin cậy")
                                elif confidence >= 55:
                                    st.warning("⚠️ Kết quả khá chắc - Nên kiểm tra thêm")
                                else:
                                    st.error("❌ Kết quả không chắc chắn - Cần chuyên gia")
                                
                                # Thông tin chi tiết
                                with st.expander("📖 THÔNG TIN CHI TIẾT", expanded=True):
                                    st.markdown(f"**🔬 Tên khoa học:** {disease_info.get('ten_khoa_hoc', 'N/A')}")
                                    st.markdown(f"**📝 Mô tả:** {disease_info.get('mo_ta_ngan', 'N/A')}")
                                    st.markdown(disease_info.get('xu_ly_cap_cuu', ''))
                                
                                st.info(f"💊 **Thuốc đặc trị:** {disease_info.get('thuoc_dac_tri', 'Liên hệ chuyên gia')}")
                                st.warning(f"⚠️ **Lưu ý:** {disease_info.get('luu_y', '')}")
                                
                                # Lưu lịch sử
                                st.session_state['history'].append({
                                    "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                    "result": f"{disease_info.get('ten_viet', class_name)} ({confidence:.1f}%)"
                                })
                            
                            else:
                                st.success("### ✅ LÁ LÚA KHỎE MẠNH!")
                                st.balloons()
                                st.info("Không phát hiện bệnh. Tiếp tục theo dõi và chăm sóc tốt!")
                        
                        except Exception as e:
                            st.error(f"❌ Lỗi kết nối Roboflow: {str(e)}")
                            st.info("Vui lòng kiểm tra kết nối mạng hoặc API key")

# --- TAB 2: CHATBOT TƯ VẤN ---
with tab2:
    st.subheader("💬 Chatbot tư vấn bệnh lúa")
    st.caption("Hỏi về: Đạo ôn, Khô vằn, Bạc lá, Lem lép hạt, Vàng lùn, Đốm nâu...")
    
    # Hiển thị lịch sử chat
    for message in st.session_state['chat_messages']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input chat
    if prompt := st.chat_input("Hỏi về bệnh lúa... (VD: Đạo ôn là gì? Cách trị khô vằn?)"):
        # Thêm câu hỏi của user
        st.session_state['chat_messages'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Tìm câu trả lời
        with st.chat_message("assistant"):
            response = tim_tra_loi(prompt)
            st.markdown(response)
            st.session_state['chat_messages'].append({"role": "assistant", "content": response})

# --- TAB 3: LỊCH SỬ ---
with tab3:
    st.subheader("📋 Lịch sử chẩn đoán")
    
    if len(st.session_state['history']) > 0:
        st.success(f"✅ Đã chẩn đoán {len(st.session_state['history'])} lần")
        
        # Hiển thị bảng lịch sử
        history_df = pd.DataFrame(st.session_state['history'])
        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "time": "Thời gian",
                "result": "Kết quả"
            }
        )
        
        # Nút xóa lịch sử
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ Xóa toàn bộ lịch sử", use_container_width=True):
                st.session_state['history'] = []
                st.rerun()
    else:
        st.info("📭 Chưa có lịch sử chẩn đoán. Hãy thử chẩn đoán ảnh ở Tab 1!")

# --- FOOTER ---
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🌾 <strong>Chuẩn đoán bệnh trên lúa - {thoi_tiet['thanh_pho']} 2026</strong></p>
    <p>🤖 Powered by <strong>Roboflow Object Detection</strong> | 🌐 OpenWeatherMap API</p>
    <p style='font-size: 12px; margin-top: 10px;'>
        ⚠️ <em>Kết quả chỉ mang tính chất tham khảo. Nên tham khảo ý kiến chuyên gia nông nghiệp địa phương.</em>
    </p>
   
</div>
""", unsafe_allow_html=True)

# --- KẾT THÚC CODE ---



