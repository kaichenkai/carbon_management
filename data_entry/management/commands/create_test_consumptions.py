from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from data_entry.models import MaterialConsumption
from coefficients.models import EmissionCoefficient, EmissionCategory


class Command(BaseCommand):
    help = '创建20条测试物料消耗记录'

    def handle(self, *args, **options):
        # 获取一些现有的系数数据
        coefficients = EmissionCoefficient.objects.all()[:20]
        
        if not coefficients.exists():
            self.stdout.write(self.style.ERROR('没有找到碳排放系数数据，请先添加系数数据'))
            return
        
        # 酒店名称列表
        hotels = [
            '北京希尔顿酒店',
            '上海浦东香格里拉大酒店',
            '广州白天鹅宾馆',
            '深圳瑞吉酒店',
            '成都香格里拉大酒店',
            '杭州西湖国宾馆',
            '南京金陵饭店',
            '厦门悦华酒店',
            '青岛海景花园大酒店',
            '西安索菲特人民大厦',
            '重庆洲际酒店',
            '天津丽思卡尔顿酒店',
            '武汉万达瑞华酒店',
            '苏州凯宾斯基大酒店',
            '大连香格里拉大饭店',
            '三亚亚龙湾美高梅度假酒店',
            '长沙运达喜来登酒店',
            '郑州建国饭店',
            '济南索菲特银座大饭店',
            '昆明洲际酒店',
        ]
        
        # 删除现有测试数据（可选）
        # MaterialConsumption.objects.all().delete()
        
        created_count = 0
        base_date = datetime.now().date()
        
        for i, coeff in enumerate(coefficients[:20]):
            try:
                # 计算日期范围
                start_date = base_date - timedelta(days=i*3)
                end_date = start_date + timedelta(days=2)
                
                # 随机数量
                quantity = Decimal(str(10 + i * 5))
                
                consumption = MaterialConsumption.objects.create(
                    hotel_name=hotels[i],
                    department=coeff.department,
                    product_name=coeff.product_name,
                    category_level1=coeff.category_level1,
                    category_level2=coeff.category_level2,
                    product_unit=coeff.unit,
                    emission_coefficient=coeff.coefficient,
                    consumption_date_start=start_date,
                    consumption_date_end=end_date,
                    consumption_time_start=datetime.strptime('08:00', '%H:%M').time(),
                    consumption_time_end=datetime.strptime('18:00', '%H:%M').time(),
                    quantity=quantity,
                    notes=f'测试数据 #{i+1}'
                )
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'创建消耗记录 {i+1}: {consumption.hotel_name} - {consumption.product_name} '
                        f'(数量: {consumption.quantity}, 碳排放: {consumption.carbon_emission} kgCO2e)'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'创建记录 {i+1} 失败: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n成功创建 {created_count} 条物料消耗记录！')
        )
