import pdfkit
import json


def html_to_pdf_runner(input):
    """
    This function converts an HTML and CSS file to a PDF file.
    Input is a JSON object with two keys 'html' and 'css', both strings indicating the paths to the files.
    'output' key is optional and specifies the output PDF file path. If not provided, output.pdf will be used.
    """

    # Extract data from input
    try:
        data = json.loads(input)
        html_path = data.get("html")
        css_path = data.get("css")
        output_path = data.get("output", "output.pdf")
    except (KeyError, json.JSONDecodeError):
        raise ValueError(
            "Invalid input. Please provide 'html' and 'css' paths in the input JSON."
        )

    # Options for pdfkit, including the CSS file
    options = {
        "quiet": "",
        "print-media-type": "",
        "no-outline": None,
        "encoding": "UTF-8",
    }

    if css_path:
        options["user-style-sheet"] = css_path

    # Convert the HTML file to PDF
    try:
        pdfkit.from_file(html_path, output_path, options=options)
        return f"PDF successfully created at {output_path}"
    except Exception as e:
        return str(e)
