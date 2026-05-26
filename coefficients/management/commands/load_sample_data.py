from django.core.management.base import BaseCommand
from coefficients.models import EmissionCoefficient, EmissionCategory


class Command(BaseCommand):
    help = '加载示例碳排放系数数据'

    def handle(self, *args, **kwargs):
        # Sample data from requirements
        sample_data = [
            {
                'category_level1': 'Seafood',
                'category_level2': 'Molluscs, other',
                'unit': 'KG',
                'coefficient': '7.30',
                'special_note': ''
            },
            {
                'category_level1': 'Meat',
                'category_level2': 'Bovine meat',
                'unit': 'KG',
                'coefficient': '42.80',
                'special_note': ''
            },
            {
                'category_level1': 'Meat',
                'category_level2': 'Pig meat',
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
                category_level1=level1_category,
                category_level2=level2_category,
                defaults={
                    'unit': data['unit'],
                    'coefficient': data['coefficient'],
                    'special_note': data['special_note'],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 创建: {coefficient}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ 更新: {coefficient}'))

        self.stdout.write(self.style.SUCCESS(f'\n完成！创建 {created_count} 条，更新 {updated_count} 条记录。'))
