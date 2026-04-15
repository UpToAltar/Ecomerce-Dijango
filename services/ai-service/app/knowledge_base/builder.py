from __future__ import annotations
import asyncio
import logging
from typing import Any

import httpx
from langchain_core.documents import Document

from app.config import settings
from .faq_data import FAQ_DATA, CATEGORY_ADVICE

logger = logging.getLogger(__name__)


def _format_price(price: int | float) -> str:
    return f"{int(price):,}đ".replace(",", ".")


def _build_product_text(product: dict[str, Any]) -> str:
    specs = product.get("specifications") or {}
    spec_str = " | ".join(f"{k}: {v}" for k, v in specs.items()) if specs else ""

    price = int(float(product.get("price") or 0))
    price_str = _format_price(price)
    discount_str = ""
    compare_raw = product.get("compare_price")
    compare = int(float(compare_raw)) if compare_raw else 0
    if compare and compare > price:
        pct = round((compare - price) / compare * 100)
        discount_str = f" (Giảm {pct}% từ {_format_price(compare)})"

    parts = [
        f"Sản phẩm: {product['name']}",
        f"Thương hiệu: {product.get('brand', 'Không rõ')}",
        f"Danh mục: {product.get('category_name', '')}",
        f"Giá: {price_str}{discount_str}",
    ]
    if spec_str:
        parts.append(f"Thông số kỹ thuật: {spec_str}")
    if product.get("description"):
        parts.append(f"Mô tả: {product['description'][:300]}")
    if product.get("rating_avg"):
        parts.append(f"Đánh giá: {product['rating_avg']}/5 ({product.get('rating_count', 0)} lượt)")
    sold = int(product.get("sold_count") or 0)
    if sold > 50:
        parts.append(f"Đã bán: {sold} sản phẩm")

    return "\n".join(parts)


async def fetch_all_products(max_pages: int = 20) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=30) as client:
        page = 1
        while page <= max_pages:
            try:
                resp = await client.get(
                    f"{settings.PRODUCT_SERVICE_URL}/api/products/",
                    params={"limit": 100, "page": page},
                )
                if resp.status_code != 200:
                    break
                data = resp.json()
                results = data.get("results", data if isinstance(data, list) else [])
                if not results:
                    break
                products.extend(results)
                if not data.get("next"):
                    break
                page += 1
            except Exception as e:
                logger.warning(f"Error fetching products page {page}: {e}")
                break
    return products


async def fetch_products_with_retry(retries: int = 6, delay: float = 10.0) -> list[dict[str, Any]]:
    for attempt in range(retries):
        try:
            products = await fetch_all_products()
            if products:
                logger.info(f"Fetched {len(products)} products from product-service.")
                return products
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}")
        if attempt < retries - 1:
            await asyncio.sleep(delay)
    logger.error("Could not fetch products after all retries.")
    return []


def build_documents(products: list[dict[str, Any]]) -> list[Document]:
    documents: list[Document] = []

    for product in products:
        text = _build_product_text(product)
        doc = Document(
            page_content=text,
            metadata={
                "id": str(product["id"]),
                "name": product["name"],
                "brand": product.get("brand", ""),
                "price": int(float(product.get("price") or 0)),
                "compare_price": int(float(product.get("compare_price") or 0)),
                "category_slug": product.get("category_slug") or product.get("category", {}).get("slug", ""),
                "category_name": product.get("category_name") or product.get("category", {}).get("name", ""),
                "rating_avg": float(product.get("rating_avg") or 0),
                "rating_count": int(product.get("rating_count") or 0),
                "sold_count": int(product.get("sold_count") or 0),
                "slug": product.get("slug", ""),
                "image_url": product.get("image_url") or "",
                "specifications": str(product.get("specifications") or {}),
                "doc_type": "product",
            },
        )
        documents.append(doc)

    for faq in FAQ_DATA:
        text = f"Câu hỏi: {faq['question']}\nTrả lời: {faq['answer']}"
        doc = Document(
            page_content=text,
            metadata={
                "id": faq["id"],
                "question": faq["question"],
                "tags": " ".join(faq["tags"]),
                "category": faq["category"],
                "doc_type": "faq",
            },
        )
        documents.append(doc)

    for cat_slug, advice in CATEGORY_ADVICE.items():
        doc = Document(
            page_content=f"Tư vấn mua {cat_slug}:\n{advice}",
            metadata={
                "id": f"advice-{cat_slug}",
                "category_slug": cat_slug,
                "doc_type": "advice",
            },
        )
        documents.append(doc)

    logger.info(f"Built {len(documents)} documents ({len(products)} products, {len(FAQ_DATA)} FAQs, {len(CATEGORY_ADVICE)} advice)")
    return documents
