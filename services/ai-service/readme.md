# AI Service — Phân tích hành vi & Tư vấn mua sắm

## Tổng quan

AI Service là microservice độc lập tích hợp 3 thành phần AI chính phục vụ bài toán **phân tích hành vi khách hàng** và **tư vấn mua sắm** trong hệ thống Ecommerce:

1. **model_behavior** — Mô hình Deep Learning (NCF + LSTM) phân tích hành vi và cá nhân hóa gợi ý sản phẩm
2. **Knowledge Base (KB)** — Cơ sở tri thức vector từ catalog sản phẩm, FAQ và tư vấn danh mục
3. **RAG Chat** — Hệ thống chat tư vấn thông minh dựa trên Retrieval-Augmented Generation

Service không có database riêng. Dữ liệu sản phẩm và hành vi lấy từ `product-service` qua API.

---

## Stack công nghệ

| Thành phần | Công nghệ |
|---|---|
| API Framework | FastAPI + WebSockets |
| Deep Learning | PyTorch (CPU) |
| Embedding | sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`) |
| Vector Store | ChromaDB (persistent, cosine similarity) |
| Knowledge Graph | **Neo4j 5 Community** (bolt://neo4j-ai:7687, GUI: 7475) |
| RAG Framework | LangChain + langchain-core |
| Cache / Session | Redis (DB 2) |
| HTTP Client | httpx (async) |
| Cổng trực tiếp | 8008 |
| Cổng qua Gateway | 8000 (`/api/ai/...`) |

---

## API Endpoints

| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/ai/health` | Health check qua gateway |
| POST | `/api/ai/chat` | Chat tư vấn (HTTP fallback) |
| WS | `/ws/chat/{session_id}` | Chat real-time (WebSocket) |
| GET | `/api/ai/recommend/{user_id}` | Gợi ý sản phẩm cá nhân hóa |
| POST | `/api/ai/track` | Ghi nhận hành vi người dùng |
| GET | `/api/ai/kb/status` | Trạng thái Knowledge Base (ChromaDB) |
| POST | `/api/ai/kb/build` | Rebuild KB thủ công |
| POST | `/api/ai/train` | Kích hoạt train model |
| GET | `/api/ai/train/status` | Trạng thái / tiến trình train |
| GET | `/api/ai/graph/status` | Trạng thái Neo4j Knowledge Graph |
| POST | `/api/ai/graph/build` | Rebuild Neo4j graph thủ công |
| GET | `/api/ai/graph/explore` | Khám phá subgraph (viewer) |
| GET | `/api/ai/graph/related` | Sản phẩm liên quan qua graph traversal |

---

## Quy trình khởi động tự động

> 📄 Code: `app/startup.py` — `run_startup_pipeline()`

Khi container start, `app/startup.py` chạy pipeline theo thứ tự:

```
1. Load Embedding Model (paraphrase-multilingual-MiniLM-L12-v2)
2. Khởi tạo ChromaDB Vector Store
3. Kết nối Neo4j Graph Store (bolt://neo4j-ai:7687)
4. Kết nối Redis
5. Fetch toàn bộ sản phẩm từ product-service (retry 8 lần × 10s)
6. Build Knowledge Base → index vào ChromaDB
7. Build Knowledge Graph → push nodes/edges vào Neo4j
8. Fetch behavior data từ /api/analytics/behavior/
9. Nếu model đã có (meta.json) → Load model từ volume
10. Nếu chưa có → Train NCF + LSTM từ đầu
11. Rebuild idx_to_product cache từ danh sách sản phẩm mới nhất
```

---

---

## 1. Xây dựng mô hình model_behavior (Deep Learning)

### Mục tiêu

Học từ lịch sử hành vi người dùng (xem sản phẩm, click, mua hàng) để dự đoán sản phẩm họ có khả năng quan tâm tiếp theo. Dùng kết quả này để cá nhân hóa danh sách gợi ý (`/api/ai/recommend/{user_id}`).

### Dữ liệu đầu vào

> 📄 Code fetch: `app/training/data_loader.py` — `fetch_behavior_data()`, `build_from_real_data()`, `generate_synthetic_interactions()`
> 📄 Profiles giả lập: `app/training/data_loader.py` — hằng số `USER_PROFILES` (10 profile)
> 📄 DB models nguồn: `services/product-service/analytics/models.py`

Dữ liệu được lấy từ `product-service` qua endpoint `GET /api/analytics/behavior/`:

| Bảng DB | Mô tả | Weight |
|---|---|---|
| `user_product_views` | Lượt xem chi tiết sản phẩm | 0.7 |
| `user_click_events` | Sự kiện click, add_to_cart, purchase | 1.0 |
| `user_search_logs` | Lịch sử tìm kiếm | (context) |

**Ngưỡng chọn nguồn dữ liệu:**
- Nếu tổng events ≥ 500 → dùng **real data** từ DB
- Nếu < 500 → dùng **synthetic data** (500 users giả lập theo 10 profile hành vi khác nhau)

### Kiến trúc mô hình

#### 1.1 NCF — Neural Collaborative Filtering (`NCFModel`)

> 📄 Code: `app/models/behavior_model.py` — class `NCFModel`
> 📄 Train: `app/training/trainer.py` — `_train_ncf()`
> 📄 Dataset: `app/training/data_loader.py` — class `InteractionDataset`

Dự đoán xác suất user tương tác với item, kết hợp 2 pathway:

```
User Embedding GMF (64-dim) ──┐
                               ├── element-wise multiply ──┐
Item Embedding GMF (64-dim) ──┘                             │
                                                             ├── Linear(96→1) → Sigmoid
User Embedding MLP (64-dim) ──┐                             │
                               ├── Linear(128→64→32) ───────┘
Item Embedding MLP (64-dim) ──┘
      BatchNorm + ReLU + Dropout(0.2)
```

| Siêu tham số | Giá trị |
|---|---|
| Embedding dim | 64 |
| Loss | BCELoss (binary cross-entropy) |
| Optimizer | Adam (lr=0.001, weight_decay=1e-5) |
| Batch size | 256 |
| Epochs | 15 |
| Gradient clipping | max_norm=1.0 |

**Dữ liệu train NCF:**
- Positive samples: `(user_idx, item_idx, label=0.7~1.0)` từ hành vi thực
- Negative samples: sampling ngẫu nhiên item user chưa tương tác, `label=0.0`

#### 1.2 Sequence Model — LSTM Next-Item Prediction (`SequenceModel`)

> 📄 Code: `app/models/behavior_model.py` — class `SequenceModel`
> 📄 Train: `app/training/trainer.py` — `_train_seq()`
> 📄 Dataset: `app/training/data_loader.py` — class `SequenceDataset`
> 📄 Lưu/Load: `app/models/behavior_model.py` — class `ModelRegistry`

Dự đoán sản phẩm tiếp theo dựa trên chuỗi hành vi gần nhất của user:

```
Input: [item_1, item_2, ..., item_t-1]   (padding 0 nếu < SEQ_LEN=10)
        ↓
Item Embedding (128-dim, padding_idx=0)
        ↓
LSTM 2 lớp (hidden=256, dropout=0.3, unidirectional)
        ↓
Attention Pooling: softmax(W·h) → weighted sum
        ↓
FC: Linear(256) → LayerNorm → ReLU → Dropout(0.3) → Linear(n_items+2)
        ↓
Logits → argsort → Top-K next items
```

| Siêu tham số | Giá trị |
|---|---|
| Embedding dim | 128 |
| LSTM hidden dim | 256 |
| LSTM layers | 2 |
| Sequence length | 10 |
| Loss | CrossEntropyLoss (next-item classification) |
| Optimizer | Adam (lr=0.001) |
| Epochs | 15 |

**Dataset construction:** Từ mỗi chuỗi hành vi `[i1, i2, i3, ..., iN]`, tạo N-1 mẫu huấn luyện:
```
seq=[i1], target=i2
seq=[i1,i2], target=i3
...
seq=[i1,...,iN-1], target=iN
```

### Inference — Gợi ý cá nhân hóa (4 tầng)

> 📄 Code endpoint: `app/api/routes.py` — `get_recommendations()`
> 📄 LSTM infer: `app/training/trainer.py` — `recommend_for_sequence()`
> 📄 Content-based: `app/api/routes.py` — `_content_based_recommend()`
> 📄 Popularity: `app/training/trainer.py` — `recommend_popular()`

Khi gọi `GET /api/ai/recommend/{user_id}`:

```
Tầng 1 — LSTM Sequence Model (tốt nhất)
  Điều kiện: model đã train + user có behavior trong Redis + ≥50% product IDs khớp item_map
  Output: danh sách item index → map sang sản phẩm
  Bonus: tăng điểm (logit +0.5) cho sản phẩm cùng danh mục với lịch sử xem

Tầng 2 — Content-Based (ChromaDB)
  Điều kiện: KB ready + user có behavior trong Redis
  Output: tìm sản phẩm tương tự với 3-6 sản phẩm đã xem gần nhất
  Filter: ưu tiên danh mục chiếm ≥50% lịch sử xem

Tầng 3 — Category-Affinity Popularity
  Điều kiện: user có behavior nhưng không có model/KB
  Output: sản phẩm phổ biến nhất trong danh mục user hay xem nhất

Tầng 4 — Global Popularity (fallback)
  Điều kiện: không có behavior
  Score = rating_avg × 0.4 + (sold_count / 500) × 0.6
```

### Lưu trữ model

| File | Nội dung |
|---|---|
| `/app/data/models/ncf.pt` | Weights NCF model |
| `/app/data/models/seq.pt` | Weights LSTM model |
| `/app/data/models/meta.json` | n_users, n_items, user_map, item_map, metrics |

---

## 2. Xây dựng Knowledge Base (KB)

### Mục tiêu

Xây dựng bộ nhớ ngữ nghĩa (vector database) từ catalog sản phẩm, FAQ, và tư vấn theo danh mục. KB là nền tảng để hệ thống RAG tìm kiếm nội dung liên quan khi người dùng đặt câu hỏi.

### Nguồn dữ liệu

> 📄 Dữ liệu FAQ & tư vấn danh mục: `app/knowledge_base/faq_data.py` — `FAQ_DATA`, `CATEGORY_ADVICE`
> 📄 Dữ liệu sản phẩm: fetch từ `product-service` qua `app/knowledge_base/builder.py` — `fetch_all_products()`

KB bao gồm 3 loại document:

| Loại | Nguồn | `doc_type` |
|---|---|---|
| Thông tin sản phẩm | Fetch từ `product-service /api/products/` | `product` |
| Câu hỏi thường gặp | File tĩnh `faq_data.py` | `faq` |
| Tư vấn theo danh mục | File tĩnh `faq_data.py` (CATEGORY_ADVICE) | `advice` |

### Pipeline xây dựng KB

> 📄 Code: `app/knowledge_base/builder.py` — `build_documents()`, `_build_product_text()`
> 📄 Gọi khi startup: `app/startup.py` — `run_startup_pipeline()`
> 📄 Gọi khi rebuild thủ công: `app/api/routes.py` — `rebuild_kb()`

**Bước 1: Fetch sản phẩm**
```
GET product-service/api/products/?limit=100&page=N
→ Phân trang tự động đến hết
→ Retry 6 lần × 10s nếu service chưa sẵn sàng
```

**Bước 2: Tạo document text cho mỗi sản phẩm**
```
Sản phẩm: {name}
Thương hiệu: {brand}
Danh mục: {category_name}
Giá: {price} (Giảm X% từ {compare_price})
Thông số kỹ thuật: {key: value | ...}
Mô tả: {description[:300]}
Đánh giá: {rating_avg}/5 ({rating_count} lượt)
Đã bán: {sold_count} sản phẩm
```

**Bước 3: Gắn metadata cho mỗi document**

```json
{
  "id": "uuid",
  "name": "Tên sản phẩm",
  "brand": "Thương hiệu",
  "price": 1200000,
  "compare_price": 1500000,
  "category_slug": "dien-thoai",
  "category_name": "Điện thoại",
  "rating_avg": 4.5,
  "rating_count": 123,
  "sold_count": 456,
  "slug": "ten-san-pham",
  "image_url": "...",
  "doc_type": "product"
}
```

> Tất cả trường số được ép kiểu `int`/`float` tường minh để tránh lỗi ChromaDB khi nhận string từ API.

**Bước 4: Embedding + Index vào ChromaDB**
```
text → sentence-transformer encode → vector (384-dim)
→ Batch insert vào ChromaDB collection "ecommerce_kb"
→ Hnsw index với cosine similarity
→ Batch size: 100 documents/lần
```

### Cấu trúc ChromaDB collection

> 📄 Code: `app/rag/vector_store.py` — class `VectorStore`, `build()`, `search_products()`
> 📄 Embedding: `app/rag/embeddings.py` — class `EmbeddingService`

- **Collection:** `ecommerce_kb`
- **Similarity:** cosine
- **Index:** HNSW (Hierarchical Navigable Small World)
- **Embedding model:** `paraphrase-multilingual-MiniLM-L12-v2` (hỗ trợ đa ngôn ngữ, tiếng Việt)

### Rebuild KB

KB tự động build khi khởi động. Để rebuild thủ công sau khi cập nhật sản phẩm:

```bash
# Qua API
curl -X POST http://localhost:8008/api/ai/kb/build

# Hoặc qua gateway
curl -X POST http://localhost:8000/api/ai/kb/build
```

Trong giao diện chat (`/ai-chat`), khi KB chưa sẵn sàng sẽ xuất hiện nút **"Xây dựng lại KB"**.

---

## 3. Áp dụng RAG cho Chat tư vấn

### Mục tiêu

Kết hợp khả năng tìm kiếm ngữ nghĩa (Retrieval) với phản hồi có cấu trúc (Generation) để tư vấn mua sắm chính xác, contextual, và hỗ trợ tiếng Việt.

### Kiến trúc tổng thể

```
User message
     ↓
┌─────────────────────────────────┐
│   Intent Detection (regex)      │
│   faq / compare / recommend /   │
│   price_query / search / general│
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│   Entity Extraction             │
│   - Category slug               │
│   - Price range (min, max)      │
│   - Sort direction (asc/desc)   │
│   - Product names (compare)     │
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│   ChromaDB Retrieval            │
│   - Semantic search (cosine)    │
│   - Filter: doc_type, category, │
│     min_price, max_price        │
│   - Fallback: keyword search    │
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│   Response Generation           │
│   - Format product cards        │
│   - Sort / rank results         │
│   - Append category advice      │
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│   Redis Memory                  │
│   - Lưu hội thoại (chat:sid)    │
│   - Lưu behavior (behavior:uid) │
│   - TTL: 1h (chat) / 24h (beh.) │
└─────────────────────────────────┘
```

### Intent Detection

> 📄 Code: `app/rag/chat_engine.py` — `detect_intent()`, các regex `_SEARCH_KW`, `_COMPARE_KW`, `_RECOMMEND_KW`, `_FAQ_KW`, `_PRICE_KW`, `_PRICE_RANGE`, `_PRICE_RANGE_FULL`

Phân loại câu hỏi bằng regex trước khi gọi ChromaDB:

| Intent | Từ khóa nhận biết | Handler |
|---|---|---|
| `faq` | chính sách, đổi trả, giao hàng, bảo hành, thanh toán... | `_handle_faq` |
| `compare` | so sánh, tốt hơn, khác nhau, nên chọn, vs... | `_handle_compare` |
| `recommend` | gợi ý, đề xuất, nên mua, tư vấn, phù hợp... | `_handle_recommend` |
| `price_query` | giá, rẻ nhất, đắt nhất, dưới X, từ X đến Y... | `_handle_price_query` |
| `search` | tìm, mua, cần, muốn, có bán... | `_handle_search` |
| `general` | (còn lại) | `_handle_general` |

### Entity Extraction

> 📄 Code: `app/rag/chat_engine.py` — `extract_category()` (`_CATEGORY_MAP`), `extract_price_range()`, `extract_max_price()`, `extract_compare_products()`

```python
# Danh mục sản phẩm
"điện thoại" → "dien-thoai"
"laptop", "macbook" → "laptop"
"tai nghe", "airpods" → "am-thanh"
"đồng hồ", "smartwatch" → "dong-ho"
# ... 10 danh mục

# Tầm giá
"dưới 5 triệu" → max_price=5_000_000
"từ 2 triệu đến 10 triệu" → min_price=2M, max_price=10M
"rẻ nhất" → sort ASC
"đắt nhất" → sort DESC

# So sánh
"so sánh iPhone 15 và Samsung Galaxy A55"
→ ["iPhone 15", "Samsung Galaxy A55"]
```

### Chi tiết từng Handler

> 📄 Code: `app/rag/chat_engine.py` — class `ChatEngine`, các method `_handle_*`
> 📄 Format sản phẩm hiển thị: `app/rag/chat_engine.py` — `_product_card()`

#### `_handle_search`
- ChromaDB semantic search với filter `category_slug`, `max_price`
- Trả tối đa 5 sản phẩm phù hợp nhất theo độ tương đồng

#### `_handle_price_query`
- Fetch nhiều candidates (n=20 nếu có filter giá)
- Fallback 3 tầng nếu filter quá chặt:
  1. Tìm theo keyword danh mục (tên tiếng Việt)
  2. Tìm rộng rồi filter theo `category_name`
  3. Tìm toàn bộ rồi filter giá
- Sort: ASC (rẻ nhất) / DESC (đắt nhất) / ASC (khoảng giá)
- Header động: "Sản phẩm dưới 5tr", "Sản phẩm từ 2tr đến 10tr", "Giá cao nhất"

#### `_handle_compare`
- Tách tên 2 sản phẩm từ câu hỏi bằng regex
- Tìm từng sản phẩm riêng lẻ trong ChromaDB (top-1 mỗi cái)
- So sánh: giá, rating, sold_count
- Tổng kết: "A rẻ hơn X%, B đánh giá cao hơn, C bán chạy hơn"

#### `_handle_recommend`
- Kết hợp query gốc + context hành vi user (5 product ID gần nhất)
- Sort kết quả theo: `rating_avg × 0.4 + (sold_count/500) × 0.6`
- Nếu có `category_slug` → append `CATEGORY_ADVICE` tương ứng

#### `_handle_faq`
- Tìm kiếm trong ChromaDB với `doc_type=faq`
- Chỉ trả câu trả lời nếu similarity score > 0.3
- Fallback: hướng dẫn liên hệ hotline

#### `_handle_general`
- Tìm kiếm không phân loại, mix cả product + faq
- Nếu có product → hiển thị product cards
- Nếu có faq/advice → trả text tư vấn

### Real-time Chat qua WebSocket

> 📄 Backend: `app/api/routes.py` — `websocket_chat()`, class `ConnectionManager`
> 📄 Frontend: `frontend/src/pages/AIChat.jsx` — `connectWS()`, `sendMessage()`
> 📄 Widget: `frontend/src/components/AIChatWidget.jsx`

```
Client ──── ws://ai-service:8008/ws/chat/{session_id}?user_id={uid}
               ↓
          Gửi: {"message": "...", "user_id": "..."}
               ↓
          Nhận: {"type": "typing"} → hiển thị loading dots
               ↓
          Nhận: {"type": "message", "message": "...", "products": [...], "intent": "..."}
```

- Mỗi session có lịch sử hội thoại riêng lưu trong Redis (key: `chat:{session_id}`)
- Giữ tối đa 10 tin nhắn gần nhất
- TTL: 3600 giây (1 giờ)
- HTTP fallback: `POST /api/ai/chat` nếu WebSocket không kết nối được

### Theo dõi hành vi trong chat

> 📄 Ghi Redis: `app/rag/chat_engine.py` — `track_behavior()`, `get_user_behavior()`
> 📄 Persist DB: `app/api/routes.py` — `_persist_to_analytics()` (background task)
> 📄 Frontend gọi: `frontend/src/utils/aiTracking.js` — `trackBehavior()`

Khi AI trả về sản phẩm trong chat, hệ thống tự động track product IDs vào Redis:
```
behavior:{user_id} → [pid1, pid2, ...] (50 item gần nhất, TTL 24h)
```

Đồng thời, `POST /api/ai/track` (từ frontend) còn persist vào DB qua product-service analytics:
- `view_detail` → `user_product_views`
- `add_to_cart` → `user_click_events`

---

## Luồng dữ liệu hành vi đầy đủ

```
User xem sản phẩm
    ↓
FE gửi POST /api/ai/track {user_id, product_id, event_type}
    ↓
ai-service → Redis behavior:{user_id}  (dùng ngay cho recommend)
    ↓ (background task)
ai-service → product-service /api/analytics/view/ hoặc /event/
    ↓
Lưu vào DB: user_product_views / user_click_events
    ↓ (khi train model)
fetch_behavior_data() → /api/analytics/behavior/
    ↓
Train NCF + LSTM với real data → model ngày càng chính xác hơn
```

---

## Hướng dẫn vận hành

### Seed dữ liệu ban đầu

> 📄 Code seed sản phẩm: `services/product-service/domain/management/commands/seed_products.py`
> 📄 Code seed hành vi: `services/product-service/domain/management/commands/seed_behavior.py`

```bash
# Seed sản phẩm (10 categories, 115+ sản phẩm)
docker compose exec product-service python manage.py seed_products

# Seed hành vi giả lập (500 users, 20.000+ interactions)
docker compose exec product-service python manage.py seed_behavior
```

### Train lại model

```bash
# Trigger qua API
curl -X POST http://localhost:8000/api/ai/train

# Theo dõi tiến trình
curl http://localhost:8000/api/ai/train/status
```

### Rebuild Knowledge Base

```bash
curl -X POST http://localhost:8000/api/ai/kb/build

# Kiểm tra trạng thái
curl http://localhost:8000/api/ai/kb/status
```

### Kiểm tra health

```bash
curl http://localhost:8000/api/ai/health
# → {"status":"ok","kb_ready":true,"model_ready":true,"total_products":115}
```

---

## 4. Neo4j Knowledge Graph

> 📄 Code: `app/graph/graph_store.py` — class `KnowledgeGraph`  
> 📄 Builder: `app/graph/graph_builder.py` — `build_graph()`  
> 📄 Startup: `app/startup.py` — `_build_graph()`

### Mục tiêu

Neo4j lưu **đồ thị tri thức** quan hệ giữa sản phẩm, danh mục và thương hiệu. Khi người dùng search hoặc request gợi ý, ngoài kết quả từ ChromaDB, AI còn dùng Neo4j để **tìm sản phẩm liên quan theo quan hệ đồ thị** (SIMILAR_TO, IN_CATEGORY, MADE_BY), làm giàu ngữ cảnh phản hồi.

### Graph Model

```
Nodes:
  (:Product {id, name, slug, price, brand, category_slug, category_name, rating_avg, sold_count, image_url})
  (:Category {slug, name})
  (:Brand {name})

Relationships:
  (:Product)-[:IN_CATEGORY]->(:Category)
  (:Product)-[:MADE_BY]->(:Brand)
  (:Product)-[:SIMILAR_TO {score: 0.0-1.0}]->(:Product)
```

**SIMILAR_TO** được tạo tự động giữa 2 sản phẩm cùng danh mục nếu:
- Chênh lệch giá ≤ 35%
- Chênh lệch rating ≤ 1.0
- Score = 0.6 × (1 - price_diff%) + 0.4 × (1 - rating_diff/5)

### Xem graph trên Neo4j Browser

**Truy cập:** `http://localhost:7475`  
**Login:** username `neo4j` / password `neo4jpassword`  

#### Cypher queries để khám phá:

```cypher
-- Xem tổng quan (Product + Category + Brand + edges)
MATCH (p:Product)-[r]->(n) RETURN p, r, n LIMIT 50

-- Xem đồ thị của 1 danh mục cụ thể
MATCH (p:Product)-[:IN_CATEGORY]->(c:Category {slug: 'dien-thoai'})
RETURN p, c LIMIT 30

-- Xem sản phẩm tương tự SIMILAR_TO
MATCH (a:Product)-[r:SIMILAR_TO]->(b:Product)
RETURN a.name, b.name, r.score
ORDER BY r.score DESC LIMIT 20

-- Xem sản phẩm của 1 thương hiệu
MATCH (p:Product)-[:MADE_BY]->(b:Brand {name: 'Apple'})
RETURN p.name, p.price, p.rating_avg
ORDER BY p.rating_avg DESC

-- Đếm node và relationship
MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count
UNION
MATCH ()-[r]->() RETURN type(r) AS label, count(r) AS count

-- Path 2-hop: sản phẩm cùng danh mục với sản phẩm X
MATCH (p:Product {id: 'PRODUCT_ID'})-[:IN_CATEGORY]->(c)<-[:IN_CATEGORY]-(related)
RETURN p, c, related LIMIT 20
```

### API Graph endpoints

```bash
# Kiểm tra trạng thái graph
curl http://localhost:8008/api/ai/graph/status
# → {"is_ready":true,"is_connected":true,"products":115,"categories":10,"brands":25,"similar_edges":340}

# Rebuild graph thủ công (background)
curl -X POST http://localhost:8008/api/ai/graph/build

# Khám phá subgraph của 1 danh mục (trả JSON nodes + relationships)
curl "http://localhost:8008/api/ai/graph/explore?type=category&id=dien-thoai&limit=30"

# Khám phá subgraph của 1 product
curl "http://localhost:8008/api/ai/graph/explore?type=product&id=<PRODUCT_UUID>"

# Khám phá subgraph của 1 brand
curl "http://localhost:8008/api/ai/graph/explore?type=brand&id=Apple&limit=20"

# Lấy sản phẩm liên quan trực tiếp (SIMILAR_TO + same category)
curl "http://localhost:8008/api/ai/graph/related?product_id=<PRODUCT_UUID>&limit=5"
```

### Tích hợp vào Chat (Graph Enrichment)

Khi `intent=search` hoặc `intent=recommend`, sau khi ChromaDB trả kết quả:

```
ChromaDB top result (product_id)
          ↓
Neo4j: MATCH (p:Product {id})-[:SIMILAR_TO | IN_CATEGORY]->(related)
          ↓
Lọc bỏ sản phẩm đã hiển thị
          ↓
Append section "🔗 Sản phẩm liên quan (theo đồ thị tri thức)"
```

Nếu Neo4j không kết nối được → graceful fallback, chỉ trả kết quả ChromaDB như cũ.

### Rebuild Graph

```bash
# Trigger qua API (khuyến nghị sau khi seed/update sản phẩm)
curl -X POST http://localhost:8000/api/ai/graph/build

# Kiểm tra sau khi rebuild
curl http://localhost:8000/api/ai/graph/status
```

---

## Hướng dẫn vận hành

### Seed dữ liệu ban đầu

> 📄 Code seed sản phẩm: `services/product-service/domain/management/commands/seed_products.py`
> 📄 Code seed hành vi: `services/product-service/domain/management/commands/seed_behavior.py`

```bash
# Seed sản phẩm (10 categories, 115+ sản phẩm)
docker compose exec product-service python manage.py seed_products

# Seed hành vi giả lập (500 users, 20.000+ interactions)
docker compose exec product-service python manage.py seed_behavior
```

### Train lại model

```bash
# Trigger qua API
curl -X POST http://localhost:8000/api/ai/train

# Theo dõi tiến trình
curl http://localhost:8000/api/ai/train/status
```

### Rebuild Knowledge Base (ChromaDB)

```bash
curl -X POST http://localhost:8000/api/ai/kb/build

# Kiểm tra trạng thái
curl http://localhost:8000/api/ai/kb/status
```

### Rebuild Knowledge Graph (Neo4j)

```bash
curl -X POST http://localhost:8000/api/ai/graph/build

# Kiểm tra trạng thái
curl http://localhost:8000/api/ai/graph/status
```

### Kiểm tra health

```bash
curl http://localhost:8000/api/ai/health
# → {"status":"ok","kb_ready":true,"model_ready":true,"total_products":115}
```

---

## Docker Volumes

| Volume | Mount point | Nội dung |
|---|---|---|
| `ai_models` | `/app/data/models/` | `ncf.pt`, `seq.pt`, `meta.json` |
| `ai_chromadb` | `/app/data/chromadb/` | ChromaDB HNSW index |
| `neo4j_ai_data` | `/data` (container `neo4j-ai`) | Neo4j graph database (chỉ riêng ai-service) |

