from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q
from .models import MaterialConsumption
from .forms import MaterialConsumptionForm, DataImportForm, ConsumptionSearchForm
from coefficients.models import EmissionCoefficient, EmissionCategory
import pandas as pd
from datetime import datetime, date, time
from io import BytesIO
from decimal import Decimal


def consumption_list(request):
    """List all material consumption records"""
    consumptions = MaterialConsumption.objects.all()
    
    # Search form
    search_form = ConsumptionSearchForm(request.GET)
    query = request.GET.get('query', '').strip()
    
    # Apply search filter
    if query:
        consumptions = consumptions.filter(
            Q(department__icontains=query) |
            Q(category_level1__name__icontains=query) |
            Q(category_level2__name__icontains=query) |
            Q(product_name__icontains=query) |
            Q(hotel_name__icontains=query)
        )
    
    # Date and time filters
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    start_time = request.GET.get('start_time', '').strip()
    end_time = request.GET.get('end_time', '').strip()
    
    if start_date:
        consumptions = consumptions.filter(consumption_date__gte=start_date)
    if end_date:
        consumptions = consumptions.filter(consumption_date__lte=end_date)
    if start_time:
        consumptions = consumptions.filter(consumption_time__gte=start_time)
    if end_time:
        consumptions = consumptions.filter(consumption_time__lte=end_time)
    
    # Sorting
    sort_by = request.GET.get('sort', '-consumption_date')
    order = request.GET.get('order', 'desc')
    
    # Valid sort fields
    valid_sorts = {
        'hotel_name': 'hotel_name',
        'department': 'department',
        'product_name': 'product_name',
        'category_level1': 'category_level1__name',
        'category_level2': 'category_level2__name',
        'consumption_date': 'consumption_date',
        'quantity': 'quantity',
        'carbon_emission': 'carbon_emission',
    }
    
    if sort_by.lstrip('-') in valid_sorts:
        # Get the actual field name for sorting (handles ForeignKey relations)
        actual_sort_field = valid_sorts[sort_by.lstrip('-')]
        # Toggle order if clicking the same column
        if order == 'asc':
            consumptions = consumptions.order_by(actual_sort_field)
        else:
            consumptions = consumptions.order_by(f'-{actual_sort_field}')
    else:
        consumptions = consumptions.order_by('-consumption_date', '-consumption_time', '-created_at')
    
    # Pagination
    paginator = Paginator(consumptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_sort': sort_by.lstrip('-'),
        'current_order': order,
        'search_form': search_form,
    }
    return render(request, 'data_entry/consumption_list.html', context)


def consumption_create(request):
    """Create new material consumption record"""
    if request.method == 'POST':
        form = MaterialConsumptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('消耗记录创建成功'))
            return redirect('consumption_list')
    else:
        form = MaterialConsumptionForm()
    
    # Get all product codes for datalist
    product_names = EmissionCoefficient.objects.values_list('product_name', flat=True)
    
    context = {
        'form': form,
        'product_names': product_names,
    }
    return render(request, 'data_entry/consumption_form.html', context)


def consumption_edit(request, pk):
    """Edit existing material consumption record"""
    consumption = get_object_or_404(MaterialConsumption, pk=pk)
    
    if request.method == 'POST':
        form = MaterialConsumptionForm(request.POST, instance=consumption)
        if form.is_valid():
            form.save()
            messages.success(request, _('消耗记录更新成功'))
            return redirect('consumption_list')
    else:
        form = MaterialConsumptionForm(instance=consumption)
    
    # Get all product_names for datalist
    product_names = EmissionCoefficient.objects.values_list('product_name', flat=True)
    
    context = {
        'form': form,
        'product_names': product_names,
        'consumption': consumption,
    }
    return render(request, 'data_entry/consumption_form.html', context)


def consumption_delete(request, pk):
    """Delete material consumption record"""
    consumption = get_object_or_404(MaterialConsumption, pk=pk)
    consumption.delete()
    messages.success(request, _('消耗记录删除成功'))
    return redirect('consumption_list')


def get_level2_categories(request):
    """API endpoint to get level 2 categories by level 1 category"""
    level1_id = request.GET.get('level1_id')
    
    if not level1_id:
        return JsonResponse({'success': False, 'error': 'Missing level1_id'})
    
    try:
        level1_category = EmissionCategory.objects.get(id=level1_id, level=1)
        level2_categories = EmissionCategory.objects.filter(
            level=2,
            parent=level1_category
        ).values('id', 'name')
        
        return JsonResponse({
            'success': True,
            'categories': list(level2_categories)
        })
    except EmissionCategory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': _('一级分类不存在')
        })


def get_products_by_category(request):
    """API endpoint to get products by category"""
    level1_id = request.GET.get('level1_id')
    level2_id = request.GET.get('level2_id')
    
    try:
        filters = {}
        if level1_id:
            filters['category_level1_id'] = level1_id
        if level2_id:
            filters['category_level2_id'] = level2_id
        
        products = EmissionCoefficient.objects.filter(**filters).values(
            'id', 'product_name', 'unit', 'coefficient'
        )
        
        return JsonResponse({
            'success': True,
            'products': list(products)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def data_import(request):
    """Import material consumption data from Excel/CSV file"""
    if request.method == 'POST':
        form = DataImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            
            try:
                # Read file based on extension
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Process the data
                result = process_import_data(df)
                
                if result['success']:
                    messages.success(
                        request,
                        gettext('成功导入 %(count)s 条记录') % {'count': result["success_count"]}
                    )
                    if result['errors']:
                        messages.warning(
                            request,
                            gettext('失败 %(count)s 条记录，详情见下方') % {'count': len(result["errors"])}
                        )
                    return render(request, 'data_entry/import_result.html', {
                        'result': result
                    })
                else:
                    messages.error(request, gettext('导入失败：%(error)s') % {'error': result['error']})
                    
            except Exception as e:
                messages.error(request, gettext('文件处理失败：%(error)s') % {'error': str(e)})
    else:
        form = DataImportForm()
    
    context = {
        'form': form,
    }
    return render(request, 'data_entry/import_form.html', context)


def process_import_data(df):
    """Process imported data and validate"""
    # Expected column mapping (Chinese to English)
    column_mapping = {
        '酒店名称': 'hotel_name',
        '部门': 'department',
        '一级分类': 'category_level1',
        '二级分类': 'category_level2',
        '产品名称': 'product_name',
        '消耗日期': 'consumption_date',
        '消耗时间': 'consumption_time',
        '消耗数量': 'quantity',
    }
    
    # Check if all required columns exist
    missing_columns = [col for col in column_mapping.keys() if col not in df.columns]
    if missing_columns:
        return {
            'success': False,
            'error': gettext('缺少必需列：%(columns)s') % {'columns': ', '.join(missing_columns)}
        }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Results tracking
    success_count = 0
    errors = []
    
    # Department choices mapping
    dept_mapping = dict(EmissionCoefficient.DEPARTMENT_CHOICES)
    dept_reverse_mapping = {v: k for k, v in dept_mapping.items()}
    
    # Process each row
    with transaction.atomic():
        for index, row in df.iterrows():
            try:
                # Validate and convert data
                row_num = index + 2  # Excel row number (1-indexed + header)
                
                # Get hotel name
                hotel_name = str(row['hotel_name']).strip() if pd.notna(row['hotel_name']) else ''
                
                # Get department
                dept_name = str(row['department']).strip()
                department = dept_reverse_mapping.get(dept_name)
                if not department:
                    errors.append({
                        'row': row_num,
                        'error': gettext('部门 "%(dept)s" 不存在') % {'dept': dept_name}
                    })
                    continue
                
                # Get categories
                level1_name = str(row['category_level1']).strip()
                level2_name = str(row['category_level2']).strip()
                
                try:
                    category_level1 = EmissionCategory.objects.get(name=level1_name, level=1)
                except EmissionCategory.DoesNotExist:
                    errors.append({
                        'row': row_num,
                        'error': gettext('一级分类 "%(category)s" 不存在') % {'category': level1_name}
                    })
                    continue
                
                try:
                    category_level2 = EmissionCategory.objects.get(
                        name=level2_name,
                        level=2,
                        parent=category_level1
                    )
                except EmissionCategory.DoesNotExist:
                    errors.append({
                        'row': row_num,
                        'error': gettext('二级分类 "%(level2)s" 不存在或不属于 "%(level1)s"') % {'level2': level2_name, 'level1': level1_name}
                    })
                    continue
                
                # Get product name
                product_name = str(row['product_name']).strip()
                
                # Get emission coefficient (optional - try to find matching coefficient)
                coefficient = EmissionCoefficient.objects.filter(
                    category_level1=category_level1,
                    category_level2=category_level2,
                    # product_name=product_name
                ).first()

                if not coefficient:
                    errors.append({
                        'row': row_num,
                        'error': gettext('未找到匹配的碳排放系数')
                    })
                    continue
                
                product_unit = coefficient.unit
                emission_coefficient = coefficient.coefficient
                
                # Parse date
                consumption_date = None
                if pd.notna(row['consumption_date']):
                    try:
                        if isinstance(row['consumption_date'], str):
                            consumption_date = datetime.strptime(row['consumption_date'], '%Y-%m-%d').date()
                        else:
                            consumption_date = pd.to_datetime(row['consumption_date']).date()
                    except:
                        errors.append({
                            'row': row_num,
                            'error': gettext('日期格式错误：%(date)s') % {'date': row['consumption_date']}
                        })
                        continue
                
                # Parse time
                consumption_time = None
                if pd.notna(row['consumption_time']):
                    try:
                        # If already a time object
                        if isinstance(row['consumption_time'], time):
                            consumption_time = row['consumption_time']
                        # If it's a string
                        elif isinstance(row['consumption_time'], str):
                            time_str = row['consumption_time'].strip()
                            try:
                                consumption_time = datetime.strptime(time_str, '%H:%M:%S').time()
                            except:
                                consumption_time = datetime.strptime(time_str, '%H:%M').time()
                        # If it's a datetime object
                        elif isinstance(row['consumption_time'], pd.Timestamp):
                            consumption_time = row['consumption_time'].time()
                        # Try to convert to datetime
                        else:
                            consumption_time = pd.to_datetime(row['consumption_time']).time()
                    except Exception as e:
                        errors.append({
                            'row': row_num,
                            'error': gettext('时间格式错误：%(time)s (%(error)s)') % {'time': row['consumption_time'], 'error': str(e)}
                        })
                        continue
                
                # Parse quantity
                try:
                    quantity = float(row['quantity'])
                    if quantity <= 0:
                        errors.append({
                            'row': row_num,
                            'error': gettext('消耗数量必须大于0')
                        })
                        continue
                except:
                    errors.append({
                        'row': row_num,
                        'error': gettext('消耗数量格式错误：%(quantity)s') % {'quantity': row['quantity']}
                    })
                    continue

                emission_coefficient
                
                # update or record
                MaterialConsumption.objects.update_or_create(
                    hotel_name=hotel_name,
                    department=department,
                    category_level1=category_level1,
                    category_level2=category_level2,
                    product_name=product_name,
                    consumption_date=consumption_date,
                    consumption_time=consumption_time,
                    quantity=Decimal(str(quantity)),
                    defaults={
                        'product_unit': product_unit,
                        'emission_coefficient': emission_coefficient,
                    }
                )
                
                success_count += 1
                
            except Exception as e:
                errors.append({
                    'row': row_num,
                    'error': gettext('处理失败：%(error)s') % {'error': str(e)}
                })
    
    return {
        'success': True,
        'success_count': success_count,
        'errors': errors,
        'total_rows': len(df)
    }


def download_import_template(request):
    """Download Excel template for data import"""
    # Create a sample DataFrame with column headers
    df = pd.DataFrame(columns=[
        '酒店名称',
        '部门',
        '一级分类',
        '二级分类',
        '产品名称',
        '消耗日期',
        '消耗时间',
        '消耗数量'
    ])
    
    # Add sample data
    df.loc[0] = [
        '示例酒店',
        '客房部',
        '示例一级分类',
        '示例二级分类',
        '示例产品',
        '2024-01-01',
        '10:30:00',
        '100'
    ]
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='数据导入模板')
    
    output.seek(0)
    
    # Return as download
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="material_consumption_import_template.xlsx"'
    
    return response


def consumption_export(request):
    """Export consumption records to Excel"""
    # Get filter parameters
    export_all = request.GET.get('all', 'false') == 'true'
    ids = request.GET.get('ids', '')
    
    # Get records based on selection
    if export_all:
        consumptions = MaterialConsumption.objects.all().order_by('-consumption_date', '-consumption_time')
    elif ids:
        id_list = [int(id.strip()) for id in ids.split(',') if id.strip()]
        consumptions = MaterialConsumption.objects.filter(pk__in=id_list).order_by('-consumption_date', '-consumption_time')
    else:
        consumptions = MaterialConsumption.objects.none()
    
    # Prepare data for export
    data = []
    for consumption in consumptions:
        data.append({
            gettext('酒店名称'): consumption.hotel_name,
            gettext('部门'): consumption.get_department_display(),
            gettext('一级分类'): consumption.category_level1.name,
            gettext('二级分类'): consumption.category_level2.name,
            gettext('产品名称'): consumption.product_name,
            gettext('消耗日期'): consumption.consumption_date.strftime('%Y-%m-%d') if consumption.consumption_date else '',
            gettext('消耗时间'): consumption.consumption_time.strftime('%H:%M:%S') if consumption.consumption_time else '',
            gettext('消耗数量'): float(consumption.quantity),
            gettext('碳排放系数'): float(consumption.emission_coefficient),
            gettext('碳排放量(kgCO2e)'): float(consumption.carbon_emission),
            gettext('特殊备注'): consumption.special_note,
            gettext('创建时间'): consumption.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=gettext('消耗记录'))
        
        # Auto-adjust column widths
        worksheet = writer.sheets[gettext('消耗记录')]
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(str(col))
            )
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
    
    output.seek(0)
    
    # Generate filename with timestamp
    from datetime import datetime as dt
    timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
    filename = f'consumption_records_{timestamp}.xlsx'
    
    # Return as download
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
