# Use official Python base image from DockerHub
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Set PYTHONPATH to /app so that imports work consistently
ENV PYTHONPATH=/app

# Copy the requirements.txt from the PaperScraper project into the container
COPY ./app/requirements.txt /app/requirements.txt

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the PaperScraper source directory into the container
COPY ./app/ /app/app/

# Copy the main.py file into the working directory
COPY main.py /app/main.py

# Expose any necessary ports (optional)
EXPOSE 5000

# Set the default command to run the paper scraper
CMD ["python", "/app/main.py"]
