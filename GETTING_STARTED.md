# Getting Started

## Quick Start

```bash
# 1. Setup environment variables
cp .env.example .env

# 2. Build and run all services
docker compose up --build

# 3. Verify services are running
curl http://localhost:8000/api/products/
```

## System Requirements
- [x] Sửa config của PostgreSQL cho các microservice để đảm bảo phân tách csdl hoàn toàn.
- [x] Fix module `django.contrib.admin` và `django.contrib.auth` trên Product Service để xoá bỏ các table Users lọt vào `product_db`.
- [x] Sửa lỗi TEMPLATES crash trong `settings.py` cho các services (APP_DIRS & loaders conflict).
- [x] Tích hợp lệnh `makemigrations` tự động trong Dockerfile các services để tự auto-migrate các custom apps.
- [x] Seed lại dữ liệu gốc an toàn, kiểm chứng thông qua Gateway.
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

## Seed Data Accounts
Password for all initial accounts:
- Admin: `admin@shop.com` / `Admin@123`
- Staff: `staff1@shop.com` / `Staff@123`
- Customer: `customer1@gmail.com` / `Customer@123`

## Directory Structure
- `services/`: 7 Django microservices (Auth, Product, Cart, Order, Payment, Notification, Review)
- `gateway/`: API Gateway
- `frontend/`: React Vite application
- `docker-compose.yml`: Main deployment config
