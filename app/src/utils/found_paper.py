import json


class FoundPaper:
    """
    Represents a found paper.

    Attributes:
        title (str): The title of the paper.
        authors (str): The authors of the paper.
        published (str): The publication date of the paper.
        summary (str): The summary of the paper.
        pdf_path (str): The file path of the PDF version of the paper.
    """

    def __init__(self, title, authors, published, summary, pdf_path):
        self.title = title
        self.authors = authors
        self.published = published
        self.summary = summary
        self.pdf_path = pdf_path

    def __str__(self):
        return (
            f"Title: {self.title}\n"
            f"Authors: {', '.join(self.authors)}\n"
            f"Published: {self.published}\n"
        )
