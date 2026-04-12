import random
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from domain.models import Category, Product


CATEGORIES = [
    {'name': 'Điện thoại', 'slug': 'dien-thoai', 'description': 'Smartphone và phụ kiện'},
    {'name': 'Laptop', 'slug': 'laptop', 'description': 'Laptop và máy tính xách tay'},
    {'name': 'Thời trang Nam', 'slug': 'thoi-trang-nam', 'description': 'Quần áo, giày dép nam'},
    {'name': 'Thời trang Nữ', 'slug': 'thoi-trang-nu', 'description': 'Quần áo, giày dép nữ'},
    {'name': 'Đồ gia dụng', 'slug': 'do-gia-dung', 'description': 'Thiết bị gia dụng thông minh'},
    {'name': 'Sách', 'slug': 'sach', 'description': 'Sách và tài liệu'},
    {'name': 'Thể thao', 'slug': 'the-thao', 'description': 'Dụng cụ và trang phục thể thao'},
    {'name': 'Mỹ phẩm', 'slug': 'my-pham', 'description': 'Mỹ phẩm và chăm sóc cá nhân'},
]

PRODUCTS = {
    'dien-thoai': [
        {'name': 'iPhone 15 Pro Max', 'brand': 'Apple', 'price': 34990000, 'compare_price': 38990000,
         'specs': {'ram': '8GB', 'storage': '256GB', 'screen': '6.7 inch', 'chip': 'A17 Pro'},
         'image': 'https://picsum.photos/seed/iphone15/400/400'},
        {'name': 'Samsung Galaxy S24 Ultra', 'brand': 'Samsung', 'price': 31990000, 'compare_price': 35990000,
         'specs': {'ram': '12GB', 'storage': '256GB', 'screen': '6.8 inch', 'chip': 'Snapdragon 8 Gen 3'},
         'image': 'https://picsum.photos/seed/s24ultra/400/400'},
        {'name': 'Xiaomi 14', 'brand': 'Xiaomi', 'price': 12990000, 'compare_price': 14990000,
         'specs': {'ram': '12GB', 'storage': '256GB', 'screen': '6.36 inch', 'chip': 'Snapdragon 8 Gen 3'},
         'image': 'https://picsum.photos/seed/xiaomi14/400/400'},
        {'name': 'OPPO Find X7 Ultra', 'brand': 'OPPO', 'price': 23990000, 'compare_price': None,
         'specs': {'ram': '16GB', 'storage': '512GB', 'screen': '6.82 inch'},
         'image': 'https://picsum.photos/seed/oppofindx7/400/400'},
        {'name': 'Google Pixel 8 Pro', 'brand': 'Google', 'price': 18990000, 'compare_price': 21990000,
         'specs': {'ram': '12GB', 'storage': '128GB', 'screen': '6.7 inch', 'chip': 'Tensor G3'},
         'image': 'https://picsum.photos/seed/pixel8/400/400'},
        {'name': 'iPhone 15', 'brand': 'Apple', 'price': 22990000, 'compare_price': 24990000,
         'specs': {'ram': '6GB', 'storage': '128GB', 'screen': '6.1 inch', 'chip': 'A16 Bionic'},
         'image': 'https://picsum.photos/seed/iphone15base/400/400'},
        {'name': 'Samsung Galaxy A55', 'brand': 'Samsung', 'price': 9990000, 'compare_price': 10990000,
         'specs': {'ram': '8GB', 'storage': '128GB', 'screen': '6.6 inch'},
         'image': 'https://picsum.photos/seed/a55/400/400'},
    ],
    'laptop': [
        {'name': 'MacBook Pro 14 M3 Pro', 'brand': 'Apple', 'price': 49990000, 'compare_price': 52990000,
         'specs': {'ram': '18GB', 'storage': '512GB SSD', 'screen': '14.2 inch', 'chip': 'M3 Pro'},
         'image': 'https://picsum.photos/seed/macbookpro/400/400'},
        {'name': 'Dell XPS 15', 'brand': 'Dell', 'price': 35990000, 'compare_price': 39990000,
         'specs': {'ram': '16GB', 'storage': '512GB SSD', 'screen': '15.6 inch', 'chip': 'Intel i7-13700H'},
         'image': 'https://picsum.photos/seed/dellxps/400/400'},
        {'name': 'ASUS ROG Strix G16', 'brand': 'ASUS', 'price': 32990000, 'compare_price': None,
         'specs': {'ram': '16GB', 'storage': '1TB SSD', 'screen': '16 inch', 'gpu': 'RTX 4060'},
         'image': 'https://picsum.photos/seed/rogstrix/400/400'},
        {'name': 'Lenovo ThinkPad X1 Carbon', 'brand': 'Lenovo', 'price': 28990000, 'compare_price': 32990000,
         'specs': {'ram': '16GB', 'storage': '512GB SSD', 'screen': '14 inch', 'chip': 'Intel i7-1365U'},
         'image': 'https://picsum.photos/seed/thinkpad/400/400'},
        {'name': 'HP Pavilion 15', 'brand': 'HP', 'price': 15990000, 'compare_price': 17990000,
         'specs': {'ram': '8GB', 'storage': '512GB SSD', 'screen': '15.6 inch', 'chip': 'Intel i5-1335U'},
         'image': 'https://picsum.photos/seed/hppav/400/400'},
        {'name': 'MacBook Air M2', 'brand': 'Apple', 'price': 27990000, 'compare_price': 29990000,
         'specs': {'ram': '8GB', 'storage': '256GB SSD', 'screen': '13.6 inch', 'chip': 'M2'},
         'image': 'https://picsum.photos/seed/macbookair/400/400'},
    ],
    'thoi-trang-nam': [
        {'name': 'Áo Polo Classic', 'brand': 'Routine', 'price': 350000, 'compare_price': 450000,
         'specs': {'material': 'Cotton', 'sizes': 'S, M, L, XL', 'color': 'Trắng, Đen, Navy'},
         'image': 'https://picsum.photos/seed/polo/400/400'},
        {'name': 'Quần Jean Slim Fit', 'brand': 'Levi\'s', 'price': 1290000, 'compare_price': 1590000,
         'specs': {'material': 'Denim', 'sizes': '29-36', 'style': 'Slim Fit'},
         'image': 'https://picsum.photos/seed/jeanslim/400/400'},
        {'name': 'Giày Sneaker Urban', 'brand': 'Nike', 'price': 2490000, 'compare_price': 2990000,
         'specs': {'sizes': '39-44', 'color': 'Trắng', 'sole': 'Air Max'},
         'image': 'https://picsum.photos/seed/nikesneaker/400/400'},
        {'name': 'Áo Khoác Bomber', 'brand': 'Zara', 'price': 1490000, 'compare_price': None,
         'specs': {'material': 'Polyester', 'sizes': 'M, L, XL'},
         'image': 'https://picsum.photos/seed/bomber/400/400'},
        {'name': 'Quần Short Thể Thao', 'brand': 'Adidas', 'price': 590000, 'compare_price': 750000,
         'specs': {'material': 'Polyester', 'sizes': 'S-XL'},
         'image': 'https://picsum.photos/seed/adidasshort/400/400'},
        {'name': 'Áo Thun Oversize', 'brand': 'Uniqlo', 'price': 390000, 'compare_price': None,
         'specs': {'material': '100% Cotton', 'sizes': 'M, L, XL, XXL'},
         'image': 'https://picsum.photos/seed/oversize/400/400'},
    ],
    'thoi-trang-nu': [
        {'name': 'Đầm Maxi Hoa', 'brand': 'Elise', 'price': 1290000, 'compare_price': 1590000,
         'specs': {'material': 'Voan', 'sizes': 'S, M, L', 'style': 'Maxi'},
         'image': 'https://picsum.photos/seed/maxidress/400/400'},
        {'name': 'Áo Blouse Lụa', 'brand': 'IVY moda', 'price': 890000, 'compare_price': None,
         'specs': {'material': 'Lụa satin', 'sizes': 'S, M, L'},
         'image': 'https://picsum.photos/seed/blouse/400/400'},
        {'name': 'Chân Váy Midi', 'brand': 'Zara', 'price': 990000, 'compare_price': 1200000,
         'specs': {'material': 'Polyester', 'sizes': 'XS-L'},
         'image': 'https://picsum.photos/seed/midiskirt/400/400'},
        {'name': 'Giày Cao Gót', 'brand': 'Juno', 'price': 490000, 'compare_price': 650000,
         'specs': {'height': '7cm', 'sizes': '35-39', 'color': 'Đen, Nude'},
         'image': 'https://picsum.photos/seed/heels/400/400'},
        {'name': 'Túi Xách Tote', 'brand': 'Charles & Keith', 'price': 1490000, 'compare_price': 1790000,
         'specs': {'material': 'Da PU', 'color': 'Đen, Nâu'},
         'image': 'https://picsum.photos/seed/tote/400/400'},
        {'name': 'Áo Khoác Dạ Dài', 'brand': 'Elise', 'price': 2490000, 'compare_price': 2990000,
         'specs': {'material': 'Dạ tweed', 'sizes': 'S, M, L'},
         'image': 'https://picsum.photos/seed/dacoat/400/400'},
    ],
    'do-gia-dung': [
        {'name': 'Nồi chiên không dầu 6L', 'brand': 'Philips', 'price': 3490000, 'compare_price': 3990000,
         'specs': {'capacity': '6L', 'power': '2000W', 'features': 'Digital, 8 chế độ'},
         'image': 'https://picsum.photos/seed/airfryer/400/400'},
        {'name': 'Máy hút bụi Robot', 'brand': 'Xiaomi', 'price': 7990000, 'compare_price': 8990000,
         'specs': {'suction': '4000Pa', 'battery': '5200mAh', 'features': 'Laser mapping'},
         'image': 'https://picsum.photos/seed/robotvac/400/400'},
        {'name': 'Máy lọc không khí', 'brand': 'Sharp', 'price': 4990000, 'compare_price': None,
         'specs': {'area': '40m²', 'filter': 'HEPA', 'features': 'Ion Plasmacluster'},
         'image': 'https://picsum.photos/seed/airpurifier/400/400'},
        {'name': 'Bàn ủi hơi nước đứng', 'brand': 'Tefal', 'price': 1990000, 'compare_price': 2490000,
         'specs': {'power': '1800W', 'tank': '1.5L'},
         'image': 'https://picsum.photos/seed/steamer/400/400'},
        {'name': 'Máy xay sinh tố Vitamix', 'brand': 'Vitamix', 'price': 5990000, 'compare_price': 6990000,
         'specs': {'power': '1500W', 'capacity': '2L', 'speed': '10 tốc độ'},
         'image': 'https://picsum.photos/seed/blender/400/400'},
        {'name': 'Nồi cơm điện cao tần', 'brand': 'Cuckoo', 'price': 6490000, 'compare_price': 7490000,
         'specs': {'capacity': '1.8L', 'features': 'IH, áp suất'},
         'image': 'https://picsum.photos/seed/ricecooker/400/400'},
    ],
    'sach': [
        {'name': 'Đắc Nhân Tâm', 'brand': 'NXB Tổng hợp', 'price': 86000, 'compare_price': 108000,
         'specs': {'author': 'Dale Carnegie', 'pages': 320, 'format': 'Bìa mềm'},
         'image': 'https://picsum.photos/seed/dacnhantam/400/400'},
        {'name': 'Nhà Giả Kim', 'brand': 'NXB Hội Nhà Văn', 'price': 69000, 'compare_price': 79000,
         'specs': {'author': 'Paulo Coelho', 'pages': 228, 'format': 'Bìa mềm'},
         'image': 'https://picsum.photos/seed/nhagiakim/400/400'},
        {'name': 'Clean Code', 'brand': 'Prentice Hall', 'price': 590000, 'compare_price': None,
         'specs': {'author': 'Robert C. Martin', 'pages': 464, 'language': 'English'},
         'image': 'https://picsum.photos/seed/cleancode/400/400'},
        {'name': 'Sapiens: Lược sử loài người', 'brand': 'NXB Tri Thức', 'price': 199000, 'compare_price': 239000,
         'specs': {'author': 'Yuval Noah Harari', 'pages': 520, 'format': 'Bìa cứng'},
         'image': 'https://picsum.photos/seed/sapiens/400/400'},
        {'name': 'Atomic Habits', 'brand': 'Avery', 'price': 320000, 'compare_price': 380000,
         'specs': {'author': 'James Clear', 'pages': 320, 'language': 'Vietnamese'},
         'image': 'https://picsum.photos/seed/atomichabits/400/400'},
        {'name': 'Tư Duy Nhanh Và Chậm', 'brand': 'NXB Thế Giới', 'price': 189000, 'compare_price': 229000,
         'specs': {'author': 'Daniel Kahneman', 'pages': 600, 'format': 'Bìa mềm'},
         'image': 'https://picsum.photos/seed/thinkingfast/400/400'},
        {'name': 'Design Patterns', 'brand': 'Addison-Wesley', 'price': 690000, 'compare_price': None,
         'specs': {'author': 'Gang of Four', 'pages': 395, 'language': 'English'},
         'image': 'https://picsum.photos/seed/designpatterns/400/400'},
    ],
    'the-thao': [
        {'name': 'Vợt cầu lông Yonex Astrox 88D', 'brand': 'Yonex', 'price': 3490000, 'compare_price': 3990000,
         'specs': {'weight': '83g', 'balance': 'Head Heavy', 'material': 'Carbon'},
         'image': 'https://picsum.photos/seed/yonex/400/400'},
        {'name': 'Giày chạy bộ Ultraboost 22', 'brand': 'Adidas', 'price': 4290000, 'compare_price': 4990000,
         'specs': {'sizes': '39-45', 'sole': 'Boost', 'weight': '310g'},
         'image': 'https://picsum.photos/seed/ultraboost/400/400'},
        {'name': 'Bóng đá Adidas UCL Pro', 'brand': 'Adidas', 'price': 1290000, 'compare_price': None,
         'specs': {'size': '5', 'material': 'PU', 'certification': 'FIFA Pro'},
         'image': 'https://picsum.photos/seed/soccerball/400/400'},
        {'name': 'Thảm Yoga TPE 8mm', 'brand': 'Nike', 'price': 790000, 'compare_price': 890000,
         'specs': {'thickness': '8mm', 'material': 'TPE', 'size': '183x61cm'},
         'image': 'https://picsum.photos/seed/yogamat/400/400'},
        {'name': 'Bộ tạ tay 20kg', 'brand': 'Reebok', 'price': 1990000, 'compare_price': 2290000,
         'specs': {'weight': '20kg set', 'material': 'Cast Iron', 'includes': '2 bars, 8 plates'},
         'image': 'https://picsum.photos/seed/dumbbell/400/400'},
        {'name': 'Áo thể thao DRI-FIT', 'brand': 'Nike', 'price': 890000, 'compare_price': 1090000,
         'specs': {'material': 'Polyester DRI-FIT', 'sizes': 'S-XXL'},
         'image': 'https://picsum.photos/seed/drifit/400/400'},
    ],
    'my-pham': [
        {'name': 'Kem chống nắng UV Expert SPF50+', 'brand': "L'Oreal", 'price': 390000, 'compare_price': 450000,
         'specs': {'spf': '50+ PA++++', 'volume': '50ml', 'type': 'Lightweight'},
         'image': 'https://picsum.photos/seed/sunscreen/400/400'},
        {'name': 'Serum Vitamin C 20%', 'brand': 'Klairs', 'price': 490000, 'compare_price': None,
         'specs': {'volume': '35ml', 'ingredients': 'Vitamin C, Niacinamide'},
         'image': 'https://picsum.photos/seed/vitcserum/400/400'},
        {'name': 'Sữa rửa mặt Amino Acid', 'brand': 'Cerave', 'price': 290000, 'compare_price': 350000,
         'specs': {'volume': '236ml', 'skin_type': 'Normal to Oily'},
         'image': 'https://picsum.photos/seed/facewash/400/400'},
        {'name': 'Nước tẩy trang Micellar', 'brand': 'Bioderma', 'price': 350000, 'compare_price': 420000,
         'specs': {'volume': '500ml', 'type': 'Sensibio H2O'},
         'image': 'https://picsum.photos/seed/micellar/400/400'},
        {'name': 'Mặt nạ ngủ Laneige', 'brand': 'Laneige', 'price': 590000, 'compare_price': 690000,
         'specs': {'volume': '70ml', 'type': 'Water Sleeping Mask'},
         'image': 'https://picsum.photos/seed/sleepingmask/400/400'},
        {'name': 'Son môi Rouge Dior', 'brand': 'Dior', 'price': 990000, 'compare_price': None,
         'specs': {'type': 'Matte', 'shade': '999 Red', 'weight': '3.5g'},
         'image': 'https://picsum.photos/seed/rougedior/400/400'},
        {'name': 'Nước hoa Chanel Chance', 'brand': 'Chanel', 'price': 3290000, 'compare_price': 3690000,
         'specs': {'volume': '50ml', 'type': 'Eau de Parfum'},
         'image': 'https://picsum.photos/seed/chanelchance/400/400'},
    ],
}


class Command(BaseCommand):
    help = 'Seed categories and products'

    def add_arguments(self, parser):
        parser.add_argument('--noinput', action='store_true')

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write(self.style.WARNING('Products already exist, skipping seed.'))
            return

        self.stdout.write('Seeding categories and products...')

        # Create categories
        cat_map = {}
        for cat_data in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                },
            )
            cat_map[cat_data['slug']] = cat
            self.stdout.write(f'  ✓ Category: {cat.name}')

        # Create products
        count = 0
        for cat_slug, products in PRODUCTS.items():
            category = cat_map[cat_slug]
            for i, p in enumerate(products):
                slug = slugify(p['name'])
                # Ensure unique slug
                if Product.objects.filter(slug=slug).exists():
                    slug = f'{slug}-{i}'

                Product.objects.create(
                    name=p['name'],
                    slug=slug,
                    description=f'{p["name"]} - Sản phẩm chính hãng, chất lượng cao. {category.description}',
                    category=category,
                    brand=p.get('brand', ''),
                    price=p['price'],
                    compare_price=p.get('compare_price'),
                    sku=f'{cat_slug[:3].upper()}-{str(count + 1).zfill(4)}',
                    stock_quantity=random.randint(10, 200),
                    sold_count=random.randint(0, 500),
                    specifications=p.get('specs', {}),
                    image_url=p.get('image', ''),
                    images=[
                        f'https://picsum.photos/seed/{slug}-{j}/400/400'
                        for j in range(1, 4)
                    ],
                    rating_avg=round(random.uniform(3.5, 5.0), 2),
                    rating_count=random.randint(5, 300),
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeded {len(CATEGORIES)} categories and {count} products!'
        ))
