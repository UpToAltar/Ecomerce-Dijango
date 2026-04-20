"""
Seed 500 REAL users into auth-service DB + generate REALISTIC behavior data
using ONLY real product_ids from product-service DB.
"""
import random
import logging
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import UserBehaviorData, SessionLocal
import httpx

logger = logging.getLogger(__name__)

# 8 behavior types
ACTIONS = ["view", "click", "add_to_cart", "purchase", "search", "wishlist", "remove_from_cart", "review"]

# Vietnamese first/last names for realistic users
FIRST_NAMES = [
    "An", "Bình", "Cường", "Dũng", "Đức", "Giang", "Hải", "Hùng", "Khoa", "Lâm",
    "Minh", "Nam", "Phúc", "Quân", "Sơn", "Thành", "Tuấn", "Vinh", "Xuân", "Yến",
    "Anh", "Bảo", "Chi", "Diệu", "Hà", "Hương", "Lan", "Linh", "Mai", "Ngọc",
    "Phương", "Quỳnh", "Thảo", "Trang", "Uyên", "Vân", "Hoa", "Thanh", "Trung", "Long",
    "Đạt", "Tùng", "Hiếu", "Nhân", "Kiên", "Trí", "Phát", "Tâm", "Hoàng", "Dương",
]
LAST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng",
    "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đào", "Đinh", "Lương", "Tạ",
]

# ────────────────────────────────────────────────
# 1. SEED 500 USERS vào auth-service
# ────────────────────────────────────────────────

async def seed_500_users() -> list:
    """
    Tạo 500 user THẬT qua auth-service /api/auth/register/ endpoint.
    Trả về danh sách user_id (UUID) đã tạo.
    """
    from app.config import settings

    # Fetch existing users first
    existing_users = await _fetch_existing_users()
    if len(existing_users) >= 500:
        logger.info(f"Already have {len(existing_users)} users in auth DB. Skipping seed.")
        return existing_users[:500]

    needed = 500 - len(existing_users)
    logger.info(f"Found {len(existing_users)} existing users. Need to create {needed} more.")

    created_ids = list(existing_users)
    async with httpx.AsyncClient(timeout=30) as client:
        for i in range(needed):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            idx = len(existing_users) + i + 1
            email = f"user{idx}_{random.randint(100,999)}@shop.com"
            phone = f"09{random.randint(10000000, 99999999)}"

            payload = {
                "email": email,
                "password": "User@123456",
                "password_confirm": "User@123456",
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
            }

            try:
                resp = await client.post(
                    f"{settings.AUTH_SERVICE_URL}/api/auth/register/",
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    user_data = data.get("user", data)
                    uid = str(user_data.get("id", ""))
                    if uid:
                        created_ids.append(uid)
                elif resp.status_code == 400:
                    # email already exists, skip
                    pass
                else:
                    logger.debug(f"Register user {idx} failed: {resp.status_code} {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"Failed to create user {idx}: {e}")

            # Log progress
            if (i + 1) % 50 == 0:
                logger.info(f"  Created {i+1}/{needed} users...")

    logger.info(f"Total users available: {len(created_ids)}")
    return created_ids[:500]


async def _fetch_existing_users() -> list:
    """Fetch all existing user IDs from auth-service."""
    from app.config import settings
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{settings.AUTH_SERVICE_URL}/api/auth/users/")
            if resp.status_code == 200:
                data = resp.json()
                users = data if isinstance(data, list) else data.get("results", data.get("users", []))
                return [str(u["id"]) for u in users if u.get("id")]
            # If 403 (admin only), try fetching via pagination
            # Some setups may return paginated results
            if resp.status_code == 403:
                logger.info("Cannot list users (admin only). Will create from scratch.")
    except Exception as e:
        logger.warning(f"Cannot fetch users: {e}")
    return []


# ────────────────────────────────────────────────
# 2. FETCH real product IDs from product-service
# ────────────────────────────────────────────────

async def fetch_all_real_products() -> list:
    """
    Fetch ALL real products from product-service.
    Returns list of dicts: [{id, name, category_name, price}, ...]
    """
    from app.config import settings
    all_products = []
    page = 1

    async with httpx.AsyncClient(timeout=15) as client:
        while True:
            try:
                resp = await client.get(
                    f"{settings.PRODUCT_SERVICE_URL}/api/products/",
                    params={"page": page, "page_size": 100}
                )
                if resp.status_code != 200:
                    break
                data = resp.json()
                results = data.get("results", data if isinstance(data, list) else [])
                if not results:
                    break
                for p in results:
                    all_products.append({
                        "id": str(p["id"]),
                        "name": p.get("name", ""),
                        "category": p.get("category_name", p.get("category", {}).get("name", "") if isinstance(p.get("category"), dict) else ""),
                        "price": float(p.get("price", 0)),
                    })
                # Check for next page
                if not data.get("next"):
                    break
                page += 1
            except Exception as e:
                logger.warning(f"Fetch products page {page} failed: {e}")
                break

    logger.info(f"Fetched {len(all_products)} REAL products from product-service.")
    return all_products


# ────────────────────────────────────────────────
# 3. GENERATE REALISTIC behavior with clear PATTERNS
# ────────────────────────────────────────────────

def _build_realistic_behaviors(user_ids: list, products: list) -> list:
    """
    Generate behavior data with CLEAR LEARNABLE PATTERNS:
    - Funnel: view → click → add_to_cart → purchase
    - Category affinity: users prefer products in 1-2 categories
    - Time-based: recent actions more likely to lead to purchase
    """
    if not products:
        raise ValueError("No real products available! product-service must have data.")

    product_ids = [p["id"] for p in products]

    # Group products by category
    cat_products = {}
    for p in products:
        cat = p.get("category", "unknown") or "unknown"
        cat_products.setdefault(cat, []).append(p["id"])
    categories = list(cat_products.keys())

    now = datetime.utcnow()
    records = []

    # Define user behavior profiles (patterns the model CAN learn)
    PROFILES = [
        # Profile A: "Browser" — mostly views and clicks, rarely buys (40%)
        {"funnel_prob": 0.1, "actions_dist": [40, 30, 10, 2, 10, 5, 2, 1], "events": (10, 25)},
        # Profile B: "Active Shopper" — full funnel view→click→cart→purchase (25%)
        {"funnel_prob": 0.7, "actions_dist": [20, 20, 25, 15, 5, 5, 5, 5], "events": (15, 35)},
        # Profile C: "Researcher" — searches a lot, compares, sometimes buys (20%)
        {"funnel_prob": 0.3, "actions_dist": [15, 15, 10, 5, 35, 10, 5, 5], "events": (12, 30)},
        # Profile D: "Impulse Buyer" — quick view→purchase, reviews often (15%)
        {"funnel_prob": 0.5, "actions_dist": [25, 10, 15, 20, 5, 5, 5, 15], "events": (8, 20)},
    ]
    PROFILE_WEIGHTS = [40, 25, 20, 15]

    for user_id in user_ids:
        profile = random.choices(PROFILES, weights=PROFILE_WEIGHTS, k=1)[0]

        # User prefers 1-2 categories
        preferred_cats = random.sample(categories, min(random.randint(1, 2), len(categories)))
        preferred_pids = []
        for cat in preferred_cats:
            preferred_pids.extend(cat_products[cat])
        if not preferred_pids:
            preferred_pids = product_ids

        # Pick 3-8 favorite products within preferred categories
        fav_products = random.sample(preferred_pids, min(random.randint(3, 8), len(preferred_pids)))

        num_events = random.randint(*profile["events"])

        # Decide if this user does a "funnel" sequence
        if random.random() < profile["funnel_prob"]:
            # Generate funnel: view → click → add_to_cart → purchase for 1-3 products
            num_funnels = random.randint(1, min(3, len(fav_products)))
            funnel_products = random.sample(fav_products, num_funnels)
            base_time = now - timedelta(days=random.randint(1, 60))

            for fp in funnel_products:
                # Full funnel with time gaps
                funnel_actions = ["view", "view", "click", "click", "add_to_cart", "purchase"]
                # Sometimes partial funnel
                if random.random() < 0.3:
                    funnel_actions = ["view", "click", "add_to_cart"]  # abandoned cart
                elif random.random() < 0.2:
                    funnel_actions = ["view", "click", "view"]  # just browsing

                for j, action in enumerate(funnel_actions):
                    ts = base_time + timedelta(hours=j * random.randint(1, 12), minutes=random.randint(0, 59))
                    records.append(UserBehaviorData(
                        user_id=user_id, product_id=fp,
                        action=action, timestamp=ts,
                    ))
                base_time += timedelta(days=random.randint(1, 7))

            # Remaining events: random but consistent with profile
            remaining = max(0, num_events - len(funnel_products) * 4)
        else:
            remaining = num_events

        # Random events matching profile distribution
        for _ in range(remaining):
            pid = random.choice(fav_products) if random.random() < 0.75 else random.choice(product_ids)
            action = random.choices(ACTIONS, weights=profile["actions_dist"], k=1)[0]
            ts = now - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            records.append(UserBehaviorData(
                user_id=user_id, product_id=pid,
                action=action, timestamp=ts,
            ))

        # Post-purchase review pattern
        purchased = [r.product_id for r in records if r.user_id == user_id and r.action == "purchase"]
        for pp in purchased:
            if random.random() < 0.4:  # 40% chance to review after purchase
                ts = now - timedelta(days=random.randint(0, 14))
                records.append(UserBehaviorData(
                    user_id=user_id, product_id=pp,
                    action="review", timestamp=ts,
                ))

    return records


# ────────────────────────────────────────────────
# MAIN: generate_behavior_data
# ────────────────────────────────────────────────

async def generate_behavior_data():
    """
    Main entry: seed 500 users + generate realistic behavior data
    with ONLY real product_ids.
    """
    # Step 1: Seed 500 users into auth DB
    logger.info("Step 1: Seeding 500 users into auth-service...")
    user_ids = await seed_500_users()
    if not user_ids:
        raise RuntimeError("Failed to create/fetch any users from auth-service!")
    logger.info(f"  → Got {len(user_ids)} user IDs")

    # Step 2: Fetch ALL real products
    logger.info("Step 2: Fetching real products from product-service...")
    products = await fetch_all_real_products()
    if not products:
        raise RuntimeError("No products found in product-service! Seed products first.")
    logger.info(f"  → Got {len(products)} real products")

    # Step 3: Check existing data
    db = SessionLocal()
    try:
        count = db.execute(text("SELECT COUNT(*) FROM user_behavior_data")).scalar()
        if count and count > 1000:
            logger.info(f"Behavior data already exists ({count} records). Skipping generation.")
            return count

        # Step 4: Generate realistic behaviors
        logger.info("Step 3: Generating realistic behavior data...")
        records = _build_realistic_behaviors(user_ids, products)

        # Step 5: Batch insert
        db.bulk_save_objects(records)
        db.commit()
        total = len(records)
        logger.info(f"  → Generated {total} behavior records for {len(user_ids)} users using {len(products)} real products.")
        return total

    except Exception as e:
        db.rollback()
        logger.error(f"Error generating behavior data: {e}")
        raise
    finally:
        db.close()
