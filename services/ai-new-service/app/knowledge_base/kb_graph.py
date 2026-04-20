"""Knowledge Base Graph builder using Neo4j."""
import logging
from collections import defaultdict
import httpx
from neo4j import GraphDatabase
from sqlalchemy import text

from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class KnowledgeBaseGraph:
    """Build and query a Knowledge Base Graph in Neo4j."""

    def __init__(self):
        self.driver = None
        self.ready = False

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False

    def close(self):
        if self.driver:
            self.driver.close()

    def clear_graph(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared Neo4j graph.")

    async def build_graph(self):
        """Build KB graph from behavior data + product info."""
        if not self.driver:
            if not self.connect():
                raise ConnectionError("Cannot connect to Neo4j")

        self.clear_graph()

        # Fetch products
        products = await self._fetch_products()
        categories = {}
        for p in products:
            cat = p.get("category", {})
            if cat and cat.get("id"):
                categories[cat["id"]] = cat

        # Load behaviors from DB
        behaviors = self._load_behaviors()

        with self.driver.session() as session:
            # Create constraints
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE")

            # Create Category nodes
            for cid, cat in categories.items():
                session.run(
                    "MERGE (c:Category {id: $id}) SET c.name = $name",
                    id=str(cid), name=cat.get("name", "Unknown"),
                )

            # Create Product nodes
            for p in products:
                session.run(
                    """MERGE (pr:Product {id: $id})
                       SET pr.name = $name, pr.price = $price,
                           pr.brand = $brand, pr.rating = $rating,
                           pr.description = $desc, pr.stock = $stock""",
                    id=str(p["id"]), name=p.get("name", ""),
                    price=float(p.get("price", 0)),
                    brand=p.get("brand", ""), rating=float(p.get("rating_avg", 0)),
                    desc=p.get("description", "")[:500],
                    stock=int(p.get("stock_quantity", 0)),
                )
                # Product -> Category
                cat = p.get("category", {})
                if cat and cat.get("id"):
                    session.run(
                        """MATCH (pr:Product {id: $pid}), (c:Category {id: $cid})
                           MERGE (pr)-[:BELONGS_TO]->(c)""",
                        pid=str(p["id"]), cid=str(cat["id"]),
                    )

            # Create User nodes and behavior edges
            user_actions = defaultdict(lambda: defaultdict(list))
            for uid, pid, action in behaviors:
                user_actions[uid][pid].append(action)

            for uid, product_actions in user_actions.items():
                session.run("MERGE (u:User {id: $id})", id=uid)
                for pid, actions in product_actions.items():
                    for action in set(actions):
                        count = actions.count(action)
                        rel_type = action.upper()
                        session.run(
                            f"""MATCH (u:User {{id: $uid}}), (p:Product {{id: $pid}})
                                MERGE (u)-[r:{rel_type}]->(p)
                                SET r.count = $count""",
                            uid=uid, pid=pid, count=count,
                        )

            # Create co-purchase / co-view edges between products
            session.run("""
                MATCH (u:User)-[:PURCHASE]->(p1:Product),
                      (u)-[:PURCHASE]->(p2:Product)
                WHERE p1.id < p2.id
                WITH p1, p2, COUNT(u) AS co_count
                WHERE co_count >= 2
                MERGE (p1)-[r:CO_PURCHASED]->(p2)
                SET r.count = co_count
            """)

            session.run("""
                MATCH (u:User)-[:VIEW]->(p1:Product),
                      (u)-[:VIEW]->(p2:Product)
                WHERE p1.id < p2.id
                WITH p1, p2, COUNT(u) AS co_count
                WHERE co_count >= 3
                MERGE (p1)-[r:CO_VIEWED]->(p2)
                SET r.count = co_count
            """)

        self.ready = True
        stats = self._get_stats()
        logger.info(f"KB Graph built: {stats}")
        return stats

    def _load_behaviors(self):
        db = SessionLocal()
        try:
            rows = db.execute(text("SELECT user_id, product_id, action FROM user_behavior_data")).fetchall()
            return [(r[0], r[1], r[2]) for r in rows]
        finally:
            db.close()

    async def _fetch_products(self):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(f"{settings.PRODUCT_SERVICE_URL}/api/products/?page_size=500")
                if resp.status_code == 200:
                    data = resp.json()
                    return data if isinstance(data, list) else data.get("results", [])
        except Exception as e:
            logger.warning(f"Cannot fetch products: {e}")
        return []

    def _get_stats(self):
        with self.driver.session() as session:
            users = session.run("MATCH (u:User) RETURN COUNT(u) AS c").single()["c"]
            products = session.run("MATCH (p:Product) RETURN COUNT(p) AS c").single()["c"]
            categories = session.run("MATCH (c:Category) RETURN COUNT(c) AS c").single()["c"]
            rels = session.run("MATCH ()-[r]->() RETURN COUNT(r) AS c").single()["c"]
        return {"users": users, "products": products, "categories": categories, "relationships": rels}

    def query_user_recommendations(self, user_id: str, limit: int = 10):
        """Recommend products for user using graph traversal."""
        if not self.driver or not self.ready:
            return []
        with self.driver.session() as session:
            # Products viewed/purchased by similar users (collaborative filtering via graph)
            result = session.run("""
                MATCH (u:User {id: $uid})-[:VIEW|PURCHASE|ADD_TO_CART]->(p:Product)
                      <-[:VIEW|PURCHASE|ADD_TO_CART]-(other:User)
                      -[:PURCHASE|ADD_TO_CART]->(rec:Product)
                WHERE NOT (u)-[:PURCHASE]->(rec) AND rec.id <> p.id
                WITH rec, COUNT(DISTINCT other) AS score
                ORDER BY score DESC
                LIMIT $limit
                RETURN rec.id AS id, rec.name AS name, rec.price AS price,
                       rec.brand AS brand, rec.rating AS rating, score
            """, uid=user_id, limit=limit)
            return [dict(r) for r in result]

    def query_similar_products(self, product_id: str, limit: int = 5):
        """Find similar products via co-purchase/co-view and same category."""
        if not self.driver or not self.ready:
            return []
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Product {id: $pid})
                OPTIONAL MATCH (p)-[:CO_PURCHASED|CO_VIEWED]-(similar:Product)
                WITH p, COLLECT(DISTINCT similar) AS co_products
                OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(cat_prod:Product)
                WHERE cat_prod.id <> p.id
                WITH co_products + COLLECT(DISTINCT cat_prod) AS all_similar
                UNWIND all_similar AS rec
                WITH DISTINCT rec
                RETURN rec.id AS id, rec.name AS name, rec.price AS price,
                       rec.brand AS brand, rec.rating AS rating
                LIMIT $limit
            """, pid=product_id, limit=limit)
            return [dict(r) for r in result]

    def get_user_profile(self, user_id: str):
        """Get user behavior summary from graph."""
        if not self.driver or not self.ready:
            return {}
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $uid})-[r]->(p:Product)
                WITH type(r) AS action, p.name AS product, p.id AS pid
                RETURN action, COLLECT(DISTINCT {name: product, id: pid})[..5] AS products, COUNT(*) AS count
                ORDER BY count DESC
            """, uid=user_id)
            return [dict(r) for r in result]

    def graph_context_for_rag(self, user_id: str = None, product_id: str = None):
        """Get context from graph for RAG system."""
        context_parts = []

        if user_id and self.driver and self.ready:
            profile = self.get_user_profile(user_id)
            if profile:
                context_parts.append(f"User {user_id} behavior profile:")
                for item in profile:
                    products = ", ".join([p["name"] for p in item["products"]])
                    context_parts.append(f"  - {item['action']}: {products} (total: {item['count']})")

            recs = self.query_user_recommendations(user_id, 5)
            if recs:
                context_parts.append(f"\nRecommended products for this user:")
                for r in recs:
                    context_parts.append(f"  - {r['name']} ({r['brand']}) - {r['price']}đ, rating: {r['rating']}")

        if product_id and self.driver and self.ready:
            similar = self.query_similar_products(product_id, 5)
            if similar:
                context_parts.append(f"\nSimilar products to {product_id}:")
                for s in similar:
                    context_parts.append(f"  - {s['name']} ({s['brand']}) - {s['price']}đ")

        return "\n".join(context_parts)
