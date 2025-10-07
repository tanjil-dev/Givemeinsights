import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


# Function to get the status code of a URL
def get_status_code(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code
    except requests.RequestException as e:
        return None  # If there is an error (e.g., timeout, connection issue)


# Function to get all internal links from a webpage
def get_internal_links(url, domain):
    internal_links = set()
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all anchor tags <a> to extract links
        for anchor in soup.find_all('a', href=True):
            href = anchor.get('href')
            # Make sure the link is internal (same domain)
            if href.startswith('/') or urlparse(href).netloc == domain:
                full_url = urljoin(url, href)
                internal_links.add(full_url)
    except requests.RequestException as e:
        print(f"Failed to retrieve or parse {url}: {e}")
    return internal_links


# Function to crawl the website and check status codes
def crawl_website(start_url):
    visited = set()
    to_visit = {start_url}
    domain = urlparse(start_url).netloc

    status_codes = {200: 0, 404: 0, 500: 0}

    while to_visit:
        url = to_visit.pop()

        if url in visited:
            continue

        visited.add(url)

        # Get the status code of the page
        status_code = get_status_code(url)

        if status_code == 200:
            status_codes[200] += 1
        elif status_code == 404:
            status_codes[404] += 1
        elif status_code == 500:
            status_codes[500] += 1

        # Get internal links and add them to the queue
        if status_code == 200:  # Only crawl 200 OK pages
            links = get_internal_links(url, domain)
            to_visit.update(links)

        print(f"Checked {url} - Status: {status_code}")

    # Print the summary of status codes
    print("\nCrawl Summary:")
    print(f"200 OK: {status_codes[200]}")
    print(f"404 Not Found: {status_codes[404]}")
    print(f"500 Internal Server Error: {status_codes[500]}")


if __name__ == "__main__":
    start_url = input("Enter the website URL to start crawling (e.g., https://example.com): ")
    crawl_website(start_url)
