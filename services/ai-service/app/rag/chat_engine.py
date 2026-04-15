from __future__ import annotations
import json
import logging
import re
from typing import Any

import redis.asyncio as aioredis

from app.config import settings
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


# ─── Intent detection ────────────────────────────────────────────────────────

_SEARCH_KW = re.compile(
    r"(tìm|mua|cần|muốn|tìm kiếm|có bán|bán không|cho tôi xem|hiển thị|show|search)", re.I
)
_COMPARE_KW = re.compile(
    r"(so sánh|tốt hơn|khác nhau|nên chọn|hay là|cái nào|loại nào|compare)", re.I
)
_RECOMMEND_KW = re.compile(
    r"(gợi ý|đề xuất|phù hợp|nên mua|tư vấn|recommend|suggest|phù hợp với|dành cho)", re.I
)
_FAQ_KW = re.compile(
    r"(chính sách|đổi trả|giao hàng|bảo hành|thanh toán|hoàn tiền|ship|liên hệ|hỗ trợ|account|đăng ký|voucher|mã giảm)", re.I
)
_PRICE_KW = re.compile(
    r"(giá|bao nhiêu tiền|bao nhiêu|price|cost|rẻ nhất|đắt nhất|tầm giá|ngân sách|budget|từ\s*\d|đến\s*\d)", re.I
)

_PRICE_RANGE = re.compile(
    r"(dưới|under|below|tầm|khoảng|around)\s*(\d+[\.,]?\d*)\s*(triệu|tr|k|nghìn|đồng|đ|vnd)?", re.I
)

_PRICE_RANGE_FULL = re.compile(
    r"từ\s*(\d+[\.,]?\d*)\s*(triệu|tr|k|nghìn)?\s*(?:đến|tới|~|-)\s*(\d+[\.,]?\d*)\s*(triệu|tr|k|nghìn)?",
    re.I,
)

_SORT_DESC_KW = re.compile(r"(đắt nhất|giá cao nhất|cao nhất|expensive|most expensive)", re.I)
_SORT_ASC_KW = re.compile(r"(rẻ nhất|giá rẻ nhất|thấp nhất|cheapest|giá thấp)", re.I)

_COMPARE_NAMES = re.compile(
    r"(?:so sánh\s+(?:sản phẩm\s+|giữa\s+)?)(.+?)\s+(?:và|with|vs\.?|hoặc)\s+(.+?)(?:\?|$)",
    re.I,
)

_CATEGORY_MAP = {
    "điện thoại": "dien-thoai",
    "iphone": "dien-thoai",
    "samsung": "dien-thoai",
    "xiaomi": "dien-thoai",
    "oppo": "dien-thoai",
    "phone": "dien-thoai",
    "smartphone": "dien-thoai",
    "laptop": "laptop",
    "macbook": "laptop",
    "máy tính": "laptop",
    "thời trang nam": "thoi-trang-nam",
    "áo nam": "thoi-trang-nam",
    "quần nam": "thoi-trang-nam",
    "giày nam": "thoi-trang-nam",
    "thời trang nữ": "thoi-trang-nu",
    "đầm": "thoi-trang-nu",
    "váy": "thoi-trang-nu",
    "túi xách": "thoi-trang-nu",
    "đồ gia dụng": "do-gia-dung",
    "gia dụng": "do-gia-dung",
    "nồi chiên": "do-gia-dung",
    "máy hút bụi": "do-gia-dung",
    "sách": "sach",
    "book": "sach",
    "tiểu thuyết": "sach",
    "thể thao": "the-thao",
    "sport": "the-thao",
    "giày chạy bộ": "the-thao",
    "yoga": "the-thao",
    "mỹ phẩm": "my-pham",
    "kem dưỡng": "my-pham",
    "serum": "my-pham",
    "son môi": "my-pham",
    "skincare": "my-pham",
    "makeup": "my-pham",
    "đồng hồ": "dong-ho",
    "smartwatch": "dong-ho",
    "apple watch": "dong-ho",
    "garmin": "dong-ho",
    "đồng hồ thông minh": "dong-ho",
    "tai nghe": "am-thanh",
    "airpods": "am-thanh",
    "loa bluetooth": "am-thanh",
    "headphone": "am-thanh",
    "earbuds": "am-thanh",
    "loa portable": "am-thanh",
    "âm thanh": "am-thanh",
    "sony headphone": "am-thanh",
}


def detect_intent(message: str) -> str:
    msg_lower = message.lower()
    if _FAQ_KW.search(msg_lower):
        return "faq"
    if _COMPARE_KW.search(msg_lower):
        return "compare"
    if _RECOMMEND_KW.search(msg_lower):
        return "recommend"
    if _PRICE_KW.search(msg_lower) or _PRICE_RANGE.search(msg_lower) or _PRICE_RANGE_FULL.search(msg_lower):
        return "price_query"
    if _SEARCH_KW.search(msg_lower):
        return "search"
    return "general"


def extract_category(message: str) -> str | None:
    msg_lower = message.lower()
    for keyword, slug in _CATEGORY_MAP.items():
        if keyword in msg_lower:
            return slug
    return None


def _parse_amount(value: str, unit: str) -> float:
    amount = float(value.replace(",", "."))
    u = unit.lower()
    if u in ("triệu", "tr"):
        return amount * 1_000_000
    if u in ("k", "nghìn"):
        return amount * 1_000
    return amount


def extract_max_price(message: str) -> float | None:
    match = _PRICE_RANGE.search(message.lower())
    if not match:
        return None
    return _parse_amount(match.group(2), match.group(3) or "")


def extract_price_range(message: str) -> tuple[float | None, float | None]:
    """Return (min_price, max_price). Both can be None."""
    m = _PRICE_RANGE_FULL.search(message.lower())
    if m:
        min_price = _parse_amount(m.group(1), m.group(2) or "")
        max_price = _parse_amount(m.group(3), m.group(4) or "")
        return min_price, max_price
    max_price = extract_max_price(message)
    return None, max_price


def extract_compare_products(message: str) -> list[str]:
    """Extract the two product names from a compare message."""
    m = _COMPARE_NAMES.search(message)
    if m:
        return [m.group(1).strip(), m.group(2).strip()]
    return []


def category_keywords(slug: str) -> list[str]:
    return [k for k, s in _CATEGORY_MAP.items() if s == slug]


def is_category_match(meta: dict[str, Any], category_slug: str) -> bool:
    meta_slug = str(meta.get("category_slug", "")).strip().lower()
    if meta_slug == category_slug:
        return True
    category_name = str(meta.get("category_name", "")).strip().lower()
    if not category_name:
        return False
    for kw in category_keywords(category_slug):
        if kw in category_name:
            return True
    return False


def _fmt_price(price: float) -> str:
    return f"{int(price):,}đ".replace(",", ".")


def _to_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v not in (None, "", "None", "null") else default
    except (ValueError, TypeError):
        return default


def _to_int(v: Any, default: int = 0) -> int:
    return int(_to_float(v, default))


def _product_card(meta: dict[str, Any], idx: int) -> str:
    name = meta.get("name", "Sản phẩm")
    brand = meta.get("brand", "")
    price = _to_float(meta.get("price", 0))
    compare = _to_float(meta.get("compare_price", 0))
    rating = _to_float(meta.get("rating_avg", 0))
    rating_count = _to_int(meta.get("rating_count", 0))
    sold = _to_int(meta.get("sold_count", 0))
    specs_raw = meta.get("specifications", "{}")
    cat_name = meta.get("category_name", "")

    discount_str = ""
    if compare and compare > price > 0:
        pct = round((compare - price) / compare * 100)
        discount_str = f" ~~{_fmt_price(compare)}~~ **(Giảm {pct}%)**"

    try:
        specs = eval(specs_raw) if isinstance(specs_raw, str) else specs_raw
        key_specs = list(specs.items())[:3]
        spec_line = " | ".join(f"{k}: {v}" for k, v in key_specs) if key_specs else ""
    except Exception:
        spec_line = ""

    lines = [f"**{idx}. {name}** ({brand})" if brand else f"**{idx}. {name}**"]
    lines.append(f"   💰 Giá: **{_fmt_price(price)}**{discount_str}")
    if spec_line:
        lines.append(f"   ⚡ {spec_line}")
    if rating:
        lines.append(f"   ⭐ {rating}/5 ({rating_count} đánh giá)" + (f" | Đã bán: {sold}" if sold > 10 else ""))
    if cat_name:
        lines.append(f"   📂 {cat_name}")
    return "\n".join(lines)


class ChatEngine:
    """RAG-based chat engine with conversation memory and product recommendations."""

    def __init__(self, vector_store: VectorStore, redis_url: str | None = None) -> None:
        self.vs = vector_store
        self._redis_url = redis_url or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(self._redis_url, decode_responses=True)
        return self._redis

    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        try:
            r = await self._get_redis()
            raw = await r.lrange(f"chat:{session_id}", 0, settings.CHAT_HISTORY_SIZE * 2 - 1)
            return [json.loads(m) for m in raw]
        except Exception:
            return []

    async def save_message(self, session_id: str, role: str, content: str) -> None:
        try:
            r = await self._get_redis()
            key = f"chat:{session_id}"
            await r.lpush(key, json.dumps({"role": role, "content": content}))
            await r.ltrim(key, 0, settings.CHAT_HISTORY_SIZE * 2 - 1)
            await r.expire(key, settings.CHAT_TTL_SECONDS)
        except Exception as e:
            logger.warning(f"Redis save_message failed: {e}")

    async def track_behavior(self, user_id: str, product_ids: list[str]) -> None:
        if not user_id or not product_ids:
            return
        try:
            r = await self._get_redis()
            key = f"behavior:{user_id}"
            for pid in product_ids:
                await r.lpush(key, pid)
            await r.ltrim(key, 0, 49)
            await r.expire(key, settings.BEHAVIOR_TTL_SECONDS)
        except Exception as e:
            logger.warning(f"Redis track_behavior failed: {e}")

    async def get_user_behavior(self, user_id: str) -> list[str]:
        try:
            r = await self._get_redis()
            return await r.lrange(f"behavior:{user_id}", 0, 49)
        except Exception:
            return []

    async def chat(
        self,
        message: str,
        session_id: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        intent = detect_intent(message)
        category_slug = extract_category(message)
        min_price, max_price = extract_price_range(message)
        history = await self.get_history(session_id)

        products_shown: list[dict] = []
        response_text = ""

        if not self.vs.is_ready():
            response_text = (
                "⚙️ Hệ thống đang khởi tạo cơ sở tri thức, vui lòng thử lại sau vài phút."
            )
        elif intent == "faq":
            response_text = await self._handle_faq(message)
        elif intent == "compare":
            response_text, products_shown = await self._handle_compare(message)
        elif intent == "recommend":
            response_text, products_shown = await self._handle_recommend(message, category_slug, max_price, user_id)
        elif intent == "price_query":
            response_text, products_shown = await self._handle_price_query(message, category_slug, min_price, max_price)
        elif intent == "search":
            response_text, products_shown = await self._handle_search(message, category_slug, max_price)
        else:
            response_text, products_shown = await self._handle_general(message, history)

        await self.save_message(session_id, "user", message)
        await self.save_message(session_id, "assistant", response_text)

        if user_id and products_shown:
            product_ids = [p["metadata"].get("id", "") for p in products_shown if p.get("metadata")]
            await self.track_behavior(user_id, [pid for pid in product_ids if pid])

        return {
            "message": response_text,
            "intent": intent,
            "products": [p["metadata"] for p in products_shown[:5]],
            "session_id": session_id,
        }

    async def _handle_search(
        self, message: str, category_slug: str | None, max_price: float | None
    ) -> tuple[str, list[dict]]:
        results = self.vs.search_products(
            message, n_results=5,
            category_slug=category_slug,
            max_price=max_price,
        )
        if not results:
            return (
                "😔 Xin lỗi, tôi không tìm thấy sản phẩm phù hợp với yêu cầu của bạn.\n"
                "Bạn có thể mô tả rõ hơn hoặc thay đổi bộ lọc giá không?",
                [],
            )
        lines = [f"🔍 Tôi tìm được **{len(results)}** sản phẩm phù hợp:\n"]
        for i, r in enumerate(results, 1):
            lines.append(_product_card(r["metadata"], i))
            lines.append("")
        lines.append("💬 Bạn có muốn tôi tư vấn thêm về sản phẩm nào không?")
        return "\n".join(lines), results

    async def _handle_price_query(
        self,
        message: str,
        category_slug: str | None,
        min_price: float | None,
        max_price: float | None,
    ) -> tuple[str, list[dict]]:
        sort_desc = bool(_SORT_DESC_KW.search(message))
        sort_asc = bool(_SORT_ASC_KW.search(message))
        fetch_n = 20 if (min_price or max_price) else 8
        results = self.vs.search_products(
            message, n_results=fetch_n,
            category_slug=category_slug,
            max_price=max_price,
            min_price=min_price,
        )

        if not results and category_slug:
            fallback_query = " ".join(category_keywords(category_slug)[:3]) or category_slug.replace("-", " ")
            raw = self.vs.search_products(
                fallback_query,
                n_results=60,
                max_price=max_price,
                min_price=min_price,
            )
            results = [r for r in raw if is_category_match(r["metadata"], category_slug)]

        if not results:
            raw = self.vs.search_products(
                "sản phẩm",
                n_results=80,
                max_price=max_price,
                min_price=min_price,
            )
            if category_slug:
                results = [r for r in raw if is_category_match(r["metadata"], category_slug)]
            else:
                results = raw

        if not results:
            range_hint = ""
            if min_price and max_price:
                range_hint = f" từ {_fmt_price(min_price)} đến {_fmt_price(max_price)}"
            elif max_price:
                range_hint = f" dưới {_fmt_price(max_price)}"
            return f"😔 Không tìm thấy sản phẩm phù hợp{range_hint}. Bạn muốn mở rộng tầm giá không?", []

        # Sort by price based on query intent
        if sort_desc:
            sorted_results = sorted(results, key=lambda x: _to_float(x["metadata"].get("price", 0)), reverse=True)
            header = "💰 **Sản phẩm có giá cao nhất:**\n"
        elif sort_asc:
            sorted_results = sorted(results, key=lambda x: _to_float(x["metadata"].get("price", 0)))
            header = "💰 **Sản phẩm có giá rẻ nhất:**\n"
        elif min_price and max_price:
            sorted_results = sorted(results, key=lambda x: _to_float(x["metadata"].get("price", 0)))
            header = f"💰 **Sản phẩm từ {_fmt_price(min_price)} đến {_fmt_price(max_price)}:**\n"
        elif max_price:
            sorted_results = sorted(results, key=lambda x: _to_float(x["metadata"].get("price", 0)))
            header = f"💰 **Sản phẩm dưới {_fmt_price(max_price)}:**\n"
        else:
            sorted_results = sorted(results, key=lambda x: _to_float(x["metadata"].get("price", 0)))
            header = "💰 **Sản phẩm theo giá:**\n"

        top = sorted_results[:6]
        lines = [header]
        for i, r in enumerate(top, 1):
            lines.append(_product_card(r["metadata"], i))
            lines.append("")
        lines.append("🎯 Bạn có muốn tôi so sánh hoặc tư vấn thêm về sản phẩm nào không?")
        return "\n".join(lines), top

    async def _handle_compare(self, message: str) -> tuple[str, list[dict]]:
        # Try to extract explicit product names from message
        named = extract_compare_products(message)
        results: list[dict] = []

        if len(named) >= 2:
            # Search for each product individually to get the best match
            seen_ids: set[str] = set()
            for name in named:
                hits = self.vs.search_products(name, n_results=2)
                for hit in hits:
                    pid = str(hit["metadata"].get("id", ""))
                    if pid not in seen_ids:
                        results.append(hit)
                        seen_ids.add(pid)
                        break
            # If we only got 1 result, pad with generic search
            if len(results) < 2:
                extra = self.vs.search_products(message, n_results=4)
                for r in extra:
                    pid = str(r["metadata"].get("id", ""))
                    if pid not in seen_ids:
                        results.append(r)
                        seen_ids.add(pid)
                    if len(results) >= 2:
                        break
        else:
            results = self.vs.search_products(message, n_results=3)

        if len(results) < 2:
            return (
                "Để so sánh sản phẩm, vui lòng cho tôi biết tên cụ thể hai sản phẩm bạn muốn so sánh.",
                results,
            )

        # Only compare the first two
        pair = results[:2]
        lines = ["⚖️ **So sánh sản phẩm:**\n"]
        for i, r in enumerate(pair, 1):
            lines.append(_product_card(r["metadata"], i))
            lines.append("")

        meta_a, meta_b = pair[0]["metadata"], pair[1]["metadata"]
        price_a = _to_float(meta_a.get("price", 0))
        price_b = _to_float(meta_b.get("price", 0))
        rating_a = _to_float(meta_a.get("rating_avg", 0))
        rating_b = _to_float(meta_b.get("rating_avg", 0))
        sold_a = _to_int(meta_a.get("sold_count", 0))
        sold_b = _to_int(meta_b.get("sold_count", 0))
        name_a = meta_a.get("name", "Sản phẩm 1")
        name_b = meta_b.get("name", "Sản phẩm 2")

        cheaper = name_a if price_a <= price_b else name_b
        better_rating = name_a if rating_a >= rating_b else name_b
        more_popular = name_a if sold_a >= sold_b else name_b

        diff_pct = abs(price_a - price_b) / max(price_a, price_b) * 100 if max(price_a, price_b) > 0 else 0
        lines.append(
            f"💡 **Tổng kết:**\n"
            f"- 💰 **Giá tốt hơn:** {cheaper}"
            + (f" (rẻ hơn {diff_pct:.0f}%)" if diff_pct > 0 else "")
            + f"\n- ⭐ **Đánh giá cao hơn:** {better_rating}"
            f"\n- 🔥 **Bán chạy hơn:** {more_popular}"
        )
        lines.append("\nBạn ưu tiên giá hay chất lượng / độ phổ biến?")
        return "\n".join(lines), pair

    async def _handle_recommend(
        self,
        message: str,
        category_slug: str | None,
        max_price: float | None,
        user_id: str | None,
    ) -> tuple[str, list[dict]]:
        user_context = ""
        if user_id:
            behavior = await self.get_user_behavior(user_id)
            if behavior:
                user_context = f"Khách hàng đã xem sản phẩm: {', '.join(behavior[:5])}"

        query = f"{message} {user_context}".strip()
        results = self.vs.search_products(
            query, n_results=5,
            category_slug=category_slug,
            max_price=max_price,
        )

        sorted_results = sorted(
            results,
            key=lambda x: (
                _to_float(x["metadata"].get("rating_avg", 0)) * 0.4
                + _to_float(x["metadata"].get("sold_count", 0)) / 500 * 0.6
            ),
            reverse=True,
        )

        lines = ["🌟 **Sản phẩm được đề xuất cho bạn:**\n"]
        for i, r in enumerate(sorted_results, 1):
            lines.append(_product_card(r["metadata"], i))
            lines.append("")

        if category_slug:
            from app.knowledge_base.faq_data import CATEGORY_ADVICE
            advice = CATEGORY_ADVICE.get(category_slug)
            if advice:
                lines.append(f"\n---\n{advice}")

        lines.append("\n💬 Tôi có thể tư vấn thêm nếu bạn cho biết thêm về ngân sách và nhu cầu sử dụng!")
        return "\n".join(lines), sorted_results

    async def _handle_faq(self, message: str) -> str:
        results = self.vs.search_faq(message, n_results=2)
        if results:
            answers = []
            for r in results:
                if r["score"] > 0.3:
                    answers.append(r["text"].split("Trả lời: ", 1)[-1])
            if answers:
                return "\n\n---\n".join(answers)
        return (
            "Xin lỗi, tôi chưa tìm thấy thông tin về vấn đề này.\n"
            "Bạn có thể liên hệ hotline **1800-XXXX** hoặc email **support@shop.vn** để được hỗ trợ trực tiếp."
        )

    async def _handle_general(
        self, message: str, history: list[dict[str, str]]
    ) -> tuple[str, list[dict]]:
        context_parts = []
        if history:
            recent = history[:4]
            for h in reversed(recent):
                role = "Khách" if h["role"] == "user" else "Tư vấn viên"
                context_parts.append(f"{role}: {h['content'][:100]}")

        results = self.vs.search(message, n_results=4)

        product_results = [r for r in results if r["metadata"].get("doc_type") == "product"]
        faq_results = [r for r in results if r["metadata"].get("doc_type") in ("faq", "advice")]

        if product_results:
            lines = ["Xin chào! Dựa trên yêu cầu của bạn, đây là một số thông tin có thể giúp ích:\n"]
            for i, r in enumerate(product_results[:3], 1):
                lines.append(_product_card(r["metadata"], i))
                lines.append("")
            lines.append("Bạn có muốn tôi tìm kiếm cụ thể hơn không?")
            return "\n".join(lines), product_results
        elif faq_results:
            answer = faq_results[0]["text"].split("Trả lời: ", 1)[-1]
            return answer, []
        else:
            return (
                "Xin chào! Tôi là trợ lý tư vấn mua sắm AI. Tôi có thể giúp bạn:\n"
                "- 🔍 Tìm kiếm sản phẩm theo nhu cầu\n"
                "- 💰 Gợi ý sản phẩm theo tầm giá\n"
                "- ⚖️ So sánh các sản phẩm\n"
                "- 📦 Giải đáp chính sách mua hàng\n\n"
                "Bạn đang cần tìm sản phẩm gì hôm nay?",
                [],
            )
