#!/usr/bin/env python
# File: crm/cron_jobs/send_order_reminders.py
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from gql import Client, gql # type: ignore
from gql.transport.requests import RequestsHTTPTransport # type: ignore

# Configure logging
LOG_FILE = Path('/tmp/order_reminders_log.txt')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
            query GetRecentOrders($date: String!) {
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
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"{timestamp} - Starting order reminders processing")

    orders = query_pending_orders()
    if not orders:
        logger.warning(f"{timestamp} - No orders found in the last 7 days")
        print("Order reminders processed!")
        return

    for order in orders:
        order_id = order.get('id')
        customer_email = order.get('customer', {}).get('email', 'Unknown')
        log_message = f"{timestamp} - Order ID: {order_id}, Customer: {customer_email}"
        logger.info(log_message)

    logger.info(f"{timestamp} - Processed {len(orders)} order reminders")
    print("Order reminders processed!")

if __name__ == '__main__':
    setup_django()
    send_order_reminders()