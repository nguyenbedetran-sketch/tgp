# Ghi chú cập nhật

Bản cập nhật này bổ sung animation cho trang đầu theo hướng kiến trúc cao cấp: ảnh hero zoom chậm khi tải, lưới phối cảnh chuyển động, hai quỹ đạo ánh sáng, parallax nhẹ theo con trỏ trên desktop và thanh tiến độ cuộn. CSS có hỗ trợ `prefers-reduced-motion` để tắt chuyển động khi người dùng yêu cầu.

Backend hỗ trợ bootstrap tài khoản quản trị bằng biến môi trường `ADMIN_BOOTSTRAP_USERNAME`, `ADMIN_BOOTSTRAP_EMAIL` và `ADMIN_BOOTSTRAP_PASSWORD`. Mật khẩu được băm bằng PBKDF2-HMAC-SHA256 với salt ngẫu nhiên; không lưu mật khẩu dạng rõ trong mã nguồn hoặc database.

Bản local đã được kiểm tra bằng Flask test client: `/api/health`, đăng nhập admin, `/api/auth/me`, trang chủ, CSS/JS và các API dịch vụ/dự án đều trả kết quả thành công. Database đi kèm đã có tài khoản admin được tạo với mật khẩu băm.
