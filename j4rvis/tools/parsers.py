import re
import json
from typing import Dict, Any

def parse_input(text: str) -> Dict[str, Any]:
    """Parse the json string into a dict."""
    return json.loads(text)


def clean_url(url: str) -> str:
    """Strips quotes from the url."""
    return url.strip("\"'")

def remove_code_block(code_txt: str) -> str:
    # Define regex patterns for the different markdown code markers
    patterns = [r"^```(?:py|python)\n(.*?)\n```\s*$"]

    for pattern in patterns:
        # Search for the pattern in the input string
        match = re.search(pattern, code_txt, re.DOTALL)

        if match:
            # Return the matched code without the markdown code markers
            return match.group(1)

    # If no markdown code markers are found, return the original string
    return code_txt