# E-commerce Microservice Project

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Hệ thống E-commerce xây dựng theo kiến trúc Microservices và Domain-Driven Design (DDD).

> **New to this repo?** See [`GETTING_STARTED.md`](GETTING_STARTED.md) for setup instructions, workflow guide, and submission checklist.

---

## Business Process

Hệ thống cung cấp trải nghiệm mua sắm e-commerce đầy đủ:
- **Khách hàng**: Đăng nhập, tìm kiếm sản phẩm, thêm vào giỏ hàng, đặt hàng, thanh toán, và đánh giá.
- **Nhân viên (Staff)**: Quản lý sản phẩm, tồn kho, duyệt đơn hàng.
- **Admin**: Quản lý người dùng, phân quyền hệ thống.
 Hệ thống hỗ trợ tính năng behavior tracking lưu lịch sử người dùng để phục vụ phân tích dữ liệu và AI suggest.

---

## Architecture

```mermaid
graph LR
    U[User] --> FE[Frontend :3000]
    FE --> GW[API Gateway :8000]
    
    GW --> SA[Auth :8001]
    GW --> SP[Product :8002]
    GW --> SC[Cart :8003]
    GW --> SO[Order :8004]
    GW --> SPy[Payment :8005]
    GW --> SN[Notification :8006]
    GW --> SR[Review :8007]
    
    SA --> DB1[(auth_db)]
    SP --> DB2[(product_db)]
    SC --> DB3[(cart_db)]
    SO --> DB4[(order_db)]
    SPy --> DB5[(payment_db)]
    SN --> DB6[(notification_db)]
    SR --> DB7[(review_db)]
    
    SP -.-> R[Redis :6379]
    SC -.-> R
    
    SO -.-> RM[RabbitMQ :5672]
    SPy -.-> RM
    SN -.-> RM
```

| Component | Port | Database | Responsibility |
|-----------|------|----------|----------------|
| **Frontend** | 3000 | - | ReactJS UI |
| **API Gateway** | 8000 | - | Route & auth proxy |
| **Auth Svc** | 8001 | auth_db | User & JWT |
| **Product Svc** | 8002 | product_db | Products, inventory, tracking |
| **Cart Svc** | 8003 | cart_db | Shopping cart |
| **Order Svc** | 8004 | order_db | Orders & shipping |
| **Payment Svc** | 8005 | payment_db | Payment gateways |
| **Notification Svc** | 8006 | notification_db | Email/Alerts |
| **Review Svc** | 8007 | review_db | Product ratings |

---

## Quick Start

```bash
docker compose up --build
```

Verify services:
- Gateway: `http://localhost:8000/health/`
- Products: `http://localhost:8002/api/products/`
- Frontend: `http://localhost:3000`

---

## Features

- **Tách biệt DB (Database per service)**: Đảm bảo độc lập dữ liệu theo chuẩn Microservices.
- **DDD Architecture**: Cấu trúc domain, application, infrastructure rõ ràng ở từng service.
- **Stock Lock**: Redis distributed lock chống race condition khi mua hàng.
- **Async Events**: Giao tiếp RabbitMQ (ví dụ: tạo đơn → trừ kho → thông báo).

---

## License
[MIT License](LICENSE)
