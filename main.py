import logging
from app.src import scrape
from datetime import datetime, timedelta

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    today = datetime.now()
    start_date = today - timedelta(days=365)
    
    # Run the main scraping logic
    scrape(start_date.strftime("%Y-%m-%d"), "NOW")

if __name__ == "__main__":
    main()
