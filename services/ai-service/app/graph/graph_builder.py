"""
graph_builder.py
Build Neo4j graph from product list.

Nodes:
  (:Product {id, name, slug, price, brand, category_slug, rating_avg, sold_count, image_url})
  (:Category {slug, name})
  (:Brand {name})

Relationships:
  (:Product)-[:IN_CATEGORY]->(:Category)
  (:Product)-[:MADE_BY]->(:Brand)
  (:Product)-[:SIMILAR_TO {score}]->(:Product)   # same category, similar price/rating
"""
from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── tunables ─────────────────────────────────────────────────────────────────
MAX_SIMILAR_PER_PRODUCT = 5   # max SIMILAR_TO edges per product
PRICE_DIFF_PCT_THRESHOLD = 0.35   # 35% price difference allowed for similarity
RATING_DIFF_THRESHOLD = 1.0       # max rating_avg difference


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v not in (None, "", "None", "null") else default
    except (TypeError, ValueError):
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    return int(_safe_float(v, default))


def _similarity_score(a: dict, b: dict) -> float:
    """Return a 0-1 score between two products (same category assumed)."""
    pa, pb = _safe_float(a.get("price")), _safe_float(b.get("price"))
    ra, rb = _safe_float(a.get("rating_avg")), _safe_float(b.get("rating_avg"))
    max_price = max(pa, pb)
    price_score = 1.0 - abs(pa - pb) / max_price if max_price > 0 else 0.5
    rating_score = 1.0 - abs(ra - rb) / 5.0
    return round(price_score * 0.6 + rating_score * 0.4, 4)


def build_graph(driver, products: list[dict[str, Any]]) -> dict[str, int]:
    """
    Rebuild the entire knowledge graph from scratch.
    Returns stat dict: {products, categories, brands, similar_edges}.
    """
    logger.info(f"Building Neo4j graph with {len(products)} products...")

    with driver.session() as session:
        # ── Clear old data ────────────────────────────────────────────────────
        session.run("MATCH (n) DETACH DELETE n")
        logger.info("Cleared existing graph data.")

        # ── Constraint / index (idempotent) ───────────────────────────────────
        _create_constraints(session)

        # ── Nodes ─────────────────────────────────────────────────────────────
        categories: dict[str, str] = {}   # slug → name
        brands: set[str] = set()

        for p in products:
            cat_slug = str(p.get("category_slug") or p.get("category", {}).get("slug", "") or "")
            cat_name = str(p.get("category_name") or p.get("category", {}).get("name", "") or cat_slug)
            brand = str(p.get("brand") or "").strip()

            if cat_slug:
                categories[cat_slug] = cat_name
            if brand:
                brands.add(brand)

        # Insert Categories
        for slug, name in categories.items():
            session.run(
                "MERGE (c:Category {slug: $slug}) SET c.name = $name",
                slug=slug, name=name,
            )

        # Insert Brands
        for brand in brands:
            session.run("MERGE (b:Brand {name: $name})", name=brand)

        # Insert Products + relationships
        for p in products:
            pid = str(p.get("id", ""))
            cat_slug = str(p.get("category_slug") or p.get("category", {}).get("slug", "") or "")
            brand = str(p.get("brand") or "").strip()

            session.run(
                """
                MERGE (p:Product {id: $id})
                SET p.name        = $name,
                    p.slug        = $slug,
                    p.price       = $price,
                    p.compare_price = $compare_price,
                    p.brand       = $brand,
                    p.category_slug = $cat_slug,
                    p.category_name = $cat_name,
                    p.rating_avg  = $rating_avg,
                    p.rating_count = $rating_count,
                    p.sold_count  = $sold_count,
                    p.image_url   = $image_url
                """,
                id=pid,
                name=str(p.get("name", "")),
                slug=str(p.get("slug", "")),
                price=_safe_float(p.get("price")),
                compare_price=_safe_float(p.get("compare_price")),
                brand=brand,
                cat_slug=cat_slug,
                cat_name=categories.get(cat_slug, cat_slug),
                rating_avg=_safe_float(p.get("rating_avg")),
                rating_count=_safe_int(p.get("rating_count")),
                sold_count=_safe_int(p.get("sold_count")),
                image_url=str(p.get("image_url") or ""),
            )
            if cat_slug:
                session.run(
                    """
                    MATCH (p:Product {id: $pid}), (c:Category {slug: $slug})
                    MERGE (p)-[:IN_CATEGORY]->(c)
                    """,
                    pid=pid, slug=cat_slug,
                )
            if brand:
                session.run(
                    """
                    MATCH (p:Product {id: $pid}), (b:Brand {name: $brand})
                    MERGE (p)-[:MADE_BY]->(b)
                    """,
                    pid=pid, brand=brand,
                )

        logger.info(f"Inserted {len(products)} product nodes, {len(categories)} categories, {len(brands)} brands.")

        # ── SIMILAR_TO edges ──────────────────────────────────────────────────
        similar_count = _build_similar_edges(session, products)
        logger.info(f"Created {similar_count} SIMILAR_TO edges.")

    return {
        "products": len(products),
        "categories": len(categories),
        "brands": len(brands),
        "similar_edges": similar_count,
    }


def _create_constraints(session) -> None:
    """Create constraints/indexes if they don't exist yet."""
    for stmt in [
        "CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT category_slug IF NOT EXISTS FOR (c:Category) REQUIRE c.slug IS UNIQUE",
        "CREATE CONSTRAINT brand_name IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE",
    ]:
        try:
            session.run(stmt)
        except Exception:
            pass  # constraint may already exist


def _build_similar_edges(session, products: list[dict]) -> int:
    """Create SIMILAR_TO edges between products in the same category."""
    # Group by category
    by_cat: dict[str, list[dict]] = {}
    for p in products:
        slug = str(p.get("category_slug") or "")
        if slug:
            by_cat.setdefault(slug, []).append(p)

    total = 0
    for cat_slug, cat_products in by_cat.items():
        if len(cat_products) < 2:
            continue

        sorted_by_price = sorted(cat_products, key=lambda x: _safe_float(x.get("price")))

        for i, prod_a in enumerate(sorted_by_price):
            pa = _safe_float(prod_a.get("price"))
            ra = _safe_float(prod_a.get("rating_avg"))
            edges_added = 0

            for prod_b in sorted_by_price[i + 1:]:
                if edges_added >= MAX_SIMILAR_PER_PRODUCT:
                    break

                pb = _safe_float(prod_b.get("price"))
                rb = _safe_float(prod_b.get("rating_avg"))
                max_p = max(pa, pb)

                if max_p > 0 and abs(pa - pb) / max_p > PRICE_DIFF_PCT_THRESHOLD:
                    break  # list is price-sorted, no need to check further

                if abs(ra - rb) > RATING_DIFF_THRESHOLD:
                    continue

                score = _similarity_score(prod_a, prod_b)
                session.run(
                    """
                    MATCH (a:Product {id: $aid}), (b:Product {id: $bid})
                    MERGE (a)-[:SIMILAR_TO {score: $score}]->(b)
                    MERGE (b)-[:SIMILAR_TO {score: $score}]->(a)
                    """,
                    aid=str(prod_a["id"]),
                    bid=str(prod_b["id"]),
                    score=score,
                )
                edges_added += 1
                total += 2  # bidirectional

    return total
