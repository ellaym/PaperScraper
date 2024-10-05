import os
import time
import logging
import requests
from pathlib import Path
from config import config_from_json
from .utils.found_paper import FoundPaper
from datetime import datetime
from PyPDF2 import PdfReader  # Add this import to read PDFs

MAX_TITLE_LENGTH = 50

# Setup logging configuration
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{log_dir}/scraper.log"),  # Logs to scraper.log file
        logging.StreamHandler(),  # Also logs to stdout
    ],
)

# Load config for microservice URLs and ports
cfg = config_from_json("app/config.json", read_from_file=True)
GPT_MICROSERVICE_URL = f"http://{cfg['gpt_service_host']}:{cfg['gpt_service_port']}/query"
EMAIL_MICROSERVICE_URL = f"http://{cfg['email_service_host']}:{cfg['email_service_port']}/send"
PAPER_RETRIEVAL_MICROSERVICE_URL = (
    f"http://{cfg['paper_retrieval_service_host']}:{cfg['paper_retrieval_service_port']}/retrieve_papers"
)
EMAIL_RECIPIENT = cfg["email_recipient"]
RELEVANCE_QUERY = cfg["relevance_query"]
SUMMARY_QUERY = cfg["summary_query"]
SEARCH_QUERY = cfg["search_query"]
OUTPUT_DIR = cfg["output_dir"]


# Function to query GPT microservice
def query_gpt(content, retries=100, timeout=20):
    """Function to send a query to the GPT microservice with retries and a timeout."""
    payload = {"query": content}
    for attempt in range(retries):
        try:
            response = requests.post(
                GPT_MICROSERVICE_URL, json=payload, timeout=timeout
            )
            response.raise_for_status()
            return response.json().get("output", "")
        except requests.exceptions.RequestException as e:
            logging.error(f"Attempt {attempt + 1} failed querying GPT: {str(e)}")
            if attempt + 1 == retries:
                logging.error(f"All retries failed for GPT service.")
                return None
        time.sleep(2)  # Wait before retrying


def send_email_via_microservice(to_email, subject, message):
    """Function to send an email via the email microservice with error handling."""
    payload = {"email": to_email, "subject": subject, "message": message}
    try:
        response = requests.post(EMAIL_MICROSERVICE_URL, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Email sent successfully to {to_email}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending email: {str(e)}")


def extract_text_from_pdf(pdf_path):
    """Extract the entire text content from a PDF."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""  # Extract text from each page
        return text
    except Exception as e:
        logging.error(f"Failed to extract text from {pdf_path}: {str(e)}")
        return None


def process_paper(found_paper: FoundPaper):
    """Process a paper: query GPT for relevance, and if relevant, get a full summary."""
    logging.info(f"Processing paper: {found_paper.title}")

    # 1. Check for relevance with the summary (abstract)
    relevance_query = f"{RELEVANCE_QUERY}: {found_paper.summary}"
    gpt_relevance_response = query_gpt(relevance_query)

    if not gpt_relevance_response:
        logging.warning(f"Skipping paper '{found_paper.title}' due to no GPT response.")
        return None

    # TODO: find a better logic for relevance (based on GPT query)
    # if "relevant" not in gpt_relevance_response.lower():
    #    logging.warning(f"Skipping paper '{found_paper.title}' since GPT decided it's not relevant.")
    #    return None

    # 2. Extract the entire PDF content
    paper_text = extract_text_from_pdf(found_paper.pdf_path)
    if not paper_text:
        logging.warning(
            f"Skipping paper '{found_paper.title}' due to failure in extracting PDF content."
        )
        return None

    # 3. Generate the full summary by sending the entire text to GPT
    # TODO: You can currently send only a portion of the paper if the text is too large for GPT.
    summary_query = f"{SUMMARY_QUERY}: {found_paper.summary}"
    gpt_summary_response = query_gpt(summary_query)

    if not gpt_summary_response:
        logging.warning(
            f"Failed to generate a summary for paper '{found_paper.title}'."
        )
        return None

    # 4. Generate the summary for the relevant paper
    final_summary = str(found_paper) + f"GPT Summary: {gpt_summary_response}\n"

    return final_summary


# Function to interact with the PaperRetrievalService microservice
def call_paper_retrieval_microservice(start_date, end_date, retries=100, timeout=10):
    """Call the PaperRetrievalService microservice to retrieve papers."""
    payload = {
        "search_query": SEARCH_QUERY,
        "output_dir": OUTPUT_DIR,
        "start_date": start_date,
        "end_date": end_date,
    }

    for attempt in range(retries):
        try:
            response = requests.post(
                PAPER_RETRIEVAL_MICROSERVICE_URL, json=payload, timeout=timeout
            )
            response.raise_for_status()
            return response.json().get(
                "papers_metadata", []
            )  # Get metadata for all papers
        except requests.exceptions.RequestException as e:
            logging.error(
                f"Attempt {attempt + 1} failed querying PaperRetrievalService: {str(e)}"
            )
            if attempt + 1 == retries:
                logging.error(f"All retries failed for PaperRetrievalService.")
                return []
        time.sleep(2)  # Wait before retrying


def scrape(start_date, end_date):
    """Call the PaperRetrievalService microservice and process the retrieved papers."""
    # Call the PaperRetrievalService microservice to retrieve the papers
    papers_metadata = call_paper_retrieval_microservice(start_date, end_date)

    if not papers_metadata:
        logging.info("No papers were retrieved by the PaperRetrievalService.")
        return

    relevant_papers_summary = []  # List to accumulate relevant paper summaries

    # Process each paper with its metadata
    for paper_data in papers_metadata:
        pdf_path = paper_data["file_path"]
        title = paper_data["title"]
        authors = paper_data["authors"]
        summary = paper_data["summary"]

        logging.info(f"Processing downloaded file: {pdf_path}")

        found_paper = FoundPaper(
            title=title,
            authors=authors,
            published=str(
                datetime.now().date()
            ),  # Placeholder, use actual publication date if available
            summary=summary,
            pdf_path=pdf_path,
        )

        # Process the paper and append relevant summaries
        paper_summary = process_paper(found_paper)
        if paper_summary:
            relevant_papers_summary.append(paper_summary)

    # Check if any relevant papers were found
    if relevant_papers_summary:
        logging.info(f"Total relevant papers found: {len(relevant_papers_summary)}")
        # Send a single email with all relevant papers
        all_summaries = "\n".join(relevant_papers_summary)
        send_email_via_microservice(
            to_email=EMAIL_RECIPIENT,
            subject=f"Relevant Papers Found on {datetime.now().strftime('%Y-%m-%d')}",
            message=all_summaries,
        )
    else:
        logging.info("No relevant papers found.")