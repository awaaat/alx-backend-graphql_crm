#!/usr/bin/env python
# File: crm/cron_jobs/send_order_reminders.py

"""
Instructions for Future Reference:

1. **Objective**
   Create a Python script that uses a GraphQL query to find pending orders 
   (order_date within the last week) and logs reminders, scheduled to run 
   daily using a cron job.

2. **Create a Python Script**:
   - Filename: `send_order_reminders.py` in `crm/cron_jobs`.
   - The script should:
     - Use the gql library to query the GraphQL endpoint (http://localhost:8000/graphql)
       for orders with `order_date` within the last 7 days.
     - Log each order’s ID and customer email to `/tmp/order_reminders_log.txt` 
       with a timestamp.
     - Print `"Order reminders processed!"` to the console.

3. **Create a Crontab Entry**:
   - File: `crm/cron_jobs/order_reminders_crontab.txt`
   - Content: a single line to run the script daily at 8:00 AM.
   - Format:
     ```
     0 8 * * * /usr/bin/env python /full/path/to/crm/cron_jobs/send_order_reminders.py
     ```
   - Ensure no extra newlines.
"""


# File: crm/cron_jobs/send_order_reminders.py
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

# Configure logging
LOG_FILE = Path('/tmp/order_reminders_log.txt')
LOG_FILE.touch(exist_ok=True)  # Ensure file exists
LOG_FILE.chmod(0o666)  # Ensure writable
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Environment configuration
PROJECT_PATH = os.getenv('DJANGO_PROJECT_PATH', '/media/allano/53CE082D539E52ED/_pD_BE/alx_backend_graphql_crm/alx_backend_graphql_crm')
GRAPHQL_URL = os.getenv('GRAPHQL_URL', 'http://localhost:8000/graphql')

def setup_django() -> None:
    """Set up Django environment."""
    try:
        sys.path.append(PROJECT_PATH)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
        import django
        django.setup()
    except Exception as e:
        logger.error(f"Failed to setup Django: {str(e)}")
        sys.exit(1)

def query_pending_orders() -> List[Dict]:
    """Query GraphQL for orders from the last 7 days."""
    try:
        transport = RequestsHTTPTransport(url=GRAPHQL_URL, timeout=10)
        client = Client(transport=transport)
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        query = gql(
            """
            query GetRecentOrders($dateぐ: String!) {
                orders(orderDate_Gte: $date) {
                    id
                    orderDate
                    customer {
                        email
                    }
                }
            }
            """
        )
        result = client.execute(query, variable_values={'date': seven_days_ago})
        return result.get('orders', [])
    except Exception as e:
        logger.error(f"GraphQL query failed: {str(e)}")
        return []

def send_order_reminders() -> None:
    """Process and log order reminders for pending orders."""
    logger.info("Starting order reminders processing")
    orders = query_pending_orders()
    if not orders:
        logger.warning("No orders found in the last 7 days")
        print("Order reminders processed!")
        return

    for order in orders:
        order_id = order.get('id')
        customer_email = order.get('customer', {}).get('email', 'Unknown')
        logger.info(f"Order ID: {order_id}, Customer: {customer_email}")

    logger.info(f"Processed {len(orders)} order reminders")
    print("Order reminders processed!")

if __name__ == '__main__':
    setup_django()
    send_order_reminders()
