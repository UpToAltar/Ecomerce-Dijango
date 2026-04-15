import random
import uuid
from django.core.management.base import BaseCommand
from analytics.models import UserProductView, UserSearchLog, UserClickEvent
from domain.models import Product, Category


SEARCH_QUERIES = {
    'dien-thoai': [
        'điện thoại', 'iphone', 'samsung galaxy', 'xiaomi', 'smartphone mới nhất',
        'điện thoại giá rẻ', 'điện thoại chụp ảnh đẹp', 'màn hình lớn', 'pin trâu', 'flagship 2024',
    ],
    'laptop': [
        'laptop', 'macbook', 'laptop gaming', 'laptop văn phòng', 'máy tính xách tay nhẹ',
        'laptop sinh viên', 'laptop core i7', 'laptop AMD ryzen', 'laptop OLED', 'laptop dưới 20 triệu',
    ],
    'thoi-trang-nam': [
        'áo polo nam', 'quần jean nam', 'giày sneaker nam', 'áo thun oversize', 'thời trang nam 2024',
        'áo khoác nam', 'quần kaki nam', 'giày da nam', 'outfit nam công sở',
    ],
    'thoi-trang-nu': [
        'đầm dự tiệc', 'chân váy midi', 'túi xách nữ', 'giày cao gót', 'thời trang nữ hàn quốc',
        'áo blouse nữ', 'quần jean nữ ống rộng', 'đồ mặc ở nhà', 'set đồ nữ',
    ],
    'do-gia-dung': [
        'nồi chiên không dầu', 'máy hút bụi robot', 'đồ gia dụng thông minh', 'máy pha cà phê',
        'lò vi sóng', 'máy lọc không khí', 'nồi cơm điện cao cấp', 'máy xay sinh tố',
    ],
    'sach': [
        'sách kỹ năng sống', 'sách lập trình python', 'sách tiếng anh', 'sách tài chính cá nhân',
        'tiểu thuyết hay', 'sách self-help', 'sách kinh doanh', 'sách khoa học', 'sách thiếu nhi',
    ],
    'the-thao': [
        'dụng cụ tập gym', 'giày chạy bộ', 'vợt cầu lông', 'thảm yoga', 'tạ tay',
        'áo thể thao', 'giày đá bóng', 'xe đạp thể thao', 'bóng rổ', 'đồ bơi',
    ],
    'my-pham': [
        'kem chống nắng spf50', 'serum vitamin c', 'nước tẩy trang', 'son môi lì',
        'skincare set dưỡng da', 'kem dưỡng ẩm', 'mặt nạ ngủ', 'tẩy tế bào chết',
        'phấn nền cushion', 'nước hoa nữ', 'mascara chống thấm nước',
    ],
    'dong-ho': [
        'đồng hồ thông minh', 'smartwatch', 'apple watch', 'samsung watch', 'đồng hồ thể thao',
        'đồng hồ Garmin chạy bộ', 'đồng hồ pin mặt trời', 'đồng hồ tự động', 'đồng hồ nữ đẹp',
        'đồng hồ theo dõi sức khỏe', 'đồng hồ chống nước',
    ],
    'am-thanh': [
        'tai nghe chống ồn', 'airpods pro', 'tai nghe bluetooth', 'loa bluetooth di động',
        'tai nghe gaming', 'loa marshall', 'loa jbl', 'sony headphone', 'earbuds tws',
        'tai nghe không dây chất lượng cao', 'loa xách tay chống nước',
    ],
}

# 14 user profiles with richer diversity
USER_PROFILES = {
    'tech_enthusiast': {
        'categories': {'dien-thoai': 0.4, 'laptop': 0.3, 'am-thanh': 0.2, 'dong-ho': 0.1},
        'count': 70,
        'avg_sessions': 5,
    },
    'gadget_lover': {
        'categories': {'dong-ho': 0.35, 'am-thanh': 0.35, 'dien-thoai': 0.2, 'do-gia-dung': 0.1},
        'count': 60,
        'avg_sessions': 4,
    },
    'fashion_female': {
        'categories': {'thoi-trang-nu': 0.4, 'my-pham': 0.35, 'dong-ho': 0.15, 'sach': 0.1},
        'count': 80,
        'avg_sessions': 5,
    },
    'fashion_male': {
        'categories': {'thoi-trang-nam': 0.4, 'the-thao': 0.25, 'dong-ho': 0.2, 'sach': 0.15},
        'count': 70,
        'avg_sessions': 4,
    },
    'audiophile': {
        'categories': {'am-thanh': 0.55, 'dien-thoai': 0.2, 'laptop': 0.15, 'sach': 0.1},
        'count': 50,
        'avg_sessions': 4,
    },
    'sport_fitness': {
        'categories': {'the-thao': 0.4, 'dong-ho': 0.25, 'thoi-trang-nam': 0.2, 'do-gia-dung': 0.15},
        'count': 60,
        'avg_sessions': 4,
    },
    'home_chef': {
        'categories': {'do-gia-dung': 0.5, 'sach': 0.2, 'the-thao': 0.15, 'my-pham': 0.15},
        'count': 50,
        'avg_sessions': 3,
    },
    'reader': {
        'categories': {'sach': 0.55, 'do-gia-dung': 0.2, 'my-pham': 0.15, 'am-thanh': 0.1},
        'count': 50,
        'avg_sessions': 3,
    },
    'beauty_lover': {
        'categories': {'my-pham': 0.5, 'thoi-trang-nu': 0.3, 'dong-ho': 0.1, 'sach': 0.1},
        'count': 60,
        'avg_sessions': 4,
    },
    'watch_collector': {
        'categories': {'dong-ho': 0.6, 'thoi-trang-nam': 0.2, 'thoi-trang-nu': 0.1, 'am-thanh': 0.1},
        'count': 40,
        'avg_sessions': 5,
    },
    'student': {
        'categories': {'sach': 0.3, 'laptop': 0.25, 'dien-thoai': 0.2, 'am-thanh': 0.15, 'the-thao': 0.1},
        'count': 60,
        'avg_sessions': 5,
    },
    'working_professional': {
        'categories': {'laptop': 0.3, 'am-thanh': 0.2, 'dong-ho': 0.2, 'do-gia-dung': 0.15, 'sach': 0.15},
        'count': 60,
        'avg_sessions': 4,
    },
    'mixed_shopper': {
        'categories': {
            'dien-thoai': 0.12, 'laptop': 0.12, 'thoi-trang-nam': 0.1, 'thoi-trang-nu': 0.1,
            'do-gia-dung': 0.1, 'sach': 0.1, 'the-thao': 0.1, 'my-pham': 0.1,
            'dong-ho': 0.08, 'am-thanh': 0.08,
        },
        'count': 80,
        'avg_sessions': 4,
    },
    'premium_buyer': {
        'categories': {'dien-thoai': 0.25, 'dong-ho': 0.25, 'am-thanh': 0.25, 'thoi-trang-nu': 0.25},
        'count': 40,
        'avg_sessions': 3,
    },
}

EVENT_TYPES = [
    'view_detail', 'add_to_cart', 'add_to_wishlist',
    'share_product', 'compare_product', 'check_stock',
]


class Command(BaseCommand):
    help = 'Seed rich synthetic user behavior data for AI training'

    def add_arguments(self, parser):
        parser.add_argument('--noinput', action='store_true')
        parser.add_argument('--force', action='store_true', help='Re-seed even if data exists')

    def handle(self, *args, **options):
        existing = UserProductView.objects.count()
        if existing >= 3000 and not options.get('force'):
            self.stdout.write(self.style.WARNING(
                f'Behavior data already exists ({existing} records). Use --force to re-seed.'
            ))
            return

        products_by_cat: dict[str, list[Product]] = {}
        for cat in Category.objects.filter(is_active=True):
            prods = list(Product.objects.filter(category=cat, is_active=True))
            if prods:
                products_by_cat[cat.slug] = prods

        if not products_by_cat:
            self.stdout.write(self.style.ERROR('No products found. Run seed_products first.'))
            return

        self.stdout.write(f'Found {sum(len(v) for v in products_by_cat.values())} products in {len(products_by_cat)} categories.')

        views_to_create = []
        clicks_to_create = []
        searches_to_create = []

        total_users = sum(p['count'] for p in USER_PROFILES.values())
        self.stdout.write(f'Generating behavior for {total_users} users...')

        for profile_name, profile_config in USER_PROFILES.items():
            cat_weights = profile_config['categories']
            n_users = profile_config['count']
            avg_sessions = profile_config['avg_sessions']

            valid_pairs = [(c, w) for c, w in cat_weights.items() if c in products_by_cat]
            if not valid_pairs:
                continue

            for _ in range(n_users):
                user_id = uuid.uuid4()
                n_sessions = random.randint(max(1, avg_sessions - 2), avg_sessions + 3)

                for _ in range(n_sessions):
                    session_id = str(uuid.uuid4())[:20]
                    cats, weights = zip(*valid_pairs)
                    n_views = random.randint(3, 12)

                    for _ in range(n_views):
                        cat_slug = random.choices(list(cats), weights=list(weights), k=1)[0]
                        product = random.choice(products_by_cat[cat_slug])

                        views_to_create.append(UserProductView(
                            id=uuid.uuid4(),
                            user_id=user_id,
                            session_id=session_id,
                            product_id=product.id,
                            source=random.choice(['search', 'homepage', 'category', 'recommendation', 'direct', 'social']),
                        ))

                        # Higher click probability for engaged users
                        click_prob = 0.45 if profile_name in ('tech_enthusiast', 'audiophile', 'watch_collector') else 0.35
                        if random.random() < click_prob:
                            clicks_to_create.append(UserClickEvent(
                                id=uuid.uuid4(),
                                user_id=user_id,
                                session_id=session_id,
                                event_type=random.choice(EVENT_TYPES),
                                product_id=product.id,
                                metadata={
                                    'price': str(product.price),
                                    'category': cat_slug,
                                    'profile': profile_name,
                                },
                            ))

                    # Search log generation
                    if random.random() < 0.4:
                        cat_slug = random.choices(list(cats), weights=list(weights), k=1)[0]
                        query_pool = SEARCH_QUERIES.get(cat_slug, ['sản phẩm'])
                        searches_to_create.append(UserSearchLog(
                            id=uuid.uuid4(),
                            user_id=user_id,
                            session_id=session_id,
                            query=random.choice(query_pool),
                            results_count=random.randint(3, 25),
                            filters={},
                        ))

        batch_size = 500
        for i in range(0, len(views_to_create), batch_size):
            UserProductView.objects.bulk_create(views_to_create[i:i + batch_size], ignore_conflicts=True)

        for i in range(0, len(clicks_to_create), batch_size):
            UserClickEvent.objects.bulk_create(clicks_to_create[i:i + batch_size], ignore_conflicts=True)

        for i in range(0, len(searches_to_create), batch_size):
            UserSearchLog.objects.bulk_create(searches_to_create[i:i + batch_size], ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(views_to_create):,} views, '
            f'{len(clicks_to_create):,} clicks, '
            f'{len(searches_to_create):,} search logs '
            f'for {total_users} users across {len(products_by_cat)} categories.'
        ))
