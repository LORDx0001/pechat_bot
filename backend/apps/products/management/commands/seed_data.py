from django.core.management.base import BaseCommand
from apps.users.models import StoreSettings
from apps.products.models import Category, Size, Color, PrintPosition, Product
from apps.orders.models import PaymentMethod

class Command(BaseCommand):
    help = 'Populates the database with initial seed data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database with demo data...')

        # 1. Store Settings Configuration
        settings = StoreSettings.load()
        settings.shop_name = "PrintWear Bot"
        settings.welcome_text = "👋 Добро пожаловать в PrintWear!\n\nЗдесь вы можете выбрать качественную одежду и заказать нанесение своего уникального принта.\n\nВыберите нужный пункт меню ниже:"
        settings.welcome_text_uz = "👋 PrintWear-ga xush kelibsiz!\n\nBu yerda siz o'zingizning noyob rasmingiz tushirilgan kiyimlarni buyurtma qilishingiz mumkin.\n\nKategoriyani tanlang:"
        settings.about_text = "Мы занимаемся качественным пошивом и прямой цифровой печатью на текстиле.\nИспользуем только премиальный хлопок (пенье) и сертифицированные гипоаллергенные краски."
        settings.about_text_uz = "Biz kiyim-kechak tikish va to'g'ridan-to'g'ri raqamli chop etish bilan shug'ullanamiz.\nFaqat premium paxtadan foydalanamiz."
        settings.manager_telegram = "@print_manager"
        settings.min_order_amount = 10000
        settings.currency = "UZS"
        settings.save()
        self.stdout.write('- Настройки магазина успешно сконфигурированы.')

        # 2. Sizes (Размеры)
        sizes_data = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        sizes = []
        for s_name in sizes_data:
            size, _ = Size.objects.get_or_create(name=s_name)
            sizes.append(size)
        self.stdout.write(f'- Добавлено размеров: {len(sizes)}.')

        # 3. Colors (Цвета)
        colors_data = [
            ('Черный', 'Qora', '#000000'),
            ('Белый', 'Oq', '#FFFFFF'),
            ('Красный', 'Qizil', '#FF0000'),
            ('Серый', 'Kulrang', '#808080'),
        ]
        colors = []
        for name, name_uz, hex_val in colors_data:
            color, _ = Color.objects.get_or_create(name=name, defaults={'name_uz': name_uz, 'hex_color': hex_val})
            if color.name_uz != name_uz:
                color.name_uz = name_uz
                color.save()
            colors.append(color)
        self.stdout.write(f'- Добавлено цветов: {len(colors)}.')

        # 4. Print Positions (Места нанесения)
        positions_data = [
            ('Спереди', 'Oldindan', 0, 'print_positions/front.png', False),
            ('Сзади', 'Orqadan', 20000, 'print_positions/back.png', False),
            ('Спереди + Сзади', 'Oldindan + Orqadan', 40000, 'print_positions/front_back.png', True),
            ('На рукаве', 'Yengida', 15000, 'print_positions/sleeve.png', False),
        ]
        for name, name_uz, extra, img_path, req_mult in positions_data:
            pos, created = PrintPosition.objects.get_or_create(name=name, defaults={'name_uz': name_uz, 'extra_price': extra, 'image': img_path, 'requires_multiple_designs': req_mult})
            if not created:
                pos.name_uz = name_uz
                pos.extra_price = extra
                pos.image = img_path
                pos.requires_multiple_designs = req_mult
                pos.save()
        self.stdout.write('- Места нанесения принтов добавлены.')

        # 5. Payment Methods (Способы оплаты)
        PaymentMethod.objects.get_or_create(
            title='Uzcard',
            card_number='8600 1234 5678 9012',
            receiver_name='Имя Получателя',
            is_active=True
        )
        PaymentMethod.objects.get_or_create(
            title='Humo',
            card_number='9860 1234 5678 9012',
            receiver_name='Имя Получателя',
            is_active=True
        )
        self.stdout.write('- Реквизиты оплаты успешно настроены.')

        # 6. Categories (Категории)
        cat_tshirt, _ = Category.objects.get_or_create(name='Футболки', defaults={'name_uz': 'Futbolkalar', 'is_active': True})
        if cat_tshirt.name_uz != 'Futbolkalar':
            cat_tshirt.name_uz = 'Futbolkalar'
            cat_tshirt.save()
        cat_hoodie, _ = Category.objects.get_or_create(name='Худи', defaults={'name_uz': 'Xudi', 'is_active': True})
        if cat_hoodie.name_uz != 'Xudi':
            cat_hoodie.name_uz = 'Xudi'
            cat_hoodie.save()
        cat_sweatshirt, _ = Category.objects.get_or_create(name='Свитшоты', defaults={'name_uz': 'Svitshotlar', 'is_active': True})
        if cat_sweatshirt.name_uz != 'Svitshotlar':
            cat_sweatshirt.name_uz = 'Svitshotlar'
            cat_sweatshirt.save()
        self.stdout.write('- Созданы категории товаров.')

        # 7. Products (Товары)
        p1, _ = Product.objects.get_or_create(
            category=cat_tshirt,
            title='Футболка Oversize',
            defaults={
                'title_uz': 'Oversize Futbolka',
                'description': 'Свободный современный крой, плотный 100% премиум хлопок (220 г/м²). Идеальна для любого принта.',
                'description_uz': 'Erkin zamonaviy bichim, qalin 100% premium paxta (220 g/m²). Har qanday rasm bosish uchun ideal.',
                'price': 120000,
                'is_active': True
            }
        )
        if p1.title_uz != 'Oversize Futbolka':
            p1.title_uz = 'Oversize Futbolka'
            p1.description_uz = 'Erkin zamonaviy bichim, qalin 100% premium paxta (220 g/m²). Har qanday rasm bosish uchun ideal.'
            p1.save()
        p1.sizes.set(sizes)
        p1.colors.set(colors)

        p2, _ = Product.objects.get_or_create(
            category=cat_hoodie,
            title='Худи Premium',
            defaults={
                'title_uz': 'Premium Xudi',
                'description': 'Худи с начесом, двойным глубоким капюшоном и удобным карманом "кенгуру". Плотность 340 г/м².',
                'description_uz': 'Issiq xudi, chuqur kapyushon va qulay "kenguru" cho\'ntakli. Zichligi 340 g/m².',
                'price': 300000,
                'is_active': True
            }
        )
        if p2.title_uz != 'Premium Xudi':
            p2.title_uz = 'Premium Xudi'
            p2.description_uz = 'Issiq xudi, chuqur kapyushon va qulay "kenguru" cho\'ntakli. Zichligi 340 g/m².'
            p2.save()
        p2.sizes.set(sizes)
        p2.colors.set(colors)

        p3, _ = Product.objects.get_or_create(
            category=cat_sweatshirt,
            title='Свитшот Classic',
            defaults={
                'title_uz': 'Classic Svitshot',
                'description': 'Классический свитшот без капюшона. Плотный хлопковый трикотаж с петельчатой изнанкой.',
                'description_uz': 'Kapyushonsiz klassik svitshot. Qalin paxtali trikotaj.',
                'price': 220000,
                'is_active': True
            }
        )
        if p3.title_uz != 'Classic Svitshot':
            p3.title_uz = 'Classic Svitshot'
            p3.description_uz = 'Kapyushonsiz klassik svitshot. Qalin paxtali trikotaj.'
            p3.save()
        p3.sizes.set(sizes)
        p3.colors.set(colors)

        self.stdout.write('- Созданы демонстрационные товары, к ним привязаны цвета и размеры.')
        self.stdout.write(self.style.SUCCESS('База данных успешно наполнена демонстрационными данными!'))
