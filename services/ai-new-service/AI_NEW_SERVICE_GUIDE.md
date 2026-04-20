# AI New Service — Hướng dẫn chi tiết

## Tổng quan

`ai-new-service` là một microservice AI mới được tích hợp vào hệ thống e-commerce, cung cấp:
1. **Bảng UserBehaviorData** — Lưu trữ hành vi người dùng (8 loại action)
2. **3 mô hình Deep Learning** — RNN, LSTM, BiLSTM để dự đoán và phân loại hành vi
3. **Knowledge Base Graph** — Neo4j graph database cho quan hệ user-product
4. **RAG Chat** — Chatbot thông minh dựa trên Knowledge Graph + Vector Store
5. **Giao diện Frontend** — Tab mới với danh sách recommend + chat

---

## 1. Cấu trúc thư mục

```
services/ai-new-service/
├── Dockerfile                          # Docker image (Python 3.11 + PyTorch CPU)
├── main.py                             # FastAPI app entry point
├── requirements.txt                    # Dependencies
└── app/
    ├── config.py                       # Cấu hình (DB, Neo4j, model hyperparams)
    ├── database.py                     # SQLAlchemy models (UserBehaviorData)
    ├── data_generator.py               # Sinh dữ liệu 500 users x 8 behaviors
    ├── startup.py                      # Khởi tạo khi service start
    ├── api/
    │   ├── routes.py                   # API endpoints
    │   └── schemas.py                  # Pydantic schemas
    ├── models/
    │   └── behavior_models.py          # RNN, LSTM, BiLSTM PyTorch models
    ├── training/
    │   ├── data_loader.py              # Load data từ DB → sequences → DataLoader
    │   └── trainer.py                  # Train, evaluate, compare, plot, report
    ├── knowledge_base/
    │   └── kb_graph.py                 # Neo4j Knowledge Base Graph
    └── rag/
        └── chat_engine.py              # RAG Chat (Vector Store + KB Graph)
```

---

## 2. Bảng UserBehaviorData

**File:** `app/database.py` (dòng 18-28)

```python
class UserBehaviorData(Base):
    __tablename__ = "user_behavior_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    product_id = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # 8 loại
    timestamp = Column(DateTime, default=datetime.utcnow)
```

**8 loại action:** `view`, `click`, `add_to_cart`, `purchase`, `search`, `wishlist`, `remove_from_cart`, `review`

---

## 3. Sinh dữ liệu (Data Generation)

**File:** `app/data_generator.py`

- Fetch danh sách user thực từ `auth-service` và product thực từ `product-service`
- Tạo đủ 500 user (real users + synthetic nếu thiếu)
- Mỗi user có 5-30 behavior events, phân bố theo trọng số thực tế:
  - `view`: 30%, `click`: 25%, `add_to_cart`: 15%, `purchase`: 5%, `search`: 10%, ...
- Timestamp ngẫu nhiên trong 90 ngày gần nhất
- **Chạy tự động khi service khởi động** (xem `app/startup.py` dòng 18-22)

**Chạy thủ công:**
```bash
# Qua API
curl -X POST http://localhost:8009/api/ai-new/generate-data
```

---

## 4. Mô hình RNN, LSTM, BiLSTM

### 4.1. Kiến trúc mô hình

**File:** `app/models/behavior_models.py`

| Model | Class | Kiến trúc |
|-------|-------|-----------|
| RNN | `BehaviorRNN` | 2-layer RNN, dropout=0.3 |
| LSTM | `BehaviorLSTM` | 2-layer LSTM, dropout=0.3 |
| BiLSTM | `BehaviorBiLSTM` | 2-layer Bidirectional LSTM, dropout=0.3 |

Mỗi model nhận input:
- `user_ids` → User Embedding (dim=64)
- `product_ids` → Product Embedding (dim=64)
- `action_ids` → Action Embedding (dim=32)
- Concatenate → RNN/LSTM/BiLSTM → FC layers

Output đồng thời:
- **Action prediction** (phân loại 8 hành vi tiếp theo)
- **Product prediction** (dự đoán sản phẩm tiếp theo)

### 4.2. Training

**File:** `app/training/trainer.py` (class `ModelTrainer`)

- **Data Loading:** `app/training/data_loader.py` — Chuyển behavior records thành sequences (window size = 8)
- **Loss:** CrossEntropyLoss(action) + 0.5 * CrossEntropyLoss(product)
- **Optimizer:** Adam, lr=0.001
- **Gradient clipping:** max_norm=1.0
- **Epochs:** 20, Batch size: 64
- **Train/Test split:** 80/20

### 4.3. Đánh giá & So sánh

**File:** `app/training/trainer.py` → method `_evaluate()` (dòng 113-145)

**Độ đo sử dụng:**
- Accuracy (overall)
- Precision (weighted)
- Recall (weighted)
- F1-Score (weighted)
- Confusion Matrix
- Per-class Classification Report
- Product prediction accuracy

**Chọn Best Model:** Dựa trên **F1-Score cao nhất** (dòng 207)

### 4.4. Visualization (Plots)

**File:** `app/training/trainer.py` → method `_plot_results()` (dòng 147-202)

5 biểu đồ được tự động sinh:
1. **`training_curves.png`** — Loss & Accuracy qua từng epoch (3 models)
2. **`metrics_comparison.png`** — Bar chart so sánh Accuracy, Precision, Recall, F1
3. **`confusion_matrices.png`** — Confusion matrix cho cả 3 models
4. **`per_class_f1.png`** — F1-Score theo từng loại action
5. **`radar_chart.png`** — Radar chart tổng hợp

### 4.5. Evaluation Report

**File:** `app/training/trainer.py` → method `_generate_report()` (dòng 204-280)

Tự động sinh file `model_evaluation_report.md` tại `/app/data/model_evaluation_report.md`

**Xem report qua API:**
```bash
curl http://localhost:8009/api/ai-new/report
```

**Xem plots qua API:**
```bash
curl http://localhost:8009/api/ai-new/plots/training_curves.png
curl http://localhost:8009/api/ai-new/plots/metrics_comparison.png
curl http://localhost:8009/api/ai-new/plots/confusion_matrices.png
```

**Chạy training thủ công:**
```bash
curl -X POST http://localhost:8009/api/ai-new/train -H "Content-Type: application/json" -d '{"force": true}'
curl http://localhost:8009/api/ai-new/train/status
```

---

## 5. Knowledge Base Graph (Neo4j)

**File:** `app/knowledge_base/kb_graph.py`

### Nodes:
- **User** — id
- **Product** — id, name, price, brand, rating, description, stock
- **Category** — id, name

### Relationships:
- `(User)-[:VIEW]->(Product)` — User đã xem sản phẩm
- `(User)-[:CLICK]->(Product)` — User đã click sản phẩm
- `(User)-[:ADD_TO_CART]->(Product)` — User đã thêm vào giỏ
- `(User)-[:PURCHASE]->(Product)` — User đã mua
- `(User)-[:SEARCH]->(Product)` — User đã tìm kiếm
- `(User)-[:WISHLIST]->(Product)` — User đã thêm wishlist
- `(User)-[:REVIEW]->(Product)` — User đã đánh giá
- `(Product)-[:BELONGS_TO]->(Category)` — Sản phẩm thuộc danh mục
- `(Product)-[:CO_PURCHASED]->(Product)` — Được mua cùng nhau (≥2 users)
- `(Product)-[:CO_VIEWED]->(Product)` — Được xem cùng nhau (≥3 users)

### Graph Queries (dòng 130-185):
- `query_user_recommendations()` — Collaborative filtering qua graph
- `query_similar_products()` — Tìm sản phẩm tương tự
- `get_user_profile()` — Lấy profile hành vi user
- `graph_context_for_rag()` — Cung cấp context cho RAG

**Truy cập Neo4j Browser:** http://localhost:7474 (neo4j/neo4jpassword)

**Rebuild KB qua API:**
```bash
curl -X POST http://localhost:8009/api/ai-new/kb/build
```

---

## 6. RAG Chat Engine

**File:** `app/rag/chat_engine.py`

### Kiến trúc RAG:
1. **Vector Store (ChromaDB)** — Index tất cả sản phẩm bằng sentence-transformers
2. **Knowledge Graph (Neo4j)** — Lấy context từ quan hệ user-product
3. **Intent Detection** — Phát hiện ý định: gợi ý, so sánh, giá, tìm kiếm, general
4. **Response Generation** — Kết hợp graph context + vector context để trả lời

### Flow xử lý chat (dòng 93-110):
```
User Message → Intent Detection → Search Vector Store + Query KB Graph → Generate Response
```

### API Endpoints:
```bash
# Chat
curl -X POST http://localhost:8009/api/ai-new/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Gợi ý laptop cho tôi", "user_id": "user123"}'

# Recommendations
curl http://localhost:8009/api/ai-new/recommend/user123
```

---

## 7. Tích hợp Frontend

### File mới: `frontend/src/pages/AINewRecommend.jsx`

Giao diện gồm 3 tab:
1. **Gợi ý sản phẩm** — Hiển thị danh sách recommend từ model + graph
2. **Chat AI (RAG)** — Giao diện chat với RAG engine
3. **Thống kê & Model** — Dashboard hiển thị stats, action distribution, model training status

### Cập nhật files:
- `frontend/src/App.jsx` — Thêm route `/ai-recommend`
- `frontend/src/components/Header.jsx` — Thêm tab "AI Recommend" trên navigation
- `frontend/src/utils/aiTracking.js` — Gửi tracking đến cả ai-new-service

---

## 8. Cập nhật Behavior Tracking

**File:** `frontend/src/utils/aiTracking.js` (dòng 36-48)

Khi user thực hiện hành vi (view, click, add_to_cart), frontend gửi đồng thời đến:
1. `ai-service` (service cũ, giữ nguyên)
2. `ai-new-service` → Ghi vào bảng `UserBehaviorData`

**Các điểm gọi tracking:**
- `frontend/src/pages/ProductDetail.jsx` dòng 31 — `trackBehavior(userId, productId, 'view_detail')`
- `frontend/src/pages/ProductDetail.jsx` dòng 58 — `trackBehavior(userId, productId, 'add_to_cart')`

---

## 9. Docker & Chạy dự án

### Các container mới:
| Container | Port | Mô tả |
|-----------|------|-------|
| `postgres-ai-new` | 5439:5432 | PostgreSQL cho ai-new-service |
| `neo4j` | 7474, 7687 | Neo4j graph database |
| `ai-new-service` | 8009:8000 | FastAPI AI service |

### Chạy toàn bộ:
```bash
docker compose up --build
```

### Chạy riêng ai-new-service:
```bash
docker compose up --build postgres-ai-new neo4j ai-new-service
```

### Volumes:
- `ai_new_models` — Lưu model weights (.pt files)
- `ai_new_plots` — Lưu biểu đồ (.png files)
- `ai_new_chromadb` — Vector store data
- `neo4j_data` — Neo4j graph data

---

## 10. API Endpoints Summary

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/health` | Health check |
| POST | `/api/ai-new/track` | Ghi hành vi user |
| GET | `/api/ai-new/recommend/{user_id}` | Lấy recommendations |
| POST | `/api/ai-new/chat` | Chat với RAG |
| POST | `/api/ai-new/train` | Trigger training |
| GET | `/api/ai-new/train/status` | Training status + results |
| GET | `/api/ai-new/kb/status` | KB Graph status |
| POST | `/api/ai-new/kb/build` | Rebuild KB Graph |
| POST | `/api/ai-new/generate-data` | Sinh dữ liệu |
| GET | `/api/ai-new/stats` | Thống kê behavior data |
| GET | `/api/ai-new/plots/{filename}` | Xem biểu đồ |
| GET | `/api/ai-new/report` | Xem evaluation report |

---

## 11. Quy trình khởi động tự động

**File:** `app/startup.py`

Khi `ai-new-service` khởi động:
1. **Tạo bảng DB** (`init_db()`) — dòng 16
2. **Sinh dữ liệu** (`generate_behavior_data()`) — dòng 20 (500 users x 8 behaviors)
3. **Train 3 models** (`trainer.train_all()`) — dòng 25 (RNN, LSTM, BiLSTM)
4. **Build KB Graph** (`kb_graph.build_graph()`) — dòng 32 (Neo4j)
5. **Init RAG Engine** (`chat_engine.initialize()`) — dòng 38 (ChromaDB + Embeddings)

> **Lưu ý:** Lần đầu khởi động mất ~2-5 phút (download model, train, build graph).
> Các lần sau nhanh hơn vì data đã tồn tại và model đã được cache.
