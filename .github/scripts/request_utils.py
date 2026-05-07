import requests
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Base URLs configuration
BASE_URLS = {
    "publication": os.getenv("BASE_URL_PUBLICATION", "https://api.crossref.org/works/"),
    "software": os.getenv("BASE_URL_SOFTWARE", "https://doi.org/"),
    "organization": os.getenv(
        "BASE_URL_ORGANIZATION", "https://api.ror.org/organizations/"
    ),
    "author": os.getenv("BASE_URL_AUTHOR", "https://pub.orcid.org/v3.0/"),
}

# Default timeout
TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", 10))
MAX_RETRIES = 3

# Configure retries
_retry_strategy = Retry(
    total=MAX_RETRIES,
    status_forcelist=[ 429, 500, 502, 503, 504],  # Specify which status codes to retry on
    allowed_methods=[ "HEAD", "GET", "OPTIONS"],  # Use `allowed_methods` for urllib3 v1.26.0 or later
    backoff_factor=1,  # Defines the delay between retries
)

_adapter = HTTPAdapter(max_retries=_retry_strategy)
session = requests.Session()
session.mount("http://", _adapter)
session.mount("https://", _adapter)

def get_record(record_type, record_id):
    """
    Fetch record "metadata" from a remote API.

    Attempts to retrieve metadata by constructing a URL from the provided
    record type and ID, then trying multiple content types in order
    (``application/ld+json``, then ``application/json``). Returns on the
    first successful response.

    Parameters
    ----------
    record_type : str
       Must be defined in BASE_URLS ['publication', 'software', organization', 'author'] 

    record_id : str
        The identifier of the record to be appended to the base URL.

    Returns
    -------
    metadata : dict
        The JSON response from the API, or an empty dict if all
        attempts failed.
    log : str
        A string accumulating informational and warning messages generated
        during the fetch process.

    Raises
    ------
    ValueError
        If ``record_type`` is not a key in ``BASE_URLS``.
    """

    log = ""

    if record_type not in BASE_URLS:
        raise ValueError(f"Record type `{record_type}` not supported")

    url = BASE_URLS[record_type] + record_id
    print(url)

    for content_type in ["application/ld+json", "application/json"]:
        headers = {"Content-Type": content_type, "Accept": content_type}

        try:
            response = session.get(
                url, headers=headers, timeout=TIMEOUT, allow_redirects=True
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            # If the response is successful and contains content, parse and return the metadata
            if response.content:
                return response.json(), log

        except requests.exceptions.RequestException as e:
            log += f"Could not fetch metadata with {content_type} from {url}: {e}\n\n"

    # Failed to fetch record
    log += f"Failed to fetch metadata with All content types or URL.\n"
    return {}, log

def search_organization(org_url):
    """
    BY_AI: Search the org_url against the ROR (Research Organization Registry).

    Strips the URL scheme and any trailing slash before querying the ROR
    advanced search endpoint. If exactly one result is returned it is used
    directly; if multiple results are found the first is used and a warning
    is raised. Parent-organization relationships are noted in the log.

    Parameters
    ----------
    org_url : str
        The website URL of the organization to look up
        (e.g. ``"https://www.monash.edu/"``).

    Returns
    -------
    ror_id : str
        The ROR identifier URL for the matched organization
        (e.g. ``"https://ror.org/02bfwt286"``), or an empty string if no
        match was found.
    log : str
        A string accumulating informational and warning messages generated
        during the search process.
    """

    log = ""
    ror_id = ""
    result = {}

    base_url = "https://api.ror.org/organizations"
    org_url = org_url.split("://")[-1]

    # Check if last character is a '/' and if so drop it
    if org_url[-1] == "/":
        org_url = org_url[:-1]

    url = base_url + "?query.advanced=links:" + org_url
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        result = response.json()

    except requests.exceptions.RequestException as e:
        log += f"Failed fetching metadata: {e} \n"

    # Deal with response and determine ROR ID
    if result["number_of_results"] == 0:
        log += f"Unable to find ROR for {org_url} \n"
    elif result["number_of_results"] == 1:
        ror_id = result["items"][0]["id"]
        log += f"Found ROR record for {org_url}: {result['items'][0]['name']} ({ror_id}) \n"
        for relation in result["items"][0]["relationships"]:
            if relation["type"] == "Parent":
                log += f"Note: This organization has a parent organization: {relation['label']} ({relation['id']}) \n"
    else:
        ror_id = result["items"][0]["id"]
        log += f"Found more than one ROR record for {org_url}. Assuming the first result is correct; if not please enter the correct ROR. \n"
        for record in result["items"]:
            log += f"\t - {record['name']} ({record['id']}) \n"

    return ror_id, log


def check_uri(uri):
    """
    BY_AI: Checks whether the given URI is reachable via an HTTP GET request.

    Sends an HTTP GET request to the URI and raises an exception for any HTTP error
    status code. Returns 'OK' if the request succeeds, otherwise returns a string
    description of the error.

    Parameters:
        uri (str): The URI to check.

    Returns:
        str: 'OK' if the URI is reachable and returned a success status, otherwise a
            string describing the error that occurred.
    """
    try:
        response = requests.get(uri)
        response.raise_for_status()  # Raise an exception for HTTP errors

        return "OK"

    except Exception as err:
        # return err.args[0]
        return str(
            err
        )  # 01/05/24: Convert the error to a string to avoid TypeError when we concatenate to log


def download_license_text(url):
    """
    BY_AI: Downloads and returns the plain-text content of a license from the given URL.

    Sends an HTTP GET request to the provided URL. If the response status is 200, the
    response body is returned as a string. If the request fails or returns a non-200
    status, a fallback message directing the reader to the RO-Crate metadata file is
    returned instead.

    Parameters:
        url (str): The URL from which to download the license text.

    Returns:
        str: The license text if successfully downloaded, or a fallback message string
            if the download fails.
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return "# please refer to the metadata file (ro-crate-metadata.json) for information on model license"
    except Exception as e:
        print(f"Error downloading license text: {e}")
        return "please refer to the metadata file (ro-crate-metadata.json) for information on model license"
