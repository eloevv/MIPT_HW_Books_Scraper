import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from scraper import get_book_data, scrape_books
except ImportError:
    import importlib.util

    spec = importlib.util.spec_from_file_location("scraper", "../scraper.py")
    scraper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scraper)
    get_book_data = scraper.get_book_data
    scrape_books = scraper.scrape_books


class TestGetBookData:
    """Test cases for get_book_data function."""

    @pytest.fixture
    def test_book_url(self):
        """Fixture providing a valid test book URL."""
        return (
            "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
        )

    def test_returns_dictionary(self, test_book_url):
        """Test that get_book_data returns a dictionary."""
        result = get_book_data(test_book_url)
        assert isinstance(result, dict), "Function should return a dictionary"

    def test_has_required_keys(self, test_book_url):
        """Test that returned dictionary contains all required keys."""
        result = get_book_data(test_book_url)
        required_keys = [
            "title",
            "price",
            "rating",
            "availability",
            "description",
            "product_info",
        ]

        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

    def test_title_is_string(self, test_book_url):
        """Test that title field is a non-empty string."""
        result = get_book_data(test_book_url)
        assert isinstance(result["title"], str), "Title should be a string"
        assert len(result["title"]) > 0, "Title should not be empty"

    def test_title_correct_value(self, test_book_url):
        """Test that title matches the expected book title."""
        result = get_book_data(test_book_url)
        expected_title = "A Light in the Attic"
        assert result["title"] == expected_title, (
            f"Expected title '{expected_title}', got '{result['title']}'"
        )

    def test_price_format(self, test_book_url):
        """Test that price field contains currency symbol."""
        result = get_book_data(test_book_url)
        assert isinstance(result["price"], str), "Price should be a string"
        assert "£" in result["price"] or "$" in result["price"], (
            "Price should contain a currency symbol"
        )

    def test_rating_valid(self, test_book_url):
        """Test that rating is one of the valid values."""
        result = get_book_data(test_book_url)
        valid_ratings = ["One", "Two", "Three", "Four", "Five"]
        assert result["rating"] in valid_ratings, (
            f"Rating should be one of {valid_ratings}, got '{result['rating']}'"
        )

    def test_product_info_is_dict(self, test_book_url):
        """Test that product_info is a dictionary."""
        result = get_book_data(test_book_url)
        assert isinstance(result["product_info"], dict), (
            "product_info should be a dictionary"
        )

    def test_product_info_has_upc(self, test_book_url):
        """Test that product_info contains UPC key."""
        result = get_book_data(test_book_url)
        assert "UPC" in result["product_info"], "product_info should contain UPC"

    def test_availability_not_none(self, test_book_url):
        """Test that availability field is not None."""
        result = get_book_data(test_book_url)
        assert result["availability"] is not None, "Availability should not be None"


class TestScrapeBooks:
    """Test cases for scrape_books function."""

    def test_returns_list(self):
        """Test that scrape_books returns a list."""
        result = scrape_books(is_save=False, max_pages=1)
        assert isinstance(result, list), "Function should return a list"

    def test_list_not_empty(self):
        """Test that scrape_books returns non-empty list."""
        result = scrape_books(is_save=False, max_pages=1)
        assert len(result) > 0, "Should scrape at least one book"

    def test_expected_book_count_single_page(self):
        """Test that scraping one page returns expected number of books."""
        result = scrape_books(is_save=False, max_pages=1)
        assert 15 <= len(result) <= 20, (
            f"Expected 15-20 books from one page, got {len(result)}"
        )

    def test_expected_book_count_two_pages(self):
        """Test that scraping two pages returns expected number of books."""
        result = scrape_books(is_save=False, max_pages=2)
        assert 30 <= len(result) <= 40, (
            f"Expected 30-40 books from two pages, got {len(result)}"
        )

    def test_each_book_is_dict(self):
        """Test that each scraped book is a dictionary."""
        result = scrape_books(is_save=False, max_pages=1)
        for book in result:
            assert isinstance(book, dict), "Each book should be a dictionary"

    def test_each_book_has_title(self):
        """Test that each scraped book has a title."""
        result = scrape_books(is_save=False, max_pages=1)
        for book in result:
            assert "title" in book, "Each book should have a title"
            assert book["title"] is not None, "Title should not be None"
            assert len(book["title"]) > 0, "Title should not be empty"

    def test_no_duplicate_titles(self):
        """Test that there are no duplicate book titles in results."""
        result = scrape_books(is_save=False, max_pages=1)
        titles = [book["title"] for book in result]
        assert len(titles) == len(set(titles)), "Should not have duplicate book titles"

    def test_max_pages_limit_works(self):
        """Test that max_pages parameter limits the scraping."""
        result_1_page = scrape_books(is_save=False, max_pages=1)
        if len(result_1_page) > 0:
            result_2_pages = scrape_books(is_save=False, max_pages=2)
            assert len(result_2_pages) >= len(result_1_page), (
                f"Scraping 2 pages ({len(result_2_pages)}) should return at least "
                f"as many books as 1 page ({len(result_1_page)})"
            )
        else:
            pytest.skip("Network error prevented scraping first page")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
