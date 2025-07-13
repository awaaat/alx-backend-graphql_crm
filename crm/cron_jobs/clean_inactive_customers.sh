#!/bin/bash
cd /media/allano/53CE082D539E52ED/_pD_BE/alx_backend_graphql_crm

touch customer_cleanup_log.txt
chmod 666 customer_cleanup_log.txt

python3 manage.py shell -c "
import sys
from datetime import timedelta
from django.utils import timezone
from django.db.models import Exists, OuterRef
from crm.models import Customer, Order

try:
    one_year_ago = timezone.now() - timedelta(days=365)
    recent_orders = Order.objects.filter(customer=OuterRef('pk'), order_date__gte=one_year_ago)
    inactive_customers = Customer.objects.annotate(has_recent_orders=Exists(recent_orders)).filter(has_recent_orders=False)
    count = inactive_customers.count()
    with open('customer_cleanup_log.txt', 'a') as f:
        f.write(f'{timezone.now()}: Found {count} inactive customers\n')
    inactive_customers.delete()
    with open('customer_cleanup_log.txt', 'a') as f:
        f.write(f'{timezone.now()}: Deleted {count} inactive customers\n')
except Exception as e:
    with open('customer_cleanup_log.txt', 'a') as f:
        f.write(f'{timezone.now()}: Error - {str(e)}\n')
    sys.exit(1)
"