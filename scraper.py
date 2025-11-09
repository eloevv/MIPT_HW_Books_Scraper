import time
import requests
import schedule  # type: ignore
import json
from datetime import datetime
from bs4 import BeautifulSoup


def get_book_data(book_url: str) -> dict:
    """
    Extracts book information from a Books to Scrape page.

    Parses a book page and collects all available data including title,
    price, rating, availability, description, and additional characteristics
    from the Product Information table.

    Args:
        url (str): URL of the book page on Books to Scrape website.

    Returns:
        dict: Dictionary containing book data with the following keys:
            - title (str): Book title
            - price (str): Book price
            - rating (str): Book rating (One, Two, Three, Four, Five)
            - availability (str): Availability information
            - description (str): Book description (if available)
            - product_info (dict): Additional characteristics from Product
              Information table (UPC, Product Type, Price excl/incl tax,
              Tax, Number of reviews)

    Raises:
        requests.RequestException: If an error occurs during page request.
    """

    response = requests.get(book_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    book_data = {}

    title_tag = soup.find("h1")
    book_data["title"] = title_tag.text.strip() if title_tag else None

    price_tag = soup.find("p", class_="price_color")
    book_data["price"] = price_tag.text.strip() if price_tag else None

    rating_tag = soup.find("p", class_="star-rating")
    if rating_tag:
        rating_classes = rating_tag.get("class", [])
        book_data["rating"] = rating_classes[1] if len(rating_classes) > 1 else None
    else:
        book_data["rating"] = None

    availability_tag = soup.find("p", class_="instock availability")
    if availability_tag:
        book_data["availability"] = availability_tag.text.strip()
    else:
        book_data["availability"] = None

    description_tag = soup.find("div", id="product_description")
    if description_tag:
        description_p = description_tag.find_next_sibling("p")
        book_data["description"] = description_p.text.strip() if description_p else None
    else:
        book_data["description"] = None

    product_info = {}
    table = soup.find("table", class_="table table-striped")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            header = row.find("th")
            data = row.find("td")
            if header and data:
                key = header.text.strip()
                value = data.text.strip()
                product_info[key] = value

    book_data["product_info"] = product_info

    return book_data


def scrape_books(is_save=False, max_pages=None):
    """
    Scrapes book data from all catalog pages on Books to Scrape website.
    Iterates through all catalog pages and collects information about each book
    using the get_book_data function. Optionally saves results to a file.

    Args:
        save_to_file (bool): If True, saves results to 'books_data.txt' file
                            in the same directory. Defaults to False.
        max_pages (int or None): Maximum number of pages to scrape.
                                 If None, scrapes all available pages.
                                 Defaults to None.

    Returns:
        list: List of dictionaries, where each dictionary contains
              data about one book collected by get_book_data function.

    Raises:
        requests.RequestException: If an error occurs during page requests.
    """

    base_url = "http://books.toscrape.com/catalogue/page-{}.html"
    books_list = []
    page_num = 1

    print("Starting to scrape books...")

    while True:
        if max_pages and page_num > max_pages:
            print(f"Reached maximum pages limit: {max_pages}")
            break

        catalog_url = base_url.format(page_num)
        print(f"Processing page {page_num}: {catalog_url}")

        try:
            response = requests.get(catalog_url)
            if response.status_code == 404:
                print(f"Page {page_num} not found. Finished scraping.")
                break

            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            book_articles = soup.find_all("article", class_="product_pod")

            if not book_articles:
                print(f"No books found on page {page_num}. Stopping.")
                break

            for article in book_articles:
                h3_tag = article.find("h3")
                if h3_tag:
                    a_tag = h3_tag.find("a")
                    if a_tag and a_tag.get("href"):
                        book_relative_url = a_tag["href"]
                        book_url = (
                            f"http://books.toscrape.com/catalogue/{book_relative_url}"
                        )

                        try:
                            book_data = get_book_data(book_url)
                            books_list.append(book_data)
                            print(f"  Scraped: {book_data['title']}")
                        except Exception as e:
                            print(f"  Error scraping {book_url}: {e}")

                        time.sleep(0.1)

            page_num += 1

        except requests.RequestException as e:
            print(f"Error requesting page {page_num}: {e}")
            break

    print(f"\nTotal books scraped: {len(books_list)}")
    if is_save:
        with open("books_data.txt", "w", encoding="utf-8") as f:
            json.dump(books_list, f, ensure_ascii=False, indent=2)

    return books_list


def run_scheduler(schedule_time="19:00"):
    """
    Sets up and runs the scheduler for automatic book scraping.

    Configures daily scraping at the specified time and runs an infinite
    loop that checks for pending tasks every 60 seconds to avoid system
    overload. When the scheduled time is reached, performs scraping and
    saves data to file.

    Args:
        schedule_time (str): Time in HH:MM format when scraping should run.
                            Defaults to "19:00".

    Returns:
        None: This function runs indefinitely until manually stopped.
    """

    def scraping_job():
        """Internal function that performs the actual scraping."""
        print(f"\n{'=' * 60}")
        print(
            f"Scheduled scraping started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"{'=' * 60}\n")

        try:
            books = scrape_books(is_save=True)
            print(f"\n{'=' * 60}")
            print(
                f"Scraping completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(f"Total books collected: {len(books)}")
            print(f"{'=' * 60}\n")
        except Exception as e:
            print(f"\n{'=' * 60}")
            print(f"Error during scheduled scraping: {e}")
            print(f"{'=' * 60}\n")

    schedule.every().day.at(schedule_time).do(scraping_job)

    print(f"Scheduler initialized. Books will be scraped daily at {schedule_time}")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Press Ctrl+C to stop the scheduler\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
