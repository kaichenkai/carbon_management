from django.core.management.base import BaseCommand
from coefficients.models import EmissionCoefficient, EmissionCategory


class Command(BaseCommand):
    help = '加载示例碳排放系数数据'

    def handle(self, *args, **kwargs):
        # Sample data from requirements
        sample_data = [
            {
                'product_code': 'F101000965',
                'category_level1': 'Seafood',
                'category_level2': 'Molluscs, other',
                'product_name': 'Chiton（石鳖）',
                'product_name_en': 'Chiton',
                'unit': 'KG',
                'coefficient': '7.30',
                'special_note': ''
            },
            {
                'product_code': 'F101005265',
                'category_level1': 'Meat',
                'category_level2': 'Bovine meat',
                'product_name': 'Ground Beef（牛肉末）',
                'product_name_en': 'Ground Beef',
                'unit': 'KG',
                'coefficient': '42.80',
                'special_note': ''
            },
            {
                'product_code': 'F101002059',
                'category_level1': 'Meat',
                'category_level2': 'Pig meat',
                'product_name': 'Bacon（培根）',
                'product_name_en': 'Bacon',
                'unit': 'KG',
                'coefficient': '7.28',
                'special_note': ''
            },
        ]

        created_count = 0
        updated_count = 0

        for data in sample_data:
            # Get or create level 1 category
            level1_category, _ = EmissionCategory.objects.get_or_create(
                name=data['category_level1'],
                level=1,
                defaults={'parent': None}
            )

            # Get or create level 2 category
            level2_category, _ = EmissionCategory.objects.get_or_create(
                name=data['category_level2'],
                level=2,
                parent=level1_category
            )

            # Create or update coefficient
            coefficient, created = EmissionCoefficient.objects.update_or_create(
                product_code=data['product_code'],
                defaults={
                    'category_level1': level1_category,
                    'category_level2': level2_category,
                    'product_name': data['product_name'],
                    'product_name_en': data['product_name_en'],
                    'unit': data['unit'],
                    'coefficient': data['coefficient'],
                    'special_note': data['special_note'],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 创建: {coefficient.product_code} - {coefficient.product_name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ 更新: {coefficient.product_code} - {coefficient.product_name}'))

        self.stdout.write(self.style.SUCCESS(f'\n完成！创建 {created_count} 条，更新 {updated_count} 条记录。'))
