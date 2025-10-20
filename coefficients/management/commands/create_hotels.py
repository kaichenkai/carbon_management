from django.core.management.base import BaseCommand
from coefficients.models import Hotel


class Command(BaseCommand):
    help = '创建初始酒店数据'

    def handle(self, *args, **options):
        hotels_data = [
            {
                'code': 'HOTEL001',
                'name': '绿色环保酒店（北京）',
                'name_en': 'Green Eco Hotel (Beijing)',
                'is_active': True
            },
            {
                'code': 'HOTEL002',
                'name': '碳中和度假酒店（上海）',
                'name_en': 'Carbon Neutral Resort Hotel (Shanghai)',
                'is_active': True
            }
        ]

        self.stdout.write("正在创建酒店数据...")
        
        for hotel_data in hotels_data:
            hotel, created = Hotel.objects.get_or_create(
                code=hotel_data['code'],
                defaults={
                    'name': hotel_data['name'],
                    'name_en': hotel_data['name_en'],
                    'is_active': hotel_data['is_active']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ 创建酒店: {hotel.code} - {hotel.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"○ 酒店已存在: {hotel.code} - {hotel.name}"))

        self.stdout.write("\n" + self.style.SUCCESS("酒店数据创建完成！"))
        self.stdout.write("\n当前所有酒店:")
        for hotel in Hotel.objects.all():
            self.stdout.write(f"  - {hotel.code}: {hotel.name} ({hotel.name_en})")
