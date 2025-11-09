from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str
from data_entry.models import MaterialConsumption
from coefficients.models import EmissionCoefficient
from datetime import datetime, timedelta
from collections import defaultdict
import json


def dashboard_view(request):
    """Dashboard view with consumption data visualization"""
    
    # Get date range from request (default: July 2024)
    end_date = request.GET.get('end_date')
    start_date = request.GET.get('start_date')
    
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
    
    # Query consumption data
    consumptions = MaterialConsumption.objects.filter(
        consumption_date__range=[start_date, end_date]
    ).order_by('consumption_date')
    
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
    
    # Get the latest record date for quick range buttons
    latest_record = MaterialConsumption.objects.order_by('-consumption_date').first()
    latest_date = latest_record.consumption_date if latest_record else end_date
    
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
    }
    
    return render(request, 'dashboard/dashboard.html', context)
