from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from data_entry.models import MaterialConsumption
from coefficients.models import EmissionCoefficient, EmissionCategory
from datetime import datetime, timedelta
from collections import defaultdict
import json


def dashboard_view(request):
    """Dashboard view with consumption data visualization"""
    
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
    
    # Query consumption data with filters
    consumptions = MaterialConsumption.objects.filter(
        consumption_date__range=[start_date, end_date]
    )
    
    # Apply category filters if provided
    if category_level1_id:
        consumptions = consumptions.filter(category_level1_id=category_level1_id)
    if category_level2_id:
        consumptions = consumptions.filter(category_level2_id=category_level2_id)
    
    consumptions = consumptions.order_by('consumption_date')
    
    # Group data by date manually
    daily_stats = defaultdict(lambda: {'quantity': 0, 'emission': 0, 'count': 0})
    
    for consumption in consumptions:
        date_key = consumption.consumption_date.strftime('%Y-%m-%d')
        daily_stats[date_key]['quantity'] += float(consumption.quantity)
        daily_stats[date_key]['emission'] += float(consumption.carbon_emission)
        daily_stats[date_key]['count'] += 1
    
    # Prepare data for Chart.js
    dates = sorted(daily_stats.keys())
    quantities = [daily_stats[date]['quantity'] for date in dates]
    emissions = [daily_stats[date]['emission'] for date in dates]
    record_counts = [daily_stats[date]['count'] for date in dates]
    
    # Calculate summary statistics from already fetched data
    total_records = len(consumptions)
    total_emission = sum(float(c.carbon_emission) for c in consumptions)
    total_quantity = sum(float(c.quantity) for c in consumptions)
    
    # Get department breakdown
    department_stats = defaultdict(lambda: {'emission': 0, 'count': 0})
    
    for consumption in consumptions:
        dept = consumption.department
        department_stats[dept]['emission'] += float(consumption.carbon_emission)
        department_stats[dept]['count'] += 1
    
    # Sort departments by emission
    sorted_departments = sorted(department_stats.items(), key=lambda x: x[1]['emission'], reverse=True)
    
    department_labels = []
    department_emissions = []
    
    for dept, stats in sorted_departments:
        dept_name = dict(EmissionCoefficient.DEPARTMENT_CHOICES).get(dept, dept)
        # Convert lazy translation to string for JSON serialization
        department_labels.append(force_str(dept_name))
        department_emissions.append(stats['emission'])
    
    # Get category level 1 breakdown
    category_level1_stats = defaultdict(lambda: {'emission': 0, 'count': 0})
    
    for consumption in consumptions:
        cat1_name = consumption.category_level1.name
        category_level1_stats[cat1_name]['emission'] += float(consumption.carbon_emission)
        category_level1_stats[cat1_name]['count'] += 1
    
    # Sort categories by emission
    sorted_categories = sorted(category_level1_stats.items(), key=lambda x: x[1]['emission'], reverse=True)
    
    category_level1_labels = []
    category_level1_emissions = []
    
    for cat_name, stats in sorted_categories:
        category_level1_labels.append(cat_name)
        category_level1_emissions.append(stats['emission'])
    
    # Get the latest record date for quick range buttons
    latest_record = MaterialConsumption.objects.order_by('-consumption_date').first()
    latest_date = latest_record.consumption_date if latest_record else end_date
    
    # Get all categories for filter dropdowns
    categories_level1 = EmissionCategory.objects.filter(level=1).order_by('name')
    categories_level2 = EmissionCategory.objects.filter(level=2).order_by('name')
    
    # Build category hierarchy for cascade dropdown
    category_hierarchy = {}
    for cat2 in categories_level2:
        parent_id = cat2.parent_id if cat2.parent else None
        if parent_id not in category_hierarchy:
            category_hierarchy[parent_id] = []
        category_hierarchy[parent_id].append({
            'id': cat2.id,
            'name': cat2.name
        })
    
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
        'categories_level1': categories_level1,
        'categories_level2': categories_level2,
        'category_hierarchy_json': json.dumps(category_hierarchy),
        'selected_category_level1': category_level1_id,
        'selected_category_level2': category_level2_id,
    }
    
    return render(request, 'dashboard/dashboard.html', context)
