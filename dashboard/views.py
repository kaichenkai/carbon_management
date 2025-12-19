from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from django.db.models import Sum, Count, F
from data_entry.models import MaterialConsumption, ConsumerData
from coefficients.models import EmissionCoefficient, EmissionCategory
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal
import json


def dashboard_view(request):
    """
    Dashboard view with consumption data visualization
    
    Performance optimizations:
    1. Uses select_related() to avoid N+1 queries
    2. Single-pass data aggregation to minimize iterations
    3. Database indexes recommended on:
       - MaterialConsumption.consumption_date
       - MaterialConsumption.category_level1_id
       - MaterialConsumption.category_level2_id
       - MaterialConsumption.department
    """
    
    # Get date range from request (default: July 2024)
    end_date = request.GET.get('end_date')
    start_date = request.GET.get('start_date')
    category_level1_id = request.GET.get('category_level1')
    category_level2_id = request.GET.get('category_level2')
    
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        # Default: end of July 2024
        end_date = datetime(2024, 7, 31).date()
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        # Default: start of July 2024
        start_date = datetime(2024, 7, 1).date()
    
    # Query consumption data with filters - use select_related to avoid N+1 queries
    consumptions_base = MaterialConsumption.objects.filter(
        consumption_date__range=[start_date, end_date]
    )
    
    # Apply category filters if provided
    if category_level1_id:
        consumptions_base = consumptions_base.filter(category_level1_id=category_level1_id)
    if category_level2_id:
        consumptions_base = consumptions_base.filter(category_level2_id=category_level2_id)
    
    # Use select_related to fetch related objects in one query
    consumptions = consumptions_base.select_related(
        'category_level1', 
        'category_level2'
    ).order_by('consumption_date')
    
    # Single pass through data to collect all statistics
    daily_stats = defaultdict(lambda: {'quantity': 0, 'emission': 0, 'count': 0})
    department_stats = defaultdict(lambda: {'emission': 0, 'count': 0})
    category_level1_stats = defaultdict(lambda: {'emission': 0, 'count': 0})
    category_level2_by_level1 = defaultdict(lambda: defaultdict(float))
    
    total_records = 0
    total_emission = 0
    total_quantity = 0
    
    # Single iteration to gather all statistics
    for consumption in consumptions:
        # Daily stats
        date_key = consumption.consumption_date.strftime('%Y-%m-%d')
        daily_stats[date_key]['quantity'] += float(consumption.quantity)
        daily_stats[date_key]['emission'] += float(consumption.carbon_emission)
        daily_stats[date_key]['count'] += 1
        
        # Department stats
        dept = consumption.department
        department_stats[dept]['emission'] += float(consumption.carbon_emission)
        department_stats[dept]['count'] += 1
        
        # Category level 1 stats
        cat1_name = consumption.category_level1.name
        category_level1_stats[cat1_name]['emission'] += float(consumption.carbon_emission)
        category_level1_stats[cat1_name]['count'] += 1
        
        # Category level 2 stats grouped by level 1
        cat2_name = consumption.category_level2.name
        category_level2_by_level1[cat1_name][cat2_name] += float(consumption.carbon_emission)
        
        # Summary totals
        total_records += 1
        total_emission += float(consumption.carbon_emission)
        total_quantity += float(consumption.quantity)
    
    # Prepare daily data for Chart.js
    dates = sorted(daily_stats.keys())
    quantities = [daily_stats[date]['quantity'] for date in dates]
    emissions = [daily_stats[date]['emission'] for date in dates]
    record_counts = [daily_stats[date]['count'] for date in dates]
    
    # Prepare department data
    sorted_departments = sorted(department_stats.items(), key=lambda x: x[1]['emission'], reverse=True)
    department_labels = []
    department_emissions = []
    
    for dept, stats in sorted_departments:
        dept_name = dict(EmissionCoefficient.DEPARTMENT_CHOICES).get(dept, dept)
        department_labels.append(force_str(dept_name))
        department_emissions.append(stats['emission'])
    
    # Prepare category level 1 data
    sorted_categories = sorted(category_level1_stats.items(), key=lambda x: x[1]['emission'], reverse=True)
    category_level1_labels = []
    category_level1_emissions = []
    
    for cat_name, stats in sorted_categories:
        category_level1_labels.append(cat_name)
        category_level1_emissions.append(stats['emission'])
    
    # Convert to format suitable for JavaScript
    category_level2_data = {}
    for cat1_name, cat2_dict in category_level2_by_level1.items():
        # Sort level 2 categories by emission within each level 1
        sorted_cat2 = sorted(cat2_dict.items(), key=lambda x: x[1], reverse=True)
        category_level2_data[cat1_name] = {
            'labels': [item[0] for item in sorted_cat2],
            'emissions': [item[1] for item in sorted_cat2]
        }
    
    # Get the latest record date for quick range buttons
    latest_record = MaterialConsumption.objects.order_by('-consumption_date').first()
    latest_date = latest_record.consumption_date if latest_record else end_date
    
    # Get all categories for filter dropdowns
    categories_level1 = EmissionCategory.objects.filter(level=1).order_by('name')
    categories_level2 = EmissionCategory.objects.filter(level=2).order_by('name')
    
    # Build category hierarchy for cascade dropdown
    category_hierarchy = {}
    for cat2 in categories_level2:
        # Use string parent_id as key, skip if no parent
        if cat2.parent_id:
            parent_id = str(cat2.parent_id)
            if parent_id not in category_hierarchy:
                category_hierarchy[parent_id] = []
            category_hierarchy[parent_id].append({
                'id': cat2.id,
                'name': cat2.name
            })
    
    # Query consumer data for adjusted daily carbon emission chart
    consumer_data = ConsumerData.objects.filter(
        consumption_date__range=[start_date, end_date]
    ).order_by('consumption_date')
    
    # Calculate adjusted daily carbon emission for each record
    adjusted_daily_stats = defaultdict(lambda: Decimal('0'))
    
    for consumer in consumer_data:
        # Get the year and month of this record
        year = consumer.consumption_date.year
        month = consumer.consumption_date.month
        
        # Query all records for the same hotel, department, and month
        monthly_data = ConsumerData.objects.filter(
            hotel_name=consumer.hotel_name,
            department=consumer.department,
            consumption_date__year=year,
            consumption_date__month=month
        ).aggregate(
            total_emission=Sum('daily_carbon_emission'),
            total_consumers=Sum('consumer_count')
        )
        
        # Calculate adjusted carbon emission
        total_emission = monthly_data['total_emission'] or Decimal('0')
        total_consumers = monthly_data['total_consumers'] or 0
        
        if total_consumers > 0:
            # Formula: (当月总碳排 / 当月总人数) × 当日消费者人数
            adjusted_emission = (total_emission / Decimal(total_consumers)) * Decimal(consumer.consumer_count)
            date_key = consumer.consumption_date.strftime('%Y-%m-%d')
            adjusted_daily_stats[date_key] += adjusted_emission
    
    # Prepare adjusted daily carbon emission data
    adjusted_dates = sorted(adjusted_daily_stats.keys())
    adjusted_emissions = [float(adjusted_daily_stats[date]) for date in adjusted_dates]
    
    # Calculate monthly per capita carbon emission
    monthly_per_capita_stats = defaultdict(lambda: {'total_emission': Decimal('0'), 'total_consumers': 0})
    
    for consumer in consumer_data:
        month_key = consumer.consumption_date.strftime('%Y-%m')
        monthly_per_capita_stats[month_key]['total_emission'] += consumer.daily_carbon_emission
        monthly_per_capita_stats[month_key]['total_consumers'] += consumer.consumer_count
    
    # Prepare monthly per capita data
    monthly_per_capita_dates = sorted(monthly_per_capita_stats.keys())
    monthly_per_capita_emissions = []
    
    for month in monthly_per_capita_dates:
        stats = monthly_per_capita_stats[month]
        if stats['total_consumers'] > 0:
            per_capita = float(stats['total_emission'] / Decimal(stats['total_consumers']))
        else:
            per_capita = 0
        monthly_per_capita_emissions.append(per_capita)
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'latest_date': latest_date,
        'today': datetime.now().date(),
        'total_records': total_records,
        'total_emission': total_emission,
        'total_quantity': total_quantity,
        'dates_json': json.dumps(dates),
        'quantities_json': json.dumps(quantities),
        'emissions_json': json.dumps(emissions),
        'record_counts_json': json.dumps(record_counts),
        'department_labels_json': json.dumps(department_labels),
        'department_emissions_json': json.dumps(department_emissions),
        'category_level1_labels_json': json.dumps(category_level1_labels),
        'category_level1_emissions_json': json.dumps(category_level1_emissions),
        'category_level2_data_json': json.dumps(category_level2_data),
        'categories_level1': categories_level1,
        'categories_level2': categories_level2,
        'category_hierarchy_json': json.dumps(category_hierarchy),
        'selected_category_level1': category_level1_id,
        'selected_category_level2': category_level2_id,
        # Consumer data charts
        'adjusted_dates_json': json.dumps(adjusted_dates),
        'adjusted_emissions_json': json.dumps(adjusted_emissions),
        'monthly_per_capita_dates_json': json.dumps(monthly_per_capita_dates),
        'monthly_per_capita_emissions_json': json.dumps(monthly_per_capita_emissions),
    }
    
    return render(request, 'dashboard/dashboard.html', context)
