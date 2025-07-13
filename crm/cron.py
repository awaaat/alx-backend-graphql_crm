# File: crm/cron.py
"""
Cron job for updating low-stock products in alx-backend-graphql_crm.

Requirements:
- Execute UpdateLowStockProducts GraphQL mutation to find products with quantity < 10 and increment by 10.
- Log updated product names and new stock levels to /tmp/low_stock_updates_log.txt with timestamps.
- Scheduled to run every 12 hours (0:00 and 12:00) via CRONJOBS in crm/settings.py.
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime

# Configure logging to /tmp/low_stock_updates_log.txt
LOG_FILE = Path('/tmp/low_stock_updates_log.txt')
LOG_FILE.touch(exist_ok=True)  # Ensure log file exists
LOG_FILE.chmod(0o666)  # Ensure writable by all users
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),  # Log to console for debugging
    ],
)
logger = logging.getLogger(__name__)

# GraphQL endpoint configuration
GRAPHQL_URL = os.getenv('GRAPHQL_URL', 'http://localhost:8000/graphql')

def setup_django() -> None:
    """
    Set up Django environment for GraphQL integration.

    Adds project path to sys.path and sets DJANGO_SETTINGS_MODULE.
    Exits with error if setup fails, logging to /tmp/low_stock_updates_log.txt.
    """
    try:
        PROJECT_PATH = os.getenv(
            'DJANGO_PROJECT_PATH',
            '/media/allano/53CE082D539E52ED/_pD_BE/alx_backend_graphql_crm/alx_backend_graphql_crm'
        )
        sys.path.append(PROJECT_PATH)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
        import django
        django.setup()
    except Exception as e:
        logger.error(f"Failed to set up Django: {str(e)}")
        sys.exit(1)

def rotate_log_file(log_file: Path, max_size: int = 10 * 1024 * 1024) -> None:
    """
    Rotate log file if it exceeds max_size bytes.

    Renames the log file with a timestamp suffix if size exceeds 10MB.
    Logs rotation success or failure.
    """
    try:
        if log_file.exists() and log_file.stat().st_size > max_size:
            backup_file = log_file.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            log_file.rename(backup_file)
            logger.info(f"Rotated log file to {backup_file}")
    except Exception as e:
        logger.error(f"Failed to rotate log file {log_file}: {str(e)}")

def update_low_stock() -> None:
    """
    Execute UpdateLowStockProducts mutation and log updated products.

    Requirements:
    - Query GraphQL endpoint to update products with quantity < 10.
    - Log each updated product's name and new stock level to /tmp/low_stock_updates_log.txt.
    - Handle errors and empty results with appropriate logging.
    - Called every 12 hours via django-crontab.
    """
    # Rotate log file if needed
    rotate_log_file(LOG_FILE)

    logger.info("Starting low-stock product update")

    try:
        # Initialize GraphQL client
        transport = RequestsHTTPTransport(url=GRAPHQL_URL, timeout=10)
        client = Client(transport=transport)

        # Define GraphQL mutation
        mutation = gql(
            """
            mutation {
                updateLowStockProducts {
                    products {
                        productId
                        name
                        quantity
                    }
                    success
                    message
                }
            }
            """
        )

        # Execute mutation
        result = client.execute(mutation)
        update_data = result.get('updateLowStockProducts', {})
        products = update_data.get('products', [])
        success = update_data.get('success', False)
        message = update_data.get('message', 'No message')

        if not success:
            logger.error(f"Mutation failed: {message}")
            return

        if not products:
            logger.warning("No low-stock products found to update")
            return

        # Log each updated product
        for product in products:
            name = product.get('name', 'Unknown')
            quantity = product.get('quantity', 0)
            product_id = product.get('productId', 'Unknown')
            logger.info(f"Updated product: {name} (ID: {product_id}), New stock: {quantity}")

        logger.info(f"Processed {len(products)} low-stock product updates")

    except Exception as e:
        logger.error(f"Failed to execute mutation: {str(e)}")

if __name__ == '__main__':
    setup_django()
    update_low_stock()