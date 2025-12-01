"""
Dashboard performance test script
Run this to verify the optimization improvements
"""
import os
import django
import time
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carbon_management.settings')
django.setup()

from django.test.utils import override_settings
from django.db import connection
from django.db.models import Count
from data_entry.models import MaterialConsumption

def test_dashboard_query_performance():
    """Test the performance of dashboard queries"""
    
    print("=" * 60)
    print("Dashboard Query Performance Test")
    print("=" * 60)
    
    # Get total record count
    total_records = MaterialConsumption.objects.count()
    print(f"\nTotal records in database: {total_records:,}")
    
    # Test 1: Basic query with select_related
    print("\n1. Testing query with select_related...")
    start_time = time.time()
    
    consumptions = MaterialConsumption.objects.filter(
        consumption_date__range=['2024-07-01', '2024-07-31']
    ).select_related('category_level1', 'category_level2')
    
    # Force evaluation
    count = consumptions.count()
    list(consumptions[:100])  # Fetch first 100 records
    
    elapsed = time.time() - start_time
    print(f"   Query time: {elapsed:.3f}s")
    print(f"   Records found: {count:,}")
    
    # Test 2: Count queries executed
    print("\n2. Checking number of database queries...")
    
    with override_settings(DEBUG=True):
        from django.db import reset_queries, connection as db_conn
        reset_queries()
        
        consumptions = MaterialConsumption.objects.filter(
            consumption_date__range=['2024-07-01', '2024-07-31']
        ).select_related('category_level1', 'category_level2')
        
        # Simulate dashboard processing
        for c in consumptions[:50]:
            _ = c.category_level1.name
            _ = c.category_level2.name
            _ = c.carbon_emission
        
        query_count = len(db_conn.queries)
        print(f"   Number of queries: {query_count}")
        
        if query_count <= 2:
            print("   ✓ Excellent! No N+1 query problem")
        elif query_count <= 5:
            print("   ✓ Good performance")
        else:
            print("   ⚠ Warning: Possible N+1 query issue")
    
    # Test 3: Index usage verification
    print("\n3. Verifying index usage...")
    
    # Check if indexes exist
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND tbl_name='data_entry_materialconsumption'
            AND name LIKE '%consump%'
        """)
        indexes = cursor.fetchall()
        
        print(f"   Found {len(indexes)} dashboard-related indexes:")
        for idx in indexes:
            print(f"   - {idx[0]}")
    
    # Test 4: Aggregation performance
    print("\n4. Testing aggregation performance...")
    start_time = time.time()
    
    stats = MaterialConsumption.objects.filter(
        consumption_date__range=['2024-07-01', '2024-07-31']
    ).values('category_level1__name').annotate(
        count=Count('id')
    )
    
    list(stats)  # Force evaluation
    elapsed = time.time() - start_time
    print(f"   Aggregation time: {elapsed:.3f}s")
    
    print("\n" + "=" * 60)
    print("Performance test completed!")
    print("=" * 60)
    
    # Performance recommendations
    print("\n📊 Performance Summary:")
    if total_records < 1000:
        print("   Data size: Small (< 1,000 records)")
        print("   Expected response time: < 100ms")
    elif total_records < 10000:
        print("   Data size: Medium (1,000 - 10,000 records)")
        print("   Expected response time: 100-500ms")
    else:
        print("   Data size: Large (> 10,000 records)")
        print("   Expected response time: 500ms - 2s")
        print("   💡 Consider adding caching for better performance")

if __name__ == '__main__':
    test_dashboard_query_performance()
