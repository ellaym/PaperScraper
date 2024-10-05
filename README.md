# PaperScraper

**PaperScraper** is a Dockerized microservice-based system designed to retrieve academic papers from various sources like ArXiv, summarize them using GPT, and send the results via email. The project uses multiple microservices to achieve its functionality, including `EmailService`, `GPTService`, and `PaperRetrievalService`.

## Features
- **Retrieve academic papers**: Automatically fetch academic papers from sources like ArXiv using multiple retrievers.
- **Summarization with GPT**: Summarize retrieved papers using a GPT-based microservice.
- **Email notifications**: Automatically send summaries and download links via email.
- **Microservice architecture**: Built using Flask microservices for modularity and scalability.
- **Dockerized**: Each service is containerized using Docker for easy deployment.

## Project Structure

```bash
PaperScraper/
├── app/
│   ├── config.json                # Configuration file for PaperScraper
│   ├── logs/                      # Log files
│   ├── src/                       # Source code for PaperScraper
│   │   ├── paper_scraper.py        # Main scraping logic
│   │   ├── utils/                  # Utility functions and helpers
│   │   └── main.py                 # Entry point for PaperScraper
│   └── requirements.txt            # Python dependencies for PaperScraper
├── services/                      # Microservices
│   ├── EmailService/
│   │   ├── Dockerfile              # Dockerfile for EmailService
│   │   └── main.py                 # Main logic for EmailService
│   ├── GPTService/
│   │   ├── Dockerfile              # Dockerfile for GPTService
│   │   └── main.py                 # Main logic for GPTService
│   └── PaperRetrievalService/
│       ├── Dockerfile              # Dockerfile for PaperRetrievalService
│       └── main.py                 # Main logic for PaperRetrievalService
├── Dockerfile                      # Dockerfile for PaperScraper
├── docker-compose.yml              # Docker Compose file to run all services
└── README.md                       # This README file
```

## Requirements
- **Docker**
- **Docker Compose**

## Setup Instructions

### 1. Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/ellaym/PaperScraper.git
cd PaperScraper
```

### 2. Build and Run the Service with Docker Compose
Use Docker Compose to build and run the services:
```bash
docker-compose up --build
```

This command will:
- Build the Docker images for each microservice.
- Start the services (`PaperScraper`, `EmailService`, `GPTService`, and `PaperRetrievalService`).
- Expose the services on their respective ports.

### 3. Access the Services

#### PaperScraper
The main `PaperScraper` service will be available on:
```
http://localhost:5000
```

#### PaperRetrievalService
You can query the `PaperRetrievalService` via:
```
http://localhost:5502/retrieve_papers
```

**Example request** (via `curl`):
```bash
curl -X POST http://localhost:5502/retrieve_papers   -H "Content-Type: application/json"   -d '{
        "search_query": "cat:cs.CR OR cat:cs.DS",
        "output_dir": "./shared_data",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
      }'
```

### 4. Dynamic Configuration of Retrievers
`PaperRetrievalService` supports dynamic configuration of retrievers using the `retrievers_config.json` file located in the `services/PaperRetrievalService` directory. 

Example `retrievers_config.json`:
```json
{
  "retrievers": {
    "arxiv": "libs.PaperRetrievalService.arxiv_retriever.ArxivRetriever"
  }
}
```

### 5. Stop the Services
To stop the Docker containers, run:
```bash
docker-compose down
```

## Microservices

### 1. PaperRetrievalService
- Retrieves papers from sources like ArXiv.
- Configurable retrievers for different paper sources.
- Communicates with the `PaperScraper` service.

### 2. GPTService
- Summarizes the retrieved papers using GPT.
- Receives queries from the `PaperScraper` service.

### 3. EmailService
- Sends email notifications with summaries and download links.
- Receives instructions from the `PaperScraper` service.

## Contributing
Feel free to open issues or submit pull requests if you have suggestions or improvements.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.
