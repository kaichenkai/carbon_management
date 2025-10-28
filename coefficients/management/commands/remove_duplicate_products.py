from django.core.management.base import BaseCommand
from django.db.models import Count
from coefficients.models import EmissionCoefficient


class Command(BaseCommand):
    help = '删除 product_name 重复的碳排放系数记录，保留最新的'

    def handle(self, *args, **options):
        # 找出所有重复的 product_name
        duplicates = (
            EmissionCoefficient.objects
            .values('product_name')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        
        if not duplicates:
            self.stdout.write(self.style.SUCCESS('没有发现重复的产品名称'))
            return
        
        total_deleted = 0
        
        for duplicate in duplicates:
            product_name = duplicate['product_name']
            count = duplicate['count']
            
            # 获取该产品名称的所有记录，按更新时间排序
            records = EmissionCoefficient.objects.filter(
                product_name=product_name
            ).order_by('-updated_at')
            
            # 保留第一条（最新的），删除其他的
            keep_record = records.first()
            delete_records = records[1:]
            
            self.stdout.write(
                self.style.WARNING(
                    f'\n产品名称: {product_name} (共 {count} 条记录)'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'  保留: ID={keep_record.id}, 产品代码={keep_record.product_code}, '
                    f'更新时间={keep_record.updated_at}'
                )
            )
            
            for record in delete_records:
                self.stdout.write(
                    self.style.ERROR(
                        f'  删除: ID={record.id}, 产品代码={record.product_code}, '
                        f'更新时间={record.updated_at}'
                    )
                )
                record.delete()
                total_deleted += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n完成！共删除 {total_deleted} 条重复记录'
            )
        )
