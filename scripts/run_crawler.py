# scripts/run_crawler.py

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler.raw_crawler import RawCrawler
from src.database.db_manager import DatabaseManager
from src.utils.config import MONGODB_URI, LOG_FORMAT, LOG_FILE

def setup_logging():
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create a log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = LOG_FILE.replace('.log', f'_{timestamp}.log')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

async def main():
    """Main function to run the crawler."""
    start_time = datetime.now()
    logger = logging.getLogger('main')
    
    try:
        logger.info("Starting laptop data collection")
        
        # Initialize database manager
        db_manager = DatabaseManager(MONGODB_URI)
        
        # Initialize and run crawler
        crawler = RawCrawler(db_manager)
        await crawler.run()
        
        # Log completion statistics
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Crawling completed in {duration}")
        
        # Cleanup
        await db_manager.close()
        
    except Exception as e:
        logger.error(f"Error running crawler: {str(e)}")
        raise
    finally:
        logger.info("Crawler process finished")

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    
    # Run the crawler
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Crawler stopped by user")
    except Exception as e:
        logging.error(f"Crawler failed: {str(e)}")
        sys.exit(1)