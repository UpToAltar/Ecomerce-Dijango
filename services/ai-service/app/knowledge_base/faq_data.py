from typing import TypedDict


class FAQItem(TypedDict):
    id: str
    question: str
    answer: str
    tags: list[str]
    category: str


FAQ_DATA: list[FAQItem] = [
    {
        "id": "faq-shipping-1",
        "question": "Chính sách giao hàng như thế nào?",
        "answer": (
            "🚚 **Chính sách giao hàng của chúng tôi:**\n"
            "- **Nội thành (TP.HCM, Hà Nội, Đà Nẵng):** 1-2 ngày làm việc\n"
            "- **Tỉnh/thành phố khác:** 3-5 ngày làm việc\n"
            "- **Phí ship:** Miễn phí cho đơn hàng từ **500.000đ** trở lên\n"
            "- Đơn dưới 500.000đ: phí ship 30.000đ\n"
            "- Bạn có thể theo dõi đơn hàng real-time qua mã vận đơn được gửi qua email/SMS."
        ),
        "tags": ["giao hàng", "ship", "vận chuyển", "delivery", "phí ship"],
        "category": "shipping",
    },
    {
        "id": "faq-return-1",
        "question": "Chính sách đổi trả hàng như thế nào?",
        "answer": (
            "🔄 **Chính sách đổi trả:**\n"
            "- Đổi trả **trong vòng 30 ngày** kể từ ngày nhận hàng\n"
            "- Sản phẩm cần còn nguyên vẹn, đầy đủ phụ kiện, hóa đơn\n"
            "- **Các trường hợp được đổi trả miễn phí:**\n"
            "  ✅ Hàng lỗi do nhà sản xuất\n"
            "  ✅ Sai màu sắc/size so với đơn hàng\n"
            "  ✅ Sản phẩm bị hư hỏng khi vận chuyển\n"
            "- Liên hệ hotline: **1800-xxxx** hoặc email: support@shop.vn để được hỗ trợ."
        ),
        "tags": ["đổi trả", "hoàn tiền", "return", "refund", "bảo hành"],
        "category": "return",
    },
    {
        "id": "faq-payment-1",
        "question": "Có những phương thức thanh toán nào?",
        "answer": (
            "💳 **Phương thức thanh toán:**\n"
            "- 💵 **COD (Thanh toán khi nhận hàng):** Trả tiền mặt trực tiếp\n"
            "- 🏦 **Chuyển khoản ngân hàng:** Vietcombank, Techcombank, BIDV, ACB...\n"
            "- 💳 **Thẻ tín dụng/ghi nợ:** Visa, MasterCard, JCB\n"
            "- 📱 **Ví điện tử:** MoMo, ZaloPay, VNPay, ShopeePay\n"
            "- Thanh toán trả góp 0% lãi suất cho đơn hàng từ **3.000.000đ** (qua thẻ tín dụng)"
        ),
        "tags": ["thanh toán", "payment", "COD", "chuyển khoản", "ví điện tử", "MoMo", "VNPay"],
        "category": "payment",
    },
    {
        "id": "faq-warranty-1",
        "question": "Chính sách bảo hành sản phẩm như thế nào?",
        "answer": (
            "🛡️ **Chính sách bảo hành:**\n"
            "- **Điện thoại, Laptop:** Bảo hành chính hãng **12-24 tháng**\n"
            "- **Đồ gia dụng:** Bảo hành **12 tháng** tại trung tâm bảo hành\n"
            "- **Thời trang, Giày dép:** Đổi lỗi trong **7 ngày**\n"
            "- **Mỹ phẩm:** Đổi hàng nếu phát hiện hàng giả/kém chất lượng\n"
            "- **Sách:** Đổi sách bị lỗi in trong **15 ngày**\n"
            "\n📌 Vui lòng giữ hóa đơn mua hàng để làm căn cứ bảo hành."
        ),
        "tags": ["bảo hành", "warranty", "hư hỏng", "sửa chữa"],
        "category": "warranty",
    },
    {
        "id": "faq-account-1",
        "question": "Làm thế nào để đăng ký tài khoản?",
        "answer": (
            "👤 **Đăng ký tài khoản:**\n"
            "1. Nhấp vào **Đăng ký** ở góc trên phải màn hình\n"
            "2. Điền email, mật khẩu và thông tin cá nhân\n"
            "3. Xác nhận email được gửi về hộp thư\n"
            "4. Hoàn tất đăng ký!\n"
            "\n💡 Thành viên được hưởng:\n"
            "- Tích điểm thưởng với mỗi đơn hàng\n"
            "- Ưu đãi sinh nhật hàng năm\n"
            "- Thông báo flash sale độc quyền"
        ),
        "tags": ["đăng ký", "tài khoản", "account", "login", "thành viên"],
        "category": "account",
    },
    {
        "id": "faq-order-1",
        "question": "Làm sao để theo dõi đơn hàng?",
        "answer": (
            "📦 **Theo dõi đơn hàng:**\n"
            "- Vào **Tài khoản → Đơn hàng của tôi**\n"
            "- Nhập mã đơn hàng vào ô tra cứu trên website\n"
            "- Xem email/SMS thông báo được gửi tự động\n"
            "\n**Trạng thái đơn hàng:**\n"
            "🟡 Chờ xác nhận → 🔵 Đang xử lý → 🚚 Đang giao → ✅ Đã giao"
        ),
        "tags": ["theo dõi", "tracking", "đơn hàng", "trạng thái"],
        "category": "order",
    },
    {
        "id": "faq-discount-1",
        "question": "Làm sao để dùng mã giảm giá?",
        "answer": (
            "🎫 **Sử dụng mã giảm giá:**\n"
            "1. Thêm sản phẩm vào giỏ hàng\n"
            "2. Tiến hành thanh toán\n"
            "3. Nhập mã vào ô **'Nhập mã giảm giá'** và nhấn Áp dụng\n"
            "\n💡 **Lưu ý:**\n"
            "- Mỗi đơn hàng chỉ dùng được 1 mã\n"
            "- Mã có thời hạn sử dụng nhất định\n"
            "- Một số mã chỉ áp dụng cho danh mục cụ thể"
        ),
        "tags": ["mã giảm giá", "coupon", "voucher", "khuyến mãi", "discount"],
        "category": "discount",
    },
    {
        "id": "faq-security-1",
        "question": "Thông tin cá nhân của tôi có được bảo mật không?",
        "answer": (
            "🔒 **Bảo mật thông tin:**\n"
            "- Toàn bộ giao dịch được mã hóa bằng **SSL/TLS**\n"
            "- Thông tin thẻ tín dụng không được lưu trên hệ thống\n"
            "- Dữ liệu cá nhân chỉ dùng để xử lý đơn hàng\n"
            "- Chúng tôi **không** chia sẻ thông tin với bên thứ ba\n"
            "- Tuân thủ quy định bảo vệ dữ liệu cá nhân (PDPA)"
        ),
        "tags": ["bảo mật", "privacy", "an toàn", "thông tin cá nhân"],
        "category": "security",
    },
    {
        "id": "faq-contact-1",
        "question": "Liên hệ hỗ trợ khách hàng như thế nào?",
        "answer": (
            "📞 **Liên hệ hỗ trợ:**\n"
            "- 📱 **Hotline:** 1800-XXXX (Miễn phí, 8h-22h)\n"
            "- 💬 **Chat trực tuyến:** Ngay trên website (8h-22h)\n"
            "- 📧 **Email:** support@shop.vn (Phản hồi trong 24h)\n"
            "- 📘 **Facebook:** fb.com/shopvn\n"
            "- 🏪 **Showroom:** 123 Nguyễn Huệ, Q1, TP.HCM\n"
            "\nTrung bình thời gian phản hồi: **dưới 15 phút** trong giờ hành chính."
        ),
        "tags": ["hỗ trợ", "liên hệ", "hotline", "contact", "customer service"],
        "category": "contact",
    },
    {
        "id": "faq-authentic-1",
        "question": "Sản phẩm có phải hàng chính hãng không?",
        "answer": (
            "✅ **Cam kết hàng chính hãng:**\n"
            "- 100% sản phẩm là **hàng chính hãng, có nguồn gốc rõ ràng**\n"
            "- Có đầy đủ tem, nhãn, hóa đơn VAT theo yêu cầu\n"
            "- Điện tử: nhập khẩu chính ngạch qua nhà phân phối ủy quyền\n"
            "- Mỹ phẩm: nguồn gốc từ các nhà phân phối chính thức tại Việt Nam\n"
            "- Thời trang: hợp tác trực tiếp với thương hiệu hoặc nhà phân phối\n"
            "\n🏆 Hoàn tiền **200%** nếu phát hiện hàng giả."
        ),
        "tags": ["chính hãng", "authentic", "hàng thật", "xuất xứ", "original"],
        "category": "product",
    },
]

CATEGORY_ADVICE: dict[str, str] = {
    "dong-ho": (
        "⌚ **Tư vấn chọn đồng hồ:**\n"
        "- **Smartwatch sức khỏe:** Apple Watch Series 9 (tốt nhất cho iOS), Samsung Galaxy Watch 6 (Android)\n"
        "- **Thể thao chuyên nghiệp:** Garmin Fenix 7 (pin 37 ngày, GPS multi-band)\n"
        "- **Tầm trung phổ thông:** Xiaomi Mi Watch S3, Amazfit GTR 4 (pin 14 ngày)\n"
        "- **Cổ điển/thời trang:** Seiko 5 Sports, Citizen Eco-Drive, Fossil Gen 6\n"
        "- **Giá tốt:** Casio G-Shock (bền, chống va đập), Fitbit Versa 4\n"
        "\n💡 Lưu ý: Apple Watch chỉ dùng được tối ưu với iPhone. Android nên chọn Samsung hoặc Garmin."
    ),
    "am-thanh": (
        "🎧 **Tư vấn chọn thiết bị âm thanh:**\n"
        "- **Tai nghe chống ồn cao cấp:** Sony WH-1000XM5 (over-ear), Bose QC45\n"
        "- **TWS flagship:** AirPods Pro 2 (iOS), Samsung Galaxy Buds 2 Pro (Android), Sony WF-1000XM4\n"
        "- **TWS tầm trung:** Anker Soundcore Liberty 4 NC (pin 50h, chống ồn 98.5%)\n"
        "- **Loa di động nhỏ gọn:** JBL Flip 6 (chống nước IP67, 12h)\n"
        "- **Loa di động cao cấp:** JBL Charge 5 (pin 20h, sạc được điện thoại), Marshall Emberton II\n"
        "\n💡 Nếu dùng nhiều cho công việc WFH: Sony XM5 hoặc Jabra Evolve2 85 (8 microphone)."
    ),
    "dien-thoai": (
        "📱 **Tư vấn chọn điện thoại:**\n"
        "- **Dưới 5 triệu:** Xiaomi Redmi Note series, Samsung Galaxy A series (A14, A25)\n"
        "- **5-10 triệu:** Samsung Galaxy A55, Xiaomi 13T, OPPO Reno series\n"
        "- **10-20 triệu:** iPhone 14, Samsung S23, Google Pixel 8, OPPO Find X\n"
        "- **Trên 20 triệu:** iPhone 15 Pro Max, Samsung S24 Ultra, Samsung Z Fold\n"
        "\n💡 **Lưu ý khi chọn:**\n"
        "- Dùng chụp ảnh: chọn camera 50MP+ như Xiaomi, Vivo, OPPO\n"
        "- Dùng gaming: chọn chip Snapdragon 8 Gen series\n"
        "- Dùng văn phòng: iPhone hoặc Samsung flagship"
    ),
    "laptop": (
        "💻 **Tư vấn chọn Laptop:**\n"
        "- **Học sinh/Văn phòng nhẹ:** HP Pavilion, Lenovo IdeaPad (15-22 triệu)\n"
        "- **Văn phòng chuyên nghiệp:** MacBook Air M2, Dell XPS, ThinkPad (27-35 triệu)\n"
        "- **Đồ họa/Video:** MacBook Pro M3, Dell XPS 15 (35-50 triệu)\n"
        "- **Gaming:** ASUS ROG, Acer Nitro, MSI (22-90 triệu)\n"
        "\n💡 **Lưu ý:**\n"
        "- RAM tối thiểu 16GB cho multitasking tốt\n"
        "- SSD NVMe nhanh hơn nhiều so với HDD"
    ),
    "my-pham": (
        "💄 **Tư vấn chăm sóc da:**\n"
        "- **Da khô:** Dưỡng ẩm Neutrogena Hydro Boost, Serum Hyaluronic Acid\n"
        "- **Da dầu/mụn:** CeraVe Cleanser, BHA Paula's Choice\n"
        "- **Da thường:** Serum Vitamin C Klairs, Laneige Sleeping Mask\n"
        "- **Routine cơ bản:** Tẩy trang → Rửa mặt → Toner → Serum → Kem dưỡng → SPF\n"
        "\n⚠️ Nên patch test sản phẩm mới trong 24-48h trước khi dùng toàn mặt."
    ),
    "the-thao": (
        "🏃 **Tư vấn dụng cụ thể thao:**\n"
        "- **Chạy bộ:** Adidas Ultraboost, Nike Air Zoom Pegasus\n"
        "- **Gym/Fitness:** Bộ tạ tay, Thảm yoga, Dây nhảy\n"
        "- **Cầu lông:** Vợt Yonex Astrox (dành cho người chơi nghiêm túc)\n"
        "- **Bóng đá:** Bóng Adidas UCL Pro (FIFA chứng nhận)\n"
        "\n💡 Đầu tư giày chất lượng là quan trọng nhất để tránh chấn thương."
    ),
}
