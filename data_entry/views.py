from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q, Sum
import threading
from .models import MaterialConsumption, ConsumerData, ImportTask
from .forms import (
    MaterialConsumptionForm, 
    DataImportForm, 
    ConsumptionSearchForm, 
    ConsumerDataForm, 
    ConsumerSearchForm,
    ConsumerDataImportForm
)
from coefficients.models import EmissionCoefficient, EmissionCategory
import pandas as pd
from datetime import datetime, date, time
from decimal import Decimal
from io import BytesIO


def consumption_list(request):
    """List all material consumption records"""
    consumptions = MaterialConsumption.objects.all()
    
    # Search form
    search_form = ConsumptionSearchForm(request.GET)
    query = request.GET.get('query', '').strip()
    
    # Search: product_code and product_name only
    if query:
        consumptions = consumptions.filter(
            Q(product_code__icontains=query) |
            Q(product_name__icontains=query)
        )
    
    # Dropdown filters
    filter_restaurant = request.GET.get('filter_restaurant', '').strip()
    filter_product_code = request.GET.get('filter_product_code', '').strip()
    filter_category1 = request.GET.get('filter_category1', '').strip()
    filter_category2 = request.GET.get('filter_category2', '').strip()
    
    if filter_restaurant:
        consumptions = consumptions.filter(restaurant=filter_restaurant)
    if filter_product_code:
        consumptions = consumptions.filter(product_code=filter_product_code)
    if filter_category1:
        consumptions = consumptions.filter(category_level1__name=filter_category1)
    if filter_category2:
        consumptions = consumptions.filter(category_level2__name=filter_category2)
    
    # Date filters
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    
    if start_date:
        consumptions = consumptions.filter(order_date__gte=start_date)
    if end_date:
        consumptions = consumptions.filter(order_date__lte=end_date)
    
    # Sorting
    sort_by = request.GET.get('sort', '-order_date')
    order = request.GET.get('order', 'desc')
    
    # Valid sort fields
    valid_sorts = {
        'restaurant': 'restaurant',
        'product_code': 'product_code',
        'product_name': 'product_name',
        'category_level1': 'category_level1__name',
        'category_level2': 'category_level2__name',
        'order_date': 'order_date',
        'consumption_time': 'consumption_time',
        'quantity': 'quantity',
        'carbon_emission': 'carbon_emission',
    }
    
    if sort_by.lstrip('-') in valid_sorts:
        actual_sort_field = valid_sorts[sort_by.lstrip('-')]
        if order == 'asc':
            consumptions = consumptions.order_by(actual_sort_field)
        else:
            consumptions = consumptions.order_by(f'-{actual_sort_field}')
    else:
        consumptions = consumptions.order_by('-order_date', '-consumption_time', '-created_at')
    
    # Build filter option lists based on current search+filter state (for cross-linking)
    # Each dropdown shows values that exist in results when its own filter is ignored
    base = MaterialConsumption.objects.all()
    if query:
        base = base.filter(Q(product_code__icontains=query) | Q(product_name__icontains=query))
    if start_date:
        base = base.filter(order_date__gte=start_date)
    if end_date:
        base = base.filter(order_date__lte=end_date)

    # restaurants: apply all filters except restaurant itself
    base_restaurant = base
    if filter_product_code:
        base_restaurant = base_restaurant.filter(product_code=filter_product_code)
    if filter_category1:
        base_restaurant = base_restaurant.filter(category_level1__name=filter_category1)
    if filter_category2:
        base_restaurant = base_restaurant.filter(category_level2__name=filter_category2)

    # product_codes: apply all filters except product_code itself
    base_product_code = base
    if filter_restaurant:
        base_product_code = base_product_code.filter(restaurant=filter_restaurant)
    if filter_category1:
        base_product_code = base_product_code.filter(category_level1__name=filter_category1)
    if filter_category2:
        base_product_code = base_product_code.filter(category_level2__name=filter_category2)

    # category1: apply all filters except category1 itself
    base_category1 = base
    if filter_restaurant:
        base_category1 = base_category1.filter(restaurant=filter_restaurant)
    if filter_product_code:
        base_category1 = base_category1.filter(product_code=filter_product_code)
    if filter_category2:
        base_category1 = base_category1.filter(category_level2__name=filter_category2)

    # category2: apply all filters except category2 itself; if category1 selected, limit to its children
    base_category2 = base
    if filter_restaurant:
        base_category2 = base_category2.filter(restaurant=filter_restaurant)
    if filter_product_code:
        base_category2 = base_category2.filter(product_code=filter_product_code)
    if filter_category1:
        base_category2 = base_category2.filter(category_level1__name=filter_category1)

    filter_options = {
        'restaurants': sorted(set(base_restaurant.values_list('restaurant', flat=True))),
        'product_codes': sorted(set(base_product_code.values_list('product_code', flat=True))),
        'category1_list': sorted(set(base_category1.values_list('category_level1__name', flat=True))),
        'category2_list': sorted(set(base_category2.values_list('category_level2__name', flat=True))),
    }
    
    # Pagination
    paginator = Paginator(consumptions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_sort': sort_by.lstrip('-'),
        'current_order': order,
        'search_form': search_form,
        'filter_options': filter_options,
        'filter_restaurant': filter_restaurant,
        'filter_product_code': filter_product_code,
        'filter_category1': filter_category1,
        'filter_category2': filter_category2,
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
    """Import material consumption data from Excel/CSV file (async)"""
    if request.method == 'POST':
        form = DataImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)

                raw_df = df.copy()
                task = ImportTask.objects.create(total_rows=len(df))

                def run(task_id, dataframe, original_dataframe):
                    process_import_data_async(task_id, dataframe, original_dataframe)

                t = threading.Thread(target=run, args=(str(task.id), df, raw_df), daemon=True)
                t.start()

                return redirect('import_progress', task_id=str(task.id))
            except Exception as e:
                messages.error(request, gettext('文件处理失败：%(error)s') % {'error': str(e)})
    else:
        form = DataImportForm()

    context = {'form': form}
    return render(request, 'data_entry/import_form.html', context)


def import_progress(request, task_id):
    """Show import progress page"""
    task = get_object_or_404(ImportTask, id=task_id)
    return render(request, 'data_entry/import_progress.html', {'task': task})


def import_progress_api(request, task_id):
    """JSON API for polling import task progress, supports ?page= for error pagination"""
    task = get_object_or_404(ImportTask, id=task_id)
    percent = 0
    if task.total_rows > 0:
        percent = int(task.processed_rows / task.total_rows * 100)
    page_size = 100
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    all_errors = task.error_details or []
    start = (page - 1) * page_size
    end = start + page_size
    total_pages = max(1, (len(all_errors) + page_size - 1) // page_size)
    return JsonResponse({
        'status': task.status,
        'total_rows': task.total_rows,
        'processed_rows': task.processed_rows,
        'success_count': task.success_count,
        'error_count': len(all_errors),
        'errors': all_errors[start:end],
        'error_message': task.error_message,
        'percent': percent,
        'page': page,
        'total_pages': total_pages,
    })


def import_error_export(request, task_id):
    """Download failed import rows with the failure reason in the last column"""
    task = get_object_or_404(ImportTask, id=task_id)
    if task.error_file:
        from django.conf import settings
        import os
        filepath = os.path.join(settings.MEDIA_ROOT, task.error_file)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                response = HttpResponse(
                    f.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            response['Content-Disposition'] = f'attachment; filename="failed_import_rows_{task_id}.xlsx"'
            return response

    return HttpResponse(gettext('失败数据文件不存在，请重新导入后再下载。'), status=404)


def _parse_date(val):
    """Parse a date value from various formats, return date or raise ValueError."""
    if isinstance(val, str):
        date_str = val.strip()
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(date_str)
    return pd.to_datetime(val).date()


def _parse_time(val):
    """Parse a time value, return time or raise ValueError."""
    from datetime import time as time_type
    if isinstance(val, time_type):
        return val
    if isinstance(val, str):
        time_str = val.strip()
        try:
            return datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError:
            return datetime.strptime(time_str, '%H:%M').time()
    if hasattr(val, 'time'):
        return val.time() if callable(val.time) else val.time
    return pd.to_datetime(val).time()


def process_import_data(df, task=None):
    """Process imported data and validate"""
    required_columns = ['餐厅', '产品编码', '一级分类', '二级分类', '产品名称', '订单日期', '消耗数量']
    column_mapping = {
        '餐厅': 'restaurant',
        '产品编码': 'product_code',
        '一级分类': 'category_level1',
        '二级分类': 'category_level2',
        '产品名称': 'product_name',
        '订单日期': 'order_date',
        '消耗时间': 'consumption_time',
        '消耗数量': 'quantity',
    }

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return {
            'success': False,
            'error': gettext('缺少必需列：%(columns)s') % {'columns': ', '.join(missing_columns)}
        }

    rename_map = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Pre-load all categories and coefficients into memory to avoid per-row queries
    level1_map = {obj.name: obj for obj in EmissionCategory.objects.filter(level=1)}
    level2_map = {(obj.name, obj.parent_id): obj for obj in EmissionCategory.objects.filter(level=2)}
    coeff_map = {
        (obj.category_level1_id, obj.category_level2_id): obj
        for obj in EmissionCoefficient.objects.all()
    }

    # Pre-load existing record unique keys to avoid per-row duplicate checks
    existing_keys = set(
        MaterialConsumption.objects.values_list(
            'restaurant', 'category_level1_id', 'category_level2_id',
            'product_name', 'order_date', 'consumption_time', 'quantity'
        )
    )

    success_count = 0
    errors = []
    to_create = []
    total = len(df)

    for index, row in df.iterrows():
        row_num = index + 2
        try:
            # Restaurant
            restaurant = str(row['restaurant']).strip()
            if not restaurant:
                errors.append({'row': row_num, 'error': gettext('餐厅不能为空')})
                continue

            # Categories (in-memory lookup)
            level1_name = str(row['category_level1']).strip()
            level2_name = str(row['category_level2']).strip()

            category_level1 = level1_map.get(level1_name)
            if not category_level1:
                errors.append({
                    'row': row_num,
                    'error': gettext('一级分类 "%(category)s" 不存在') % {'category': level1_name}
                })
                continue

            category_level2 = level2_map.get((level2_name, category_level1.pk))
            if not category_level2:
                errors.append({
                    'row': row_num,
                    'error': gettext('二级分类 "%(level2)s" 不存在或不属于 "%(level1)s"') % {
                        'level2': level2_name, 'level1': level1_name
                    }
                })
                continue

            # Product code
            product_code = str(row['product_code']).strip() if pd.notna(row.get('product_code')) else ''
            if not product_code:
                errors.append({'row': row_num, 'error': gettext('产品编码不能为空')})
                continue

            product_name = str(row['product_name']).strip()

            # Coefficient (in-memory lookup)
            coefficient = coeff_map.get((category_level1.pk, category_level2.pk))
            if not coefficient:
                errors.append({'row': row_num, 'error': gettext('未找到匹配的碳排放系数')})
                continue

            product_unit = coefficient.unit
            emission_coefficient = coefficient.coefficient

            # Parse date
            order_date = None
            if pd.notna(row['order_date']):
                try:
                    order_date = _parse_date(row['order_date'])
                except Exception:
                    errors.append({
                        'row': row_num,
                        'error': gettext('日期格式错误：%(date)s') % {'date': row['order_date']}
                    })
                    continue

            # Parse time (optional)
            consumption_time = None
            if 'consumption_time' in df.columns and pd.notna(row.get('consumption_time')):
                try:
                    consumption_time = _parse_time(row['consumption_time'])
                except Exception:
                    errors.append({
                        'row': row_num,
                        'error': gettext('时间格式错误：%(time)s') % {'time': str(row['consumption_time'])}
                    })
                    continue

            # Parse quantity
            try:
                quantity = float(row['quantity'])
                if quantity < 0:
                    errors.append({'row': row_num, 'error': gettext('消耗数量不能为负数')})
                    continue
            except Exception:
                errors.append({
                    'row': row_num,
                    'error': gettext('消耗数量格式错误：%(quantity)s') % {'quantity': row['quantity']}
                })
                continue

            # Duplicate check (in-memory)
            dup_key = (restaurant, category_level1.pk, category_level2.pk, product_name, order_date, consumption_time, Decimal(str(quantity)))
            if dup_key in existing_keys:
                errors.append({
                    'row': row_num,
                    'error': gettext('重复记录：该餐厅、产品在此日期且消耗数量相同的记录已存在')
                })
                continue

            existing_keys.add(dup_key)
            to_create.append(MaterialConsumption(  # noqa
                restaurant=restaurant,
                product_code=product_code,
                category_level1=category_level1,
                category_level2=category_level2,
                product_name=product_name,
                order_date=order_date,
                consumption_time=consumption_time,
                quantity=Decimal(str(quantity)),
                product_unit=product_unit,
                emission_coefficient=emission_coefficient,
            ))
            success_count += 1

        except Exception as e:
            errors.append({
                'row': row_num,
                'error': gettext('处理失败：%(error)s') % {'error': str(e)}
            })

        # Update progress every 500 rows
        if task is not None and (index + 1) % 500 == 0:
            task.processed_rows = index + 1
            task.save(update_fields=['processed_rows', 'updated_at'])

    # Pre-calculate carbon_emission (bulk_create skips save())
    for obj in to_create:
        obj.carbon_emission = obj.quantity * obj.emission_coefficient

    # Bulk insert in batches of 2000
    if to_create:
        with transaction.atomic():
            MaterialConsumption.objects.bulk_create(to_create, batch_size=2000)

    return {
        'success': True,
        'success_count': success_count,
        'errors': errors,
        'total_rows': len(df)
    }


def process_import_data_async(task_id, df, raw_df=None):
    """Run process_import_data in background thread, updating ImportTask progress"""
    import django
    django.setup.__module__  # ensure app registry is ready

    from .models import ImportTask
    try:
        task = ImportTask.objects.get(id=task_id)
        task.status = ImportTask.STATUS_PROCESSING
        task.save(update_fields=['status', 'updated_at'])

        result = process_import_data(df, task=task)

        if not result.get('success'):
            task.status = ImportTask.STATUS_FAILED
            task.error_message = result.get('error', gettext('导入失败'))
            task.processed_rows = task.total_rows
            task.save(update_fields=['status', 'error_message', 'processed_rows', 'updated_at'])
            return

        # Build error file if there are failed rows
        error_file_path = ''
        if result.get('errors'):
            from django.conf import settings
            import os
            orig = raw_df
            error_positions = [
                e['row'] - 2 for e in result['errors']
                if e.get('row') is not None and e['row'] >= 2
            ]
            error_reasons = {
                e['row'] - 2: e['error'] for e in result['errors']
                if e.get('row') is not None and e['row'] >= 2
            }
            if orig is not None and error_positions:
                try:
                    valid_positions = [pos for pos in error_positions if 0 <= pos < len(orig)]
                    err_df = orig.iloc[valid_positions].copy()
                    err_df['失败原因'] = [error_reasons.get(pos, '') for pos in valid_positions]
                    media_root = str(settings.MEDIA_ROOT)
                    save_dir = os.path.join(media_root, 'import_errors')
                    os.makedirs(save_dir, exist_ok=True)
                    filename = f'import_errors_{task_id}.xlsx'
                    filepath = os.path.join(save_dir, filename)
                    err_df.to_excel(filepath, index=False)
                    if os.path.exists(filepath):
                        error_file_path = f'import_errors/{filename}'
                except Exception as file_err:
                    task.error_message = gettext('失败数据文件生成失败：%(error)s') % {'error': str(file_err)}

        errors_for_db = [{'row': e['row'], 'error': e['error']} for e in result['errors']]

        task.status = ImportTask.STATUS_DONE
        task.success_count = result['success_count']
        task.error_details = errors_for_db
        task.processed_rows = result['total_rows']
        task.error_file = error_file_path
        task.save(update_fields=[
            'status', 'success_count', 'error_details', 'processed_rows',
            'error_file', 'error_message', 'updated_at'
        ])
    except Exception as e:
        try:
            task = ImportTask.objects.get(id=task_id)
            task.status = ImportTask.STATUS_FAILED
            task.error_message = str(e)
            task.save(update_fields=['status', 'error_message', 'updated_at'])
        except Exception:
            pass


def download_import_template(request):
    """Download Excel template for data import"""
    # Create a sample DataFrame with column headers
    df = pd.DataFrame(columns=[
        '餐厅',
        '产品编码',
        '产品名称',
        '订单日期',
        '消耗时间',
        '一级分类',
        '二级分类',
        '消耗数量'
    ])
    
    # Add sample data
    df.loc[0] = [
        'F&B',
        'SKU-001',
        '示例产品',
        '2024-01-01',
        '10:30:00',
        '示例一级分类',
        '示例二级分类',
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
    from django.utils import translation
    from urllib.parse import quote
    lang = translation.get_language()
    if lang and lang.startswith('zh'):
        filename = '物料消耗导入模板.xlsx'
    else:
        filename = 'material_consumption_import_template.xlsx'
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    
    return response


def consumption_export(request):
    """Export consumption records to Excel"""
    # Get filter parameters
    export_all = request.GET.get('all', 'false') == 'true'
    ids = request.GET.get('ids', '')
    
    # Get records based on selection
    if export_all:
        consumptions = MaterialConsumption.objects.all().order_by('-order_date')
    elif ids:
        id_list = [int(id.strip()) for id in ids.split(',') if id.strip()]
        consumptions = MaterialConsumption.objects.filter(pk__in=id_list).order_by('-order_date')
    else:
        consumptions = MaterialConsumption.objects.none()
    
    # Prepare data for export
    data = []
    for consumption in consumptions:
        data.append({
            gettext('餐厅'): consumption.restaurant,
            gettext('产品编码'): consumption.product_code,
            gettext('产品名称'): consumption.product_name,
            gettext('订单日期'): consumption.order_date.strftime('%Y-%m-%d') if consumption.order_date else '',
            gettext('消耗时间'): consumption.consumption_time.strftime('%H:%M:%S') if consumption.consumption_time else '',
            gettext('一级分类'): consumption.category_level1.name,
            gettext('二级分类'): consumption.category_level2.name,
            gettext('碳排放系数'): float(consumption.emission_coefficient),
            gettext('消耗数量'): float(consumption.quantity),
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
    from django.utils import translation
    from urllib.parse import quote
    lang = translation.get_language()
    if lang and lang.startswith('zh'):
        filename = f'物料消耗记录_{timestamp}.xlsx'
    else:
        filename = f'consumption_records_{timestamp}.xlsx'
    
    # Return as download
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
    
    return response


# Consumer Data Views

def consumer_list(request):
    """List all consumer data records"""
    consumers = ConsumerData.objects.all()
    
    # Search form
    search_form = ConsumerSearchForm(request.GET)
    query = request.GET.get('query', '').strip()
    
    # Apply search filter
    if query:
        consumers = consumers.filter(
            Q(restaurant__icontains=query)
        )
    
    # Date filters
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    
    if start_date:
        consumers = consumers.filter(order_date__gte=start_date)
    if end_date:
        consumers = consumers.filter(order_date__lte=end_date)
    
    # Sorting
    sort_by = request.GET.get('sort', '-order_date')
    order = request.GET.get('order', 'desc')
    
    # Valid sort fields
    valid_sorts = {
        'restaurant': 'restaurant',
        'order_date': 'order_date',
        'consumer_count': 'consumer_count',
        'daily_carbon_emission': 'daily_carbon_emission',
    }
    
    if sort_by.lstrip('-') in valid_sorts:
        actual_sort_field = valid_sorts[sort_by.lstrip('-')]
        if order == 'asc':
            consumers = consumers.order_by(actual_sort_field)
        else:
            consumers = consumers.order_by(f'-{actual_sort_field}')
    else:
        consumers = consumers.order_by('-order_date', '-created_at')
    
    # Pagination
    paginator = Paginator(consumers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate adjusted carbon emission for each record in current page
    for consumer in page_obj:
        # Get the year and month of this record
        if not consumer.order_date:
            consumer.adjusted_emission = None
            continue
        year = consumer.order_date.year
        month = consumer.order_date.month
        
        # Query all records for the same restaurant and month
        monthly_data = ConsumerData.objects.filter(
            restaurant=consumer.restaurant,
            order_date__year=year,
            order_date__month=month
        ).aggregate(
            total_emission=Sum('daily_carbon_emission'),
            total_consumers=Sum('consumer_count')
        )
        
        # Calculate adjusted carbon emission
        total_emission = monthly_data['total_emission'] or Decimal('0')
        total_consumers = monthly_data['total_consumers'] or 0
        
        if total_consumers > 0:
            # Formula: (当月总碳排 / 当月总人数) × 当日消费者人数
            consumer.adjusted_daily_carbon_emission = (total_emission / Decimal(total_consumers)) * Decimal(consumer.consumer_count)
        else:
            consumer.adjusted_daily_carbon_emission = Decimal('0')
    
    context = {
        'page_obj': page_obj,
        'current_sort': sort_by.lstrip('-'),
        'current_order': order,
        'search_form': search_form,
    }
    return render(request, 'data_entry/consumer_list.html', context)


def consumer_create(request):
    """Create new consumer data record"""
    if request.method == 'POST':
        form = ConsumerDataForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _('消费者数据创建成功'))
                return redirect('consumer_list')
            except Exception as e:
                messages.error(request, _('创建失败：%(error)s') % {'error': str(e)})
    else:
        form = ConsumerDataForm()
    
    context = {
        'form': form,
    }
    return render(request, 'data_entry/consumer_form.html', context)


def consumer_edit(request, pk):
    """Edit existing consumer data record"""
    consumer = get_object_or_404(ConsumerData, pk=pk)
    
    if request.method == 'POST':
        form = ConsumerDataForm(request.POST, instance=consumer)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _('消费者数据更新成功'))
                return redirect('consumer_list')
            except Exception as e:
                messages.error(request, _('更新失败：%(error)s') % {'error': str(e)})
    else:
        form = ConsumerDataForm(instance=consumer)
    
    context = {
        'form': form,
        'consumer': consumer,
    }
    return render(request, 'data_entry/consumer_form.html', context)


def consumer_delete(request, pk):
    """Delete consumer data record"""
    consumer = get_object_or_404(ConsumerData, pk=pk)
    consumer.delete()
    messages.success(request, _('消费者数据删除成功'))
    return redirect('consumer_list')


def consumer_refresh_emissions(request):
    """Refresh all daily carbon emissions for consumer data"""
    try:
        consumers = ConsumerData.objects.all()
        updated_count = 0
        
        for consumer in consumers:
            old_emission = consumer.daily_carbon_emission
            consumer.daily_carbon_emission = consumer.calculate_daily_emission()
            if old_emission != consumer.daily_carbon_emission:
                consumer.save(update_fields=['daily_carbon_emission', 'updated_at'])
                updated_count += 1
        
        messages.success(request, _('成功刷新 %(count)s 条记录的碳排放数据') % {'count': updated_count})
    except Exception as e:
        messages.error(request, _('刷新失败：%(error)s') % {'error': str(e)})
    
    return redirect('consumer_list')


def consumer_import(request):
    """Import consumer data from Excel/CSV file"""
    if request.method == 'POST':
        form = ConsumerDataImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            
            try:
                # Read file based on extension
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Process the data
                result = process_consumer_import_data(df)
                
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
                    return render(request, 'data_entry/consumer_import_result.html', {
                        'result': result
                    })
                else:
                    messages.error(request, gettext('导入失败：%(error)s') % {'error': result['error']})
                    
            except Exception as e:
                messages.error(request, gettext('文件处理失败：%(error)s') % {'error': str(e)})
    else:
        form = ConsumerDataImportForm()
    
    context = {
        'form': form,
    }
    return render(request, 'data_entry/consumer_import_form.html', context)


def process_consumer_import_data(df):
    """Process imported consumer data and validate"""
    # Expected column mapping (Chinese to English)
    column_mapping = {
        '餐厅': 'restaurant',
        '订单日期': 'order_date',
        '消费者人数': 'consumer_count',
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
    
    # Optional columns
    if '特殊备注' in df.columns:
        df = df.rename(columns={'特殊备注': 'notes'})
    
    # Results tracking
    success_count = 0
    errors = []
    
    # Process each row
    with transaction.atomic():
        for index, row in df.iterrows():
            row_num = index + 2  # Excel row (1-indexed + header)
            
            try:
                # Validate restaurant
                restaurant = str(row['restaurant']).strip()
                if not restaurant:
                    errors.append({
                        'row': row_num,
                        'error': gettext('餐厅不能为空')
                    })
                    continue
                
                # Parse order date
                try:
                    order_date = pd.to_datetime(row['order_date']).date()
                except:
                    errors.append({
                        'row': row_num,
                        'error': gettext('日期格式错误：%(date)s') % {'date': row['order_date']}
                    })
                    continue
                
                # Parse consumer count
                try:
                    consumer_count = int(row['consumer_count'])
                    if consumer_count <= 0:
                        errors.append({
                            'row': row_num,
                            'error': gettext('消费者人数必须大于0')
                        })
                        continue
                except:
                    errors.append({
                        'row': row_num,
                        'error': gettext('消费者人数格式错误：%(count)s') % {'count': row['consumer_count']}
                    })
                    continue
                
                # Get notes (optional)
                notes = ''
                if 'notes' in row and pd.notna(row['notes']):
                    notes = str(row['notes']).strip()
                
                # Check if record already exists
                existing_record = ConsumerData.objects.filter(
                    restaurant=restaurant,
                    order_date=order_date,
                ).first()
                
                if existing_record:
                    # Record already exists - treat as error
                    errors.append({
                        'row': row_num,
                        'error': gettext('记录已存在（ID: %(id)s）') % {'id': existing_record.id}
                    })
                    continue
                
                # Create new record
                ConsumerData.objects.create(
                    restaurant=restaurant,
                    order_date=order_date,
                    consumer_count=consumer_count,
                    notes=notes,
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


def consumer_download_template(request):
    """Download Excel template for consumer data import"""
    # Create a sample DataFrame with column headers
    df = pd.DataFrame(columns=[
        '餐厅',
        '订单日期',
        '消费者人数',
        '特殊备注'
    ])
    
    # Add sample data
    df.loc[0] = [
        'F&B',
        '2024-01-01',
        '100',
        '示例备注（可选）'
    ]
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='消费者数据导入模板')
    
    output.seek(0)
    
    # Return as download
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="consumer_data_import_template.xlsx"'
    
    return response
