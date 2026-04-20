"""RAG Chat Engine using KB Graph + Vector Store."""
import logging
from typing import Optional

from sentence_transformers import SentenceTransformer
import chromadb
import httpx

from app.config import settings
from app.knowledge_base.kb_graph import KnowledgeBaseGraph

logger = logging.getLogger(__name__)


class RAGChatEngine:
    """RAG system: combines KB Graph context + vector store retrieval."""

    def __init__(self, kb_graph: KnowledgeBaseGraph):
        self.kb_graph = kb_graph
        self.embedder = None
        self.chroma_client = None
        self.collection = None
        self.ready = False

    def initialize(self):
        """Load embedding model and vector store."""
        try:
            logger.info("Loading embedding model...")
            self.embedder = SentenceTransformer(settings.EMBEDDING_MODEL)

            chroma_path = f"{settings.DATA_DIR}/chromadb_new"
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name="products",
                metadata={"hnsw:space": "cosine"},
            )
            self.ready = True
            logger.info("RAG Chat Engine initialized.")
        except Exception as e:
            logger.error(f"Failed to init RAG engine: {e}")

    async def index_products(self):
        """Fetch products and index into vector store."""
        if not self.embedder:
            return 0

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{settings.PRODUCT_SERVICE_URL}/api/products/?page_size=500")
                if resp.status_code != 200:
                    return 0
                data = resp.json()
                products = data if isinstance(data, list) else data.get("results", [])
        except Exception as e:
            logger.warning(f"Cannot fetch products for indexing: {e}")
            return 0

        if not products:
            return 0

        ids, documents, metadatas = [], [], []
        for p in products:
            pid = str(p["id"])
            cat_name = p.get("category", {}).get("name", "") if isinstance(p.get("category"), dict) else ""
            doc = f"{p.get('name', '')} - {p.get('brand', '')} - {cat_name} - {p.get('description', '')[:300]} - Giá: {p.get('price', 0)}đ"
            ids.append(pid)
            documents.append(doc)
            metadatas.append({
                "name": p.get("name", ""),
                "price": float(p.get("price", 0)),
                "brand": p.get("brand", ""),
                "category": cat_name,
                "rating": float(p.get("rating_avg", 0)),
            })

        # Upsert to ChromaDB
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
            )

        logger.info(f"Indexed {len(products)} products into vector store.")
        return len(products)

    def search_products(self, query: str, n_results: int = 5):
        """Search products in vector store."""
        if not self.collection:
            return []
        results = self.collection.query(query_texts=[query], n_results=n_results)
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                "distance": results["distances"][0][i] if results.get("distances") else 0,
            })
        return items

    def chat(self, user_message: str, user_id: Optional[str] = None, product_id: Optional[str] = None) -> str:
        """Process a chat message using RAG."""
        if not self.ready:
            return "Hệ thống AI đang khởi tạo, vui lòng thử lại sau."

        # 1. Get graph context
        graph_context = ""
        if self.kb_graph and self.kb_graph.ready:
            graph_context = self.kb_graph.graph_context_for_rag(user_id=user_id, product_id=product_id)

        # 2. Search vector store
        search_results = self.search_products(user_message, n_results=5)
        vector_context = ""
        if search_results:
            vector_context = "Sản phẩm liên quan:\n"
            for item in search_results:
                meta = item.get("metadata", {})
                vector_context += f"- {meta.get('name', 'N/A')} ({meta.get('brand', '')}) - {meta.get('price', 0):,.0f}đ - Rating: {meta.get('rating', 0)}\n"

        # 3. Build response using context
        response = self._generate_response(user_message, graph_context, vector_context, user_id)
        return response

    def _generate_response(self, query: str, graph_context: str, vector_context: str, user_id: str = None) -> str:
        """Generate response based on contexts (rule-based RAG)."""
        query_lower = query.lower()

        # Detect intent
        if any(kw in query_lower for kw in ["gợi ý", "recommend", "đề xuất", "nên mua", "tư vấn", "giới thiệu"]):
            return self._recommend_response(query, graph_context, vector_context, user_id)
        elif any(kw in query_lower for kw in ["so sánh", "compare", "khác nhau", "nào tốt hơn"]):
            return self._compare_response(query, vector_context)
        elif any(kw in query_lower for kw in ["giá", "price", "bao nhiêu", "rẻ", "đắt", "tầm"]):
            return self._price_response(query, vector_context)
        elif any(kw in query_lower for kw in ["tìm", "search", "kiếm", "có", "bán"]):
            return self._search_response(query, vector_context)
        else:
            return self._general_response(query, graph_context, vector_context)

    def _recommend_response(self, query, graph_ctx, vector_ctx, user_id):
        parts = ["Dựa trên phân tích hành vi và dữ liệu sản phẩm, tôi gợi ý cho bạn:\n"]
        if graph_ctx:
            parts.append(f"**Phân tích từ Knowledge Graph:**\n{graph_ctx}\n")
        if vector_ctx:
            parts.append(f"**{vector_ctx}**")
        if not graph_ctx and not vector_ctx:
            parts.append("Hiện tại chưa có đủ dữ liệu để gợi ý. Hãy xem thêm sản phẩm để hệ thống học hành vi của bạn!")
        return "\n".join(parts)

    def _compare_response(self, query, vector_ctx):
        parts = ["So sánh sản phẩm:\n"]
        if vector_ctx:
            parts.append(vector_ctx)
        parts.append("\nBạn có thể cho tôi biết cụ thể muốn so sánh sản phẩm nào?")
        return "\n".join(parts)

    def _price_response(self, query, vector_ctx):
        parts = ["Thông tin giá sản phẩm:\n"]
        if vector_ctx:
            parts.append(vector_ctx)
        return "\n".join(parts)

    def _search_response(self, query, vector_ctx):
        parts = ["Kết quả tìm kiếm:\n"]
        if vector_ctx:
            parts.append(vector_ctx)
        else:
            parts.append("Không tìm thấy sản phẩm phù hợp. Hãy thử từ khóa khác!")
        return "\n".join(parts)

    def _general_response(self, query, graph_ctx, vector_ctx):
        parts = ["Xin chào! Tôi là trợ lý AI của cửa hàng. Tôi có thể giúp bạn:\n"]
        parts.append("- **Gợi ý sản phẩm** phù hợp với sở thích của bạn")
        parts.append("- **Tìm kiếm** sản phẩm theo yêu cầu")
        parts.append("- **So sánh** các sản phẩm")
        parts.append("- **Tư vấn giá cả** và thông tin sản phẩm\n")
        if vector_ctx:
            parts.append(f"Một số sản phẩm bạn có thể quan tâm:\n{vector_ctx}")
        return "\n".join(parts)
