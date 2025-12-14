import streamlit as st
from datetime import datetime
import json
import os
import base64 # Thư viện cần thiết để mã hóa Base64

# 1. THÊM THƯ VIỆN CẦN THIẾT CHO OPENAI
from dotenv import load_dotenv
import openai # Thư viện OpenAI

# Load biến môi trường từ file .env
load_dotenv()

# Lấy API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Khởi tạo OpenAI Client
client = None
if OPENAI_API_KEY:
    try:
        # Khởi tạo OpenAI Client
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # Chọn mô hình GPT (gpt-4o-mini hỗ trợ đa phương thức)
        MODEL_NAME = "gpt-4o-mini" 
    except Exception as e:
        st.error(f"Lỗi khi khởi tạo OpenAI Client: {e}")
else:
    st.warning("Vui lòng thiết lập OPENAI_API_KEY trong file .env để sử dụng AI thật sự.")


# Đường dẫn file lưu lịch sử
HISTORY_FILE = "chat_history.json"

# Hàm lưu lịch sử vào file JSON
def save_history_to_file():
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.chat_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Lỗi khi lưu lịch sử: {e}")

# Hàm load lịch sử từ file JSON
def load_history_from_file():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Lỗi khi đọc lịch sử: {e}")
    return []

# 1.1 HÀM MÃ HÓA ẢNH SANG BASE64
def encode_image_to_base64(uploaded_file):
    """Mã hóa file ảnh Streamlit UploadedFile sang chuỗi Base64."""
    if uploaded_file is None:
        return None
    try:
        # Đọc file ảnh dưới dạng bytes
        bytes_data = uploaded_file.getvalue()
        # Mã hóa Base64 và chuyển sang chuỗi UTF-8
        base64_string = base64.b64encode(bytes_data).decode('utf-8')
        return base64_string
    except Exception as e:
        st.error(f"Lỗi khi mã hóa ảnh: {e}")
        return None

# Cấu hình trang
st.set_page_config(
    page_title="ChatBot AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS tùy chỉnh để làm giao diện giống ChatGPT
st.markdown("""
<style>
    /* Ẩn menu và footer mặc định */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tùy chỉnh sidebar */
    [data-testid="stSidebar"] {
        background-color: #202123;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    /* Tùy chỉnh nút trong sidebar */
    .sidebar-button {
        background-color: transparent;
        border: 1px solid #4d4d4f;
        color: white;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
        margin: 5px 0;
        width: 100%;
        text-align: left;
    }
    
    .sidebar-button:hover {
        background-color: #2a2b32;
    }
    
    /* Tùy chỉnh khung chat */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    
    .chat-message.user {
        background-color: #f7f7f8;
    }
    
    .chat-message.assistant {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
    }
    
    .chat-message .message-content {
        margin-top: 0.5rem;
    }
    
    .chat-message .role {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    /* Tùy chỉnh input */
    .stTextInput > div > div > input {
        background-color: white;
        border: 1px solid #d1d5db;
        border-radius: 0.5rem;
        padding: 0.75rem;
    }
    
    /* Tùy chỉnh nút gửi */
    .stButton > button {
        background-color: #10a37f;
        color: white;
        border: none;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #0d8c6d;
    }
    
    /* History item */
    .history-item {
        padding: 0.75rem;
        margin: 0.25rem 0;
        border-radius: 0.375rem;
        cursor: pointer;
        color: white;
        background-color: transparent;
        border: 1px solid transparent;
    }
    
    .history-item:hover {
        background-color: #2a2b32;
    }
    
    .history-item.active {
        background-color: #343541;
        border-color: #4d4d4f;
    }
    
    /* Tùy chỉnh vùng input container */
    .input-container {
        position: relative;
        margin-bottom: 1rem;
    }
    
    /* Tùy chỉnh file uploader để nằm inline */
    [data-testid="stFileUploader"] {
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stFileUploader"] > div {
        padding: 0.5rem;
        border: 1px solid #d1d5db;
        border-radius: 0.5rem;
        background-color: white;
    }
    
    /* Ẩn label của file uploader */
    [data-testid="stFileUploader"] label {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    # Load lịch sử từ file khi khởi động
    st.session_state.chat_history = load_history_from_file()

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "chat_counter" not in st.session_state:
    # Tính chat_counter dựa trên lịch sử đã có
    st.session_state.chat_counter = len(st.session_state.chat_history)

# Thêm state cho ảnh được tải lên
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "app_initialized" not in st.session_state: 
    st.session_state.app_initialized = False

# Hàm tạo chat mới
def create_new_chat():
    st.session_state.chat_counter += 1
    chat_id = f"chat_{st.session_state.chat_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    st.session_state.current_chat_id = chat_id
    # Đặt lại file_uploader khi tạo chat mới
    st.session_state.messages = []
    st.session_state.uploaded_image = None
    if 'file_uploader_key' in st.session_state:
        del st.session_state['file_uploader_key'] # *** SỬA LỖI RESET FILE UPLOADER ***
    
    # Thêm vào history
    st.session_state.chat_history.append({
        "id": chat_id,
        "title": f"Chat mới {st.session_state.chat_counter}",
        "messages": [],
        "created_at": datetime.now().isoformat()
    })
    
    # Lưu vào file
    save_history_to_file()

# Hàm load chat từ history
def load_chat(chat_id):
    for chat in st.session_state.chat_history:
        if chat["id"] == chat_id:
            st.session_state.current_chat_id = chat_id
            st.session_state.messages = chat["messages"].copy()
            # Đảm bảo file_uploader được reset khi load chat
            st.session_state.uploaded_image = None 
            if 'file_uploader_key' in st.session_state:
                del st.session_state['file_uploader_key'] # *** SỬA LỖI RESET FILE UPLOADER ***
            break

# Hàm lưu tin nhắn vào chat hiện tại
def save_message_to_current_chat():
    if st.session_state.current_chat_id:
        for chat in st.session_state.chat_history:
            if chat["id"] == st.session_state.current_chat_id:
                chat["messages"] = st.session_state.messages.copy()
                # Cập nhật title nếu là tin nhắn đầu tiên và là người dùng
                if len(chat["messages"]) > 0 and chat["title"].startswith("Chat mới"):
                    # Tìm tin nhắn đầu tiên của user để làm title
                    first_user_msg = next((msg for msg in chat["messages"] if msg["role"] == "user"), None)
                    if first_user_msg:
                        # Nội dung tin nhắn user có thể là string (chỉ text) hoặc list (text + image)
                        if isinstance(first_user_msg["content"], list):
                            # Lấy phần text của tin nhắn đầu tiên
                            prompt_text = next((item["text"] for item in first_user_msg["content"] if "text" in item), "Ảnh...")
                        else:
                            prompt_text = first_user_msg["content"]
                            
                        first_message = prompt_text[:50]
                        chat["title"] = first_message if len(first_message) < 50 else first_message + "..."
                        
                break
        
        # Lưu vào file
        save_history_to_file()

# Hàm xóa chat
def delete_chat(chat_id):
    st.session_state.chat_history = [chat for chat in st.session_state.chat_history if chat["id"] != chat_id]
    if st.session_state.current_chat_id == chat_id:
        st.session_state.current_chat_id = None
        st.session_state.messages = []
        st.session_state.uploaded_image = None
        if 'file_uploader_key' in st.session_state:
             del st.session_state['file_uploader_key'] # *** SỬA LỖI RESET FILE UPLOADER ***
    
    # Lưu vào file
    save_history_to_file()

# 2. HÀM GỬI YÊU CẦU ĐA PHƯƠNG THỨC (TEXT VÀ IMAGE)
# 2. HÀM GỬI YÊU CẦU ĐA PHƯƠNG THỨC (TEXT VÀ IMAGE)
def get_ai_response(user_message_content):
    if not client:
        if isinstance(user_message_content, list):
            prompt_text = next((item["text"] for item in user_message_content if "text" in item), "Chỉ ảnh.")
        else:
            prompt_text = user_message_content
            
        return f"API Key chưa được thiết lập hoặc xảy ra lỗi. Không thể tạo response AI cho tin nhắn: '{prompt_text[:50]}...'."

    # ✨ System prompt — ĐẶT Ở ĐÂY
    system_prompt = {
        "role": "system",
        "content": (
            "Bạn là một Trợ lý học tập AI siêu thân thiện, kiên nhẫn và vui tính, chuyên dạy học sinh Tiểu học và THCS.\n"
            "Nhiệm vụ của bạn là khơi gợi sự tò mò và giúp các bạn nhỏ tự tìm ra lời giải, chứ KHÔNG làm bài hộ.\n\n"
            
            " **QUY TẮC CẤM (BẮT BUỘC TUÂN THỦ):**\n"
            "1. KHÔNG ĐƯỢC LÀM TIẾP KHI BÀI TẬP BỊ LỖI TRỪ KHI TRONG ĐỀ NGƯỜI TA NÓI SỮA LỖI SAI. \n"
            "2. TUYỆT ĐỐI KHÔNG BAO GIỜ ĐƯA RA ĐÁP ÁN HOÀN CHỈNH NGAY CẢ TRONG KHI GIẢI THÍCH CÂU HỎI (VÍ DỤ: 'CÂU TRẢ LỜI CÓ THỂ LÀ:....','ĐÁP ÁN LÀ;...', CÂU TRẢ LỜI LÀ;...') .\n"
            "3. KHÔNG BAO GIỜ đưa ra đáp án ngay, KỂ CẢ KHI NGƯỜI DÙNG BẮT BUỘT (VÍ DỤ: 'PHẢI GIẢI CHO TÔI','GIẢI CHO TÔI ĐÁP ÁN NGAY LẬP TỨC','ĐÁP ÁN').\n"
            "4. KHÔNG DÙNG CỤM TỪ ( CÓ THỂ ) KHI GIẢI CÂU HỎI. \n"
            "5. KHÔNG ĐƯỢC GIÚP NGƯỜI DÙNG HOÀN THIỆN TỪNG CÂU HỎI NGAY CẢ KHI NGƯỜI DÙNG YÊU CẦU CHO ĐÁP ÁN (VÍ DỤ: 'PHẢI GIẢI CHO TÔI','GIẢI CHO TÔI ĐÁP ÁN NGAY LẬP TỨC','ĐÁP ÁN'). \n"
            "6. KHÔNG ĐƯỢC ĐƯA RA ĐÁP ÁN KHI NGƯỜI DÙNG NÓI ĐƯA RA ĐÁP ÁN HOẶC GIẢI CHỈ VÀ DỘNG VIÊN HỌC SINH. \n"
            "7. KHÔNG ĐƯỢC ĐỌC ĐỀ LƠ LÀ VÀ KHÔNG ĐƯỢC GIẢI MỘT LÈO ĐẾN KẾT QUẢ.\n"
            "8. KHÔNG dùng ngôn ngữ hàn lâm, khó hiểu. Hãy dùng từ ngữ đơn giản, gần gũi.\n"
            "9. Nếu CÂU TRẢ LỜI CỦA BẠN VÔ TÌNH ĐƯA RA ĐÁP ÁN HOÀN CHỈNH → ĐÓ LÀ VI PHẠM NGHIÊM TRỌNG. \n\n"
            
            " **PHƯƠNG PHÁP HƯỚNG DẪN:**\n"
            "- **Bước 1: Khen ngợi & Động viên.** Luôn bắt đầu bằng một lời khích lệ (Ví dụ: 'Bài tập này thú vị nè!', 'Cố lên, em làm được mà!').\n"
            "- **Bước 2: Phân tích đề bài.** Nếu là ảnh, hãy giúp học sinh tóm tắt lại đề bài cho dễ hiểu.\n"
            "- **Bước 3: Gợi ý nhỏ (Scaffolding).** Chỉ đưa ra manh mối cho bước ĐẦU TIÊN.\n"
            "- **Bước 4: Hỏi ngược lại.** Luôn kết thúc bằng một câu hỏi để học sinh phải suy nghĩ và trả lời.\n\n"
            
            "  **PHONG CÁCH:**\n"
            "- Sử dụng nhiều Emoji 🌟✏️📚 để tạo cảm giác thân thiện.\n"
            "- Nếu học sinh trả lời sai, hãy nhẹ nhàng sửa: 'Gần đúng rồi, thử nghĩ lại chỗ này xem...'\n"
            "- Nếu học sinh trả lời đúng, hãy khen ngợi nhiệt tình trước khi sang bước tiếp theo."
        )
    }

    # Lấy lịch sử chat (giữ nguyên nội dung text hoặc multimodal)
    messages_for_api = [
        system_prompt,  # <==== Thêm ở đầu
        *[
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.messages
        ]
    ]

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages_for_api
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"Lỗi khi gọi OpenAI API: {e}. Vui lòng kiểm tra API Key, kết nối mạng và quota sử dụng."



# Sidebar
with st.sidebar:
    st.title("💬 ChatBot AI")
    
    # Nút tạo chat mới
    if st.button("➕ Chat mới", use_container_width=True):
        create_new_chat()
        st.rerun()
    
    st.markdown("---")
    
    # Hiển thị lịch sử chat
    st.subheader("📚 Lịch sử")
    
    if len(st.session_state.chat_history) == 0:
        st.info("Chưa có cuộc hội thoại nào")
    else:
        # Hiển thị các chat từ mới đến cũ
        for chat in reversed(st.session_state.chat_history):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                is_active = chat["id"] == st.session_state.current_chat_id
                
                if st.button(
                    f"💬 {chat['title']}", 
                    key=f"chat_{chat['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    load_chat(chat["id"])
                    st.rerun()
            
            with col2:
                if st.button("🗑️", key=f"delete_{chat['id']}", use_container_width=True):
                    delete_chat(chat["id"])
                    st.rerun()
    
    st.markdown("---")
    
    # Thông tin thêm
    with st.expander("ℹ️ Thông tin"):
        st.markdown(f"""
        **Chatbot AI Demo** (Sử dụng OpenAI API)
        
        Mô hình: **`{MODEL_NAME}`** (hỗ trợ đa phương thức)
        
        Tính năng:
        - 🖼️ **Hỗ trợ Image-to-Text**
        - 💬 Chat tương tác (AI thật sự)
        - 📝 Lưu lịch sử
        - 🔄 Nhiều cuộc hội thoại
        - 🎨 Giao diện ChatGPT
        
        Phát triển bởi Streamlit và OpenAI
        """)
    
    # Nút xóa toàn bộ lịch sử
    if st.button("🗑️ Xóa toàn bộ lịch sử", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.session_state.uploaded_image = None
        if 'file_uploader_key' in st.session_state:
             del st.session_state['file_uploader_key'] # *** SỬA LỖI RESET FILE UPLOADER ***
        save_history_to_file()
        st.rerun()

# Kiểm tra cờ khởi tạo
if not st.session_state.app_initialized:
    # Nếu chưa có chat ID và chưa có lịch sử, tạo chat mới
    if st.session_state.current_chat_id is None and len(st.session_state.chat_history) == 0:
        create_new_chat()

    # Nếu đã có lịch sử nhưng chưa load chat nào, load chat gần nhất
    elif st.session_state.current_chat_id is None and len(st.session_state.chat_history) > 0:
        # Lấy ID của chat mới nhất
        newest_chat_id = st.session_state.chat_history[-1]["id"] 
        load_chat(newest_chat_id)

    # Đặt cờ là True sau khi khởi tạo thành công lần đầu
    st.session_state.app_initialized = True
    
# Hàm hiển thị nội dung tin nhắn, kể cả ảnh.
def display_message_content(message_content):
    """Hàm hiển thị nội dung tin nhắn, kể cả ảnh."""
    if isinstance(message_content, list):
        # Đây là tin nhắn đa phương thức (có ảnh)
        for item in message_content:
            if "text" in item:
                st.markdown(item["text"])
            elif "image_url" in item:
                # Trích xuất URL Base64 để hiển thị ảnh
                image_url = item["image_url"]["url"]
                st.image(image_url, use_column_width=True)
    else:
        # Đây là tin nhắn chỉ có văn bản
        st.markdown(message_content)

# Hiển thị các tin nhắn
chat_container = st.container()

with chat_container:
    if len(st.session_state.messages) == 0:
        st.info("👋 Xin chào! Tôi là ChatBot AI. Hãy nhập tin nhắn hoặc tải ảnh lên.")
    else:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                display_message_content(message["content"]) # *** SỬ DỤNG HÀM MỚI ***

# 3. THÀNH PHẦN TẢI ẢNH LÊN VÀ INPUT (GIỐNG CHATGPT)
# Tạo container cho input area
input_col1, input_col2 = st.columns([0.21, 0.79])

with input_col1:
    # Nút upload ảnh (icon nhỏ bên trái)
    uploaded_image = st.file_uploader(
        "📎", 
        type=["jpg", "jpeg", "png"], 
        key="file_uploader_key",
        label_visibility="collapsed"
    )
    st.session_state.uploaded_image = uploaded_image

with input_col2:
    # Chat input ở bên phải
    prompt = st.chat_input("Nhập tin nhắn của bạn...")

# Hiển thị thông báo file đã tải
if st.session_state.uploaded_image:
    st.success(f"✅ Đã tải: {st.session_state.uploaded_image.name}")
    with st.expander("🖼️ Xem trước ảnh"):
        st.image(st.session_state.uploaded_image, use_column_width=True)

if prompt: # Xử lý khi có prompt HOẶC có ảnh
    # Tạo nội dung tin nhắn đa phương thức cho API
    user_message_content = []
    
    # CHUẨN BỊ VÀ GỬI ẢNH ĐẾN API
    base64_image = None
    if st.session_state.uploaded_image is not None:
        # Mã hóa ảnh sang Base64
        base64_image = encode_image_to_base64(st.session_state.uploaded_image)
        
        if base64_image:
            # Thêm đối tượng ảnh vào content
            user_message_content.append({
                "type": "image_url",
                "image_url": {
                    # Tạo data URL theo định dạng của OpenAI
                    "url": f"data:{st.session_state.uploaded_image.type};base64,{base64_image}"
                },
            })

    # Thêm đối tượng văn bản vào content (ngay cả khi prompt rỗng, nếu có ảnh)
    final_prompt = prompt if prompt else ""
    user_message_content.append({"type": "text", "text": final_prompt})
    
    
    # Quyết định nội dung lưu vào state (list nếu có ảnh, string nếu chỉ có text)
    if base64_image:
        message_to_save = user_message_content
    else:
        # Nếu chỉ có văn bản (không có ảnh), vẫn giữ nguyên định dạng string để tương thích
        message_to_save = final_prompt


    # Thêm tin nhắn của user vào state
    st.session_state.messages.append({"role": "user", "content": message_to_save})
    
    # Hiển thị tin nhắn user
    with chat_container:
        with st.chat_message("user"):
            display_message_content(message_to_save)
    
    # Tạo response (chỉ tạo, không hiển thị trực tiếp)
    with st.spinner("Đang suy nghĩ..."):
        # Gửi nội dung tin nhắn (list hoặc string) cho hàm get_ai_response
        response = get_ai_response(message_to_save) 
        
    # Thêm response vào messages
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # ********** SỬA LỖI RESET FILE UPLOADER **********
    # Xóa ảnh đã tải lên sau khi gửi tin nhắn thành công
    st.session_state.uploaded_image = None 
    if 'file_uploader_key' in st.session_state:
        # SỬ DỤNG 'del' ĐỂ RESET FILE UPLOADER
        del st.session_state['file_uploader_key'] 
        
    # Lưu vào history
    save_message_to_current_chat()

    # Rerun để cập nhật giao diện (rất quan trọng)
    st.rerun()

# Footer
st.markdown("---")
# st.markdown(
#     "<div style='text-align: center; color: gray; padding: 1rem;'>"
#     "💡 Tip: Click vào icon 📎 bên trái để tải ảnh lên, sau đó nhập tin nhắn của bạn."
#     "</div>", 
#     unsafe_allow_html=True

# )














