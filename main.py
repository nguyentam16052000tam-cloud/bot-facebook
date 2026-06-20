import hashlib
from flask import Flask, request

app = Flask(__name__)

# =========================================================================
# ⚠️ CẤU HÌNH THÔNG TIN BẢO MẬT CỦA BẠN
# Điền chuỗi Partner Key mà bạn lấy từ trang kết nối API của Doithegiatot/TSR vào đây
# =========================================================================
PARTNER_KEY = "CHUỖI_PARTNER_KEY_CỦA_BẠN_TRÊN_WEB_ĐỔI_THẺ"

def md5_hash(text):
    """Hàm chuyển đổi chuỗi văn bản sang mã hóa MD5 để đối chiếu chữ ký"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# Đường dẫn nhận dữ liệu Webhook từ web đổi thẻ cào truyền về
@app.route('/webhook-callback', methods=['POST'])
def webhook_callback():
    data = request.json
    if not data:
        return "Không có dữ liệu gửi về", 400

    # 1. Đọc toàn bộ các thông số do hệ thống đổi thẻ tự động bắn sang
    status = str(data.get('status'))         # Trạng thái: 1 = Thành công, 2 = Sai mệnh giá, 3 = Thẻ lỗi
    prices = str(data.get('prices'))         # Mệnh giá gốc của thẻ cào khách nạp (Ví dụ: 100000)
    real_amount = str(data.get('amount'))    # Số tiền thực tế bạn nhận được trên web sau khi trừ chiết khấu
    request_id = str(data.get('request_id'))   # Mã đơn hàng duy nhất do Bot của bạn tự sinh ra ban đầu
    callback_sign = data.get('callback_sign') # Chữ ký bảo mật đi kèm từ web đổi thẻ

    # 2. BƯỚC CHECK THẬT/GIẢ: Tự tính toán lại chữ ký dựa trên thuật toán cốt lõi
    # Công thức chuẩn: md5(partner_key + status + prices + amount + request_id)
    raw_check_str = PARTNER_KEY + status + prices + real_amount + request_id
    my_calculated_sign = md5_hash(raw_check_str)

    # 3. ĐỐI CHIẾU CHỮ KÝ: Nếu không khớp, chặn ngay lập tức vì đây là yêu cầu ảo từ Hacker giả mạo
    if callback_sign != my_calculated_sign:
        print("⚠️ CẢNH BÁO NGUY HIỂM: Phát hiện request giả mạo Webhook nhằm hack tiền ảo!")
        return "Chữ ký không hợp lệ!", 400

    # 4. NẾU CHỮ KÝ TRÙNG KHỚP -> GIAO DỊCH THẬT 100%
    if status == "1":
        # Thẻ thật thành công -> Tiền mặt đã nhảy vào tài khoản web của bạn
        print(f"✅ Thẻ đúng! Mã đơn: {request_id}. Số tiền bạn thực nhận trên web: {real_amount}đ")
        
        # Tách lấy ID người dùng Telegram từ mã request_id ban đầu của bạn
        # Ví dụ request_id lúc khách ấn nạp là "BOT_1234567_167000" -> tách ra lấy được telegram_user_id = "1234567"
        telegram_user_id = request_id.split('_')[1]
        
        # 🛠️ [HÀNH ĐỘNG]: Bạn viết thêm lệnh cập nhật số dư cho khách vào Database Python của bạn tại đây...
        # Ví dụ: update_balance_database(telegram_user_id, real_amount)
        
        # 🛠️ [HÀNH ĐỘNG]: Gọi API Telegram gửi tin nhắn báo nạp tiền thành công cho khách hàng
        
    elif status == "2":
        # Khách khai báo sai mệnh giá trên Bot (Bị phạt nuốt thẻ hoặc trừ tiền tùy chính sách của web)
        print(f"❌ Khách gửi sai mệnh giá. Mã đơn: {request_id}")
    else:
        # Thẻ sai mã, sai seri hoặc thẻ đã bị cào sử dụng trước đó
        print(f"❌ Thẻ lỗi/Đã sử dụng. Mã đơn: {request_id}")

    # Luôn luôn phản hồi về phía web đổi thẻ chữ 'OK' để họ biết hệ thống của bạn đã nhận dữ liệu ổn định
    return "OK", 200

if __name__ == '__main__':
    # 🌟 CẤU HÌNH ĐẶC BIỆT DÀNH CHO RENDER: Chạy bắt buộc ở cổng 10000 và host 0.0.0.0
    app.run(host='0.0.0.0', port=10000)
