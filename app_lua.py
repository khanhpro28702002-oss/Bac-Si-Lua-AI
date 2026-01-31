HF_TOKEN = "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"
MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

def goi_chuyen_gia_hf(user_input):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Prompt đơn giản cho Mistral
    prompt = f"""Bạn là chuyên gia nông nghiệp Việt Nam. Hãy trả lời câu hỏi sau một cách ngắn gọn, dễ hiểu:

Câu hỏi: {user_input}

Trả lời:"""
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }
    }
    
    try:
        response = requests.post(MODEL_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            full_text = result[0].get('generated_text', '')
            # Lấy phần sau "Trả lời:"
            answer = full_text.split("Trả lời:")[-1].strip()
            return answer if answer else "Xin lỗi, AI chưa trả lời được."
        else:
            return "Không nhận được phản hồi từ AI."
            
    except requests.exceptions.HTTPError as e:
        return f"Lỗi API: {e.response.status_code}. Model có thể đang bận, thử lại sau."
    except Exception as e:
        return f"Lỗi kết nối: {str(e)}"
