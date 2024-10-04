import json

class FoundPaper():
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
    
    def serialize(self):
        """
        Serializes the paper object into a JSON string for a POST request.

        Returns:
            str: A JSON string containing the serialized paper data.
        """
        return json.dumps({
            "title": self.title,
            "authors": self.authors,
            "published": self.published,
            "summary": self.summary,
            "pdf_path": self.pdf_path
        })

    @staticmethod
    def deserialize(data):
        """
        Deserializes the paper data from a dictionary.

        Args:
            data (dict): A dictionary containing the paper data.

        Returns:
            FoundPaper: A FoundPaper object created from the deserialized data.
        """
        return FoundPaper(
            title=data["title"],
            authors=data["authors"],
            published=data["published"],
            summary=data["summary"],
            pdf_path=data["pdf_path"]
        )
