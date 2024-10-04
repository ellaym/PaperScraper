import arxiv
import os
import time
import logging
import requests
from pathlib import Path
from config import config_from_json
from utils.found_paper import FoundPaper
from datetime import datetime

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

# Load config for microservice URLs and ports
cfg = config_from_json("config.json", read_from_file=True)
GPT_MICROSERVICE_URL = f"http://localhost:{cfg['gpt_service_port']}/query"
EMAIL_MICROSERVICE_URL = f"http://localhost:{cfg['email_service_port']}/send"
EMAIL_RECIPIENT = cfg['email_recipient']

# Function to query GPT microservice
def query_gpt(content, retries=3, timeout=10):
    """Function to send a query to the GPT microservice with retries and a timeout."""
    payload = {"query": content}
    for attempt in range(retries):
        try:
            response = requests.post(GPT_MICROSERVICE_URL, json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json().get("output", "")
        except requests.exceptions.RequestException as e:
            logging.error(f"Attempt {attempt + 1} failed querying GPT: {str(e)}")
            if attempt + 1 == retries:
                logging.error(f"All retries failed for GPT service.")
                return None
        time.sleep(2)  # Wait before retrying

# Function to send an email via the email microservice
def send_email_via_microservice(to_email, subject, message):
    """Function to send an email via the email microservice with error handling."""
    payload = {"email": to_email, "subject": subject, "message": message}
    try:
        response = requests.post(EMAIL_MICROSERVICE_URL, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Email sent successfully to {to_email}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending email: {str(e)}")

# Function to process papers and return summary of relevant ones
def process_paper(found_paper: FoundPaper):
    """Process a paper: query GPT for relevance and return summary if relevant."""
    logging.info(f"Processing paper: {found_paper.title}")
    gpt_response = query_gpt(found_paper.summary)

    if not gpt_response:
        logging.warning(f"Skipping paper '{found_paper.title}' due to no GPT response.")
        return None

    # Check if GPT indicates that the paper is relevant
    is_relevant = "relevant" in gpt_response.lower()
    if not is_relevant:
        logging.info(f"Paper '{found_paper.title}' is not relevant based on GPT response.")
        return None

    # Generate the summary for relevant paper
    summary = (
        f"Title: {found_paper.title}\n"
        f"Authors: {', '.join(found_paper.authors)}\n"
        f"Published: {found_paper.published}\n"
        f"Summary: {found_paper.summary}\n"
        f"GPT Analysis: {gpt_response}\n"
    )

    return summary

# Function to scrape papers from Arxiv
def scrape(search_query, output_dir, page_size=5, delay_seconds=3, num_retries=3):
    """Scrape papers from Arxiv using the provided query and send one summary email at the end."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logging.info(f"Starting scraping process with query: {search_query}")

    # Initialize the Arxiv client
    client = arxiv.Client(
        page_size=page_size,
        delay_seconds=delay_seconds,
        num_retries=num_retries,
    )

    # Create the search object
    search = arxiv.Search(
        query=search_query,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    # Fetch the search results
    results = client.results(search)
    result_count = 0
    relevant_papers_summary = []  # List to accumulate relevant paper summaries

    # Process each paper found in the results
    for result in results:
        result_count += 1
        
        logging.info(f"Found paper: {result.title}")

        # Save the PDF with a sanitized title
        sanitized_title = result.title[:MAX_TITLE_LENGTH].replace(" ", "_").replace("/", "_")
        pdf_filename = f"{result.get_short_id()}_{sanitized_title}.pdf"
        pdf_path = Path(output_dir) / pdf_filename

        # Download the paper's PDF
        result.download_pdf(filename=pdf_path)
        logging.info(f"Downloaded PDF to: {pdf_path}\n")

        found_paper = FoundPaper(
            title=result.title,
            authors=[author.name for author in result.authors],
            published=result.published.strftime("%Y-%m-%d"),
            summary=result.summary,
            pdf_path=str(pdf_path),
        )

        # Process the paper and append relevant summaries
        paper_summary = process_paper(found_paper)
        if paper_summary:
            relevant_papers_summary.append(paper_summary)

        # Wait between requests to avoid overloading the Arxiv API
        time.sleep(delay_seconds)

    # Check if any relevant papers were found
    if relevant_papers_summary:
        logging.info(f"Total relevant papers found: {len(relevant_papers_summary)}")
        # Send a single email with all relevant papers
        all_summaries = "\n".join(relevant_papers_summary)
        send_email_via_microservice(
            to_email=EMAIL_RECIPIENT,
            subject=f"Relevant Papers Found on {datetime.now().strftime('%Y-%m-%d')}",
            message=all_summaries
        )
    else:
        logging.info("No relevant papers found.")

    # Log the total results
    if result_count == 0:
        logging.warning("No papers were found for the given query.")
    else:
        logging.info(f"Total papers found: {result_count}")

if __name__ == "__main__":
    # Load configuration from config.json
    cfg = config_from_json("config.json", read_from_file=True)
    search_query = cfg["search_query"]
    output_dir = cfg["output_dir"]

    scrape(search_query, output_dir)
