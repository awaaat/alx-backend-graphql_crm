# File: crm/cron.py
import logging
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.db import connection
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configure logging for low stock updates
log_file = Path('/tmp/low_stock_updates_log.txt')
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(),
    ]
)

def rotate_log_file(log_file: Path, max_size: int = 10 * 1024 * 1024) -> None:
    """Rotate log file if it exceeds max_size bytes."""
    try:
        if log_file.exists() and log_file.stat().st_size > max_size:
            backup_file = log_file.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            log_file.rename(backup_file)
            logger.info(f"Rotated log file to {backup_file}")
    except Exception as e:
        logger.error(f"Failed to rotate log file {log_file}: {str(e)}")

def update_low_stock() -> None:
    """Execute GraphQL mutation to update low-stock products every 12 hours."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"{timestamp} - Starting low-stock products update")

    try:
        transport = RequestsHTTPTransport(url=settings.CRON_CONFIG['GRAPHQL_URL'], timeout=10)
        client = Client(transport=transport)
        mutation = gql(
            """
            mutation {
                updateLowStockProducts {
                    products {
                        id
                        name
                        quantity
                    }
                    success
                    message
                }
            }
            """
        )
        result = client.execute(mutation)
        mutation_result = result.get('updateLowStockProducts', {})

        with log_file.open('a') as f:
            f.write(f"{timestamp}: Stock update started\n")
            if mutation_result.get('success'):
                message = mutation_result.get('message', 'No message provided')
                f.write(f"{timestamp}: {message}\n")
                for product in mutation_result.get('products', []):
                    product_id = product.get('id')
                    product_name = product.get('name')
                    new_quantity = product.get('quantity')
                    f.write(f"{timestamp}: Updated {product_name} (ID: {product_id}) - New quantity: {new_quantity}\n")
                logger.info(f"{timestamp} - Successfully updated {len(mutation_result.get('products', []))} products")
            else:
                error_message = mutation_result.get('message', 'Unknown error')
                f.write(f"{timestamp}: Stock update failed - {error_message}\n")
                logger.error(f"{timestamp} - Stock update failed: {error_message}")

    except Exception as e:
        with log_file.open('a') as f:
            f.write(f"{timestamp}: Error - {str(e)}\n")
        logger.error(f"{timestamp} - Failed to execute stock update mutation: {str(e)}")
        # TODO: Integrate with alerting system (e.g., Sentry, email)