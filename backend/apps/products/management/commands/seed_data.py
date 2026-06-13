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
        settings.about_text = "Мы занимаемся качественным пошивом и прямой цифровой печатью на текстиле.\nИспользуем только премиальный хлопок (пенье) и сертифицированные гипоаллергенные краски."
        settings.manager_telegram = "@print_manager"
        settings.min_order_amount = 1000
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
            ('Черный', '#000000'),
            ('Белый', '#FFFFFF'),
            ('Красный', '#FF0000'),
            ('Серый', '#808080'),
        ]
        colors = []
        for name, hex_val in colors_data:
            color, _ = Color.objects.get_or_create(name=name, hex_color=hex_val)
            colors.append(color)
        self.stdout.write(f'- Добавлено цветов: {len(colors)}.')

        # 4. Print Positions (Места нанесения)
        positions_data = [
            ('Спереди', 0, 'print_positions/front.png', False),
            ('Сзади', 150, 'print_positions/back.png', False),
            ('Спереди + Сзади', 300, 'print_positions/front_back.png', True),
            ('На рукаве', 100, 'print_positions/sleeve.png', False),
        ]
        for name, extra, img_path, req_mult in positions_data:
            pos, created = PrintPosition.objects.get_or_create(name=name, defaults={'extra_price': extra, 'image': img_path, 'requires_multiple_designs': req_mult})
            if not created:
                pos.extra_price = extra
                pos.image = img_path
                pos.requires_multiple_designs = req_mult
                pos.save()
        self.stdout.write('- Места нанесения принтов добавлены.')

        # 5. Payment Methods (Способы оплаты)
        PaymentMethod.objects.get_or_create(
            title='Сбербанк',
            card_number='4276 0000 0000 0000',
            receiver_name='Иван И. И.',
            is_active=True
        )
        PaymentMethod.objects.get_or_create(
            title='Т-Банк (Тинькофф)',
            card_number='2200 0000 0000 0000',
            receiver_name='Иван И. И.',
            is_active=True
        )
        self.stdout.write('- Реквизиты оплаты успешно настроены.')

        # 6. Categories (Категории)
        cat_tshirt, _ = Category.objects.get_or_create(name='Футболки', is_active=True)
        cat_hoodie, _ = Category.objects.get_or_create(name='Худи', is_active=True)
        cat_sweatshirt, _ = Category.objects.get_or_create(name='Свитшоты', is_active=True)
        self.stdout.write('- Созданы категории товаров.')

        # 7. Products (Товары)
        p1, _ = Product.objects.get_or_create(
            category=cat_tshirt,
            title='Футболка Oversize',
            description='Свободный современный крой, плотный 100% премиум хлопок (220 г/м²). Идеальна для любого принта.',
            price=1500,
            is_active=True
        )
        p1.sizes.set(sizes)
        p1.colors.set(colors)

        p2, _ = Product.objects.get_or_create(
            category=cat_hoodie,
            title='Худи Premium',
            description='Худи с начесом, двойным глубоким капюшоном и удобным карманом "кенгуру". Плотность 340 г/м².',
            price=3500,
            is_active=True
        )
        p2.sizes.set(sizes)
        p2.colors.set(colors)

        p3, _ = Product.objects.get_or_create(
            category=cat_sweatshirt,
            title='Свитшот Classic',
            description='Классический свитшот без капюшона. Плотный хлопковый трикотаж с петельчатой изнанкой.',
            price=2500,
            is_active=True
        )
        p3.sizes.set(sizes)
        p3.colors.set(colors)

        self.stdout.write('- Созданы демонстрационные товары, к ним привязаны цвета и размеры.')
        self.stdout.write(self.style.SUCCESS('База данных успешно наполнена демонстрационными данными!'))
