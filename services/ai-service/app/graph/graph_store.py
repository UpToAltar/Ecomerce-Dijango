"""
graph_store.py
Neo4j KnowledgeGraph — connection, build, and query helpers for ai-service.
"""
from __future__ import annotations
import logging
from typing import Any

from app.config import settings
from app.graph.graph_builder import build_graph

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """Thin wrapper around the Neo4j driver for the e-commerce knowledge graph."""

    def __init__(self) -> None:
        self._driver = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open connection to Neo4j. Returns True on success."""
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {settings.NEO4J_URI}")
            return True
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")
            self._driver = None
            return False

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None

    # ── State checks ──────────────────────────────────────────────────────────

    def is_connected(self) -> bool:
        return self._driver is not None

    def is_ready(self) -> bool:
        """True if there is at least one Product node in the graph."""
        if not self._driver:
            return False
        try:
            with self._driver.session() as session:
                result = session.run("MATCH (p:Product) RETURN count(p) AS cnt")
                record = result.single()
                return (record["cnt"] if record else 0) > 0
        except Exception:
            return False

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self, products: list[dict[str, Any]]) -> dict[str, int]:
        """
        (Re)build the entire knowledge graph from the products list.
        Delegates to graph_builder.build_graph().
        Returns stats dict.
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not connected.")
        return build_graph(self._driver, products)

    # ── Query helpers ─────────────────────────────────────────────────────────

    def get_related_products(
        self,
        product_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Return products related to `product_id` via SIMILAR_TO or SAME_CATEGORY
        (2-hop path through Category).
        """
        if not self._driver:
            return []
        try:
            with self._driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Product {id: $pid})-[:SIMILAR_TO]->(r:Product)
                    WHERE r.id <> $pid
                    RETURN r { .id, .name, .slug, .price, .brand,
                               .category_slug, .category_name,
                               .rating_avg, .sold_count, .image_url } AS prod,
                           1 AS hop
                    UNION
                    MATCH (p:Product {id: $pid})-[:IN_CATEGORY]->(c:Category)
                          <-[:IN_CATEGORY]-(r:Product)
                    WHERE r.id <> $pid
                    RETURN r { .id, .name, .slug, .price, .brand,
                               .category_slug, .category_name,
                               .rating_avg, .sold_count, .image_url } AS prod,
                           2 AS hop
                    ORDER BY hop, prod.rating_avg DESC
                    LIMIT $limit
                    """,
                    pid=product_id,
                    limit=limit,
                )
                return [dict(record["prod"]) for record in result]
        except Exception as e:
            logger.warning(f"get_related_products error: {e}")
            return []

    def get_category_products(
        self,
        category_slug: str,
        limit: int = 8,
        min_rating: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Return top products in a category sorted by rating."""
        if not self._driver:
            return []
        try:
            with self._driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Product)-[:IN_CATEGORY]->(c:Category {slug: $slug})
                    WHERE p.rating_avg >= $min_rating
                    RETURN p { .id, .name, .slug, .price, .brand,
                               .category_slug, .category_name,
                               .rating_avg, .sold_count, .image_url }
                    ORDER BY p.rating_avg DESC, p.sold_count DESC
                    LIMIT $limit
                    """,
                    slug=category_slug,
                    min_rating=min_rating,
                    limit=limit,
                )
                return [dict(record["p"]) for record in result]
        except Exception as e:
            logger.warning(f"get_category_products error: {e}")
            return []

    def get_brand_products(
        self,
        brand: str,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        """Return top products from a brand sorted by rating."""
        if not self._driver:
            return []
        try:
            with self._driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Product)-[:MADE_BY]->(b:Brand {name: $brand})
                    RETURN p { .id, .name, .slug, .price, .brand,
                               .category_slug, .category_name,
                               .rating_avg, .sold_count, .image_url }
                    ORDER BY p.rating_avg DESC, p.sold_count DESC
                    LIMIT $limit
                    """,
                    brand=brand,
                    limit=limit,
                )
                return [dict(record["p"]) for record in result]
        except Exception as e:
            logger.warning(f"get_brand_products error: {e}")
            return []

    def get_similar_products(
        self,
        product_id: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Return directly SIMILAR_TO linked products ordered by score."""
        if not self._driver:
            return []
        try:
            with self._driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Product {id: $pid})-[r:SIMILAR_TO]->(s:Product)
                    RETURN s { .id, .name, .slug, .price, .brand,
                               .category_slug, .category_name,
                               .rating_avg, .sold_count, .image_url },
                           r.score AS score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    pid=product_id,
                    limit=limit,
                )
                return [dict(record["s"]) for record in result]
        except Exception as e:
            logger.warning(f"get_similar_products error: {e}")
            return []

    def search_products_by_name(
        self,
        name_fragment: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Full text contains search on product name (case-insensitive)."""
        if not self._driver:
            return []
        try:
            with self._driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Product)
                    WHERE toLower(p.name) CONTAINS toLower($name)
                    RETURN p { .id, .name, .slug, .price, .brand,
                               .category_slug, .category_name,
                               .rating_avg, .sold_count, .image_url }
                    ORDER BY p.rating_avg DESC
                    LIMIT $limit
                    """,
                    name=name_fragment,
                    limit=limit,
                )
                return [dict(record["p"]) for record in result]
        except Exception as e:
            logger.warning(f"search_products_by_name error: {e}")
            return []

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, int]:
        """Return node and relationship counts."""
        if not self._driver:
            return {"products": 0, "categories": 0, "brands": 0, "similar_edges": 0, "total_nodes": 0}
        try:
            with self._driver.session() as session:
                counts = {}
                for label, key in [("Product", "products"), ("Category", "categories"), ("Brand", "brands")]:
                    r = session.run(f"MATCH (n:{label}) RETURN count(n) AS c")
                    rec = r.single()
                    counts[key] = rec["c"] if rec else 0
                r = session.run("MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) AS c")
                rec = r.single()
                counts["similar_edges"] = rec["c"] if rec else 0
                counts["total_nodes"] = counts["products"] + counts["categories"] + counts["brands"]
                return counts
        except Exception as e:
            logger.warning(f"stats error: {e}")
            return {"products": 0, "categories": 0, "brands": 0, "similar_edges": 0, "total_nodes": 0}

    # ── Graph exploration (for API /explore) ──────────────────────────────────

    def explore_node(
        self,
        node_type: str,
        node_id: str,
        depth: int = 1,
        limit: int = 30,
    ) -> dict[str, Any]:
        """
        Return a subgraph dict {nodes: [...], relationships: [...]} for the viewer.
        node_type: 'product' | 'category' | 'brand'
        node_id: product id / category slug / brand name
        """
        if not self._driver:
            return {"nodes": [], "relationships": []}
        try:
            with self._driver.session() as session:
                if node_type == "product":
                    query = """
                    MATCH path = (p:Product {id: $nid})-[r*1..1]-(related)
                    RETURN nodes(path) AS ns, relationships(path) AS rs
                    LIMIT $limit
                    """
                elif node_type == "category":
                    query = """
                    MATCH path = (c:Category {slug: $nid})<-[r:IN_CATEGORY]-(p:Product)
                    RETURN nodes(path) AS ns, relationships(path) AS rs
                    LIMIT $limit
                    """
                else:  # brand
                    query = """
                    MATCH path = (b:Brand {name: $nid})<-[r:MADE_BY]-(p:Product)
                    RETURN nodes(path) AS ns, relationships(path) AS rs
                    LIMIT $limit
                    """

                result = session.run(query, nid=node_id, limit=limit)
                nodes_seen: dict[str, dict] = {}
                rels: list[dict] = []

                for record in result:
                    for node in record["ns"]:
                        nid = str(node.element_id)
                        if nid not in nodes_seen:
                            nodes_seen[nid] = {
                                "id": nid,
                                "labels": list(node.labels),
                                "properties": dict(node),
                            }
                    for rel in record["rs"]:
                        rels.append({
                            "id": str(rel.element_id),
                            "type": rel.type,
                            "start": str(rel.start_node.element_id),
                            "end": str(rel.end_node.element_id),
                            "properties": dict(rel),
                        })

                return {"nodes": list(nodes_seen.values()), "relationships": rels}
        except Exception as e:
            logger.warning(f"explore_node error: {e}")
            return {"nodes": [], "relationships": []}
