import arxiv
import os
from pathlib import Path
from config import config_from_json
import logging
from utils.found_paper import FoundPaper

MAX_TITLE_LENGTH = 50

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scraper.log"),  # Logs to scraper.log file
        logging.StreamHandler(),  # Also logs to stdout
    ],
)

def process_paper(found_paper: FoundPaper):
    #TODO: form query from abstract
    #TODO: send to gpt service
    is_relevant = False
    
    if not is_relevant:
        return False
    
    #TODO: form query for the entire paper
    #TODO: send to gpt service
    summary = None
    is_relevant = False
    if not is_relevant:
        return False
    
    #TODO: Generate the summary you want to send by mail
    #TODO: Add this to the summary string
    #TODO: Send this to the email microservice
    
    return True

def scrape(search_query, output_dir, page_size=5, delay_seconds=3, num_retries=3):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logging.info(f"Starting scraping process with query: {search_query}")

    # Initialize the client
    client = arxiv.Client(
        page_size=page_size,
        delay_seconds=delay_seconds,
        num_retries=num_retries,
    )

    # Create the search
    search = arxiv.Search(
        query=search_query,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    # Fetch results using the client
    results = client.results(search)

    # Track the number of papers retrieved
    result_count = 0
    summaries_string = ""

    # Iterate over the search results and log them
    for result in results:
        result_count += 1
        logging.info(f"Found the paper {result.title}")

        # Define the path to save the PDF
        sanitized_title = (
            result.title[:MAX_TITLE_LENGTH].replace(" ", "_").replace("/", "_")
        )
        pdf_filename = f"{result.get_short_id()}_{sanitized_title}.pdf"
        pdf_path = Path(output_dir) / pdf_filename

        # Download the PDF
        result.download_pdf(filename=pdf_path)
        logging.info(f"Downloaded PDF to: {pdf_path}\n")

        found_paper = FoundPaper(
            title=result.title,
            authors=[author.name for author in result.authors],
            published=result.published.strftime("%Y-%m-%d"),
            summary=result.summary,
            pdf_path=str(pdf_path),
        )
        
        if not process_paper(found_paper):
            continue
        

    # Check if any results were found
    if result_count == 0:
        logging.warning("No papers were found for the given query.")
    else:
        logging.info(f"Total papers found: {result_count}")


if __name__ == "__main__":
    cfg = config_from_json("config.json", read_from_file=True)
    search_query = cfg["search_query"]
    output_dir = cfg["output_dir"]

    scrape(search_query, output_dir)
