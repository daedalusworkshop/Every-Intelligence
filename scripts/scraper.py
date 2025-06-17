#!/usr/bin/env python3
"""
Every.to Content Scraper - Modular & Testable Version
====================================================

A testable scraper that allows you to run each phase independently
and validate results at each step.

Key Features:
- Run each function independently for testing
- Built-in validation functions
- Progress saving and resuming
- Comprehensive testing utilities

Usage Examples:
    # Test individual components
    python scraper.py --test-columns
    python scraper.py --test-single-column napkin-math
    python scraper.py --test-single-article https://every.to/...
    
    # Run complete process with validation
    python scraper.py --discover-only
    python scraper.py --scrape-only
    python scraper.py --full-run
    
    # Validation and testing
    python scraper.py --validate-discovery
    python scraper.py --compare-with-baseline
"""

import requests
import time
import json
import re
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime

# Import our article extraction functions
from extractor import extract_article_data

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://every.to"
COLUMNISTS_URL = "https://every.to/columnists"
REQUEST_DELAY = 1.5  # seconds between requests (be respectful!)
MAX_RETRIES = 3

# File paths for incremental progress
COLUMNS_FILE = "discovered_columns.json"
URLS_FILE = "discovered_urls.json" 
ARTICLES_FILE = "scraped_articles.json"
VALIDATION_FILE = "validation_report.json"

@dataclass
class ScrapingStats:
    """Track scraping statistics for validation"""
    total_columns: int = 0
    total_urls_discovered: int = 0
    total_articles_scraped: int = 0
    failed_urls: List[str] = None
    discovery_time: str = ""
    scraping_time: str = ""
    
    def __post_init__(self):
        if self.failed_urls is None:
            self.failed_urls = []

class EveryToScraper:
    """
    A modular scraper that can be tested at each step
    """
    
    def __init__(self, delay: float = REQUEST_DELAY):
        self.delay = delay
        self.stats = ScrapingStats()
        
    def get_webpage(self, url: str, retries: int = MAX_RETRIES) -> Optional[BeautifulSoup]:
        """
        Download a webpage with retry logic and error handling.
        
        Returns BeautifulSoup object or None if failed.
        """
        for attempt in range(retries):
            try:
                logger.debug(f"Fetching: {url} (attempt {attempt + 1})")
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'lxml')
                return soup
                
            except requests.RequestException as e:
                logger.warning(f"Failed to fetch {url} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(self.delay * 2)  # Longer delay on retry
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
            
            # Be respectful - delay between requests
            time.sleep(self.delay)
        
        return None

    def discover_columns(self, save_to_file: bool = True) -> List[str]:
        """
        Extract all column names from the /columnists page.
        
        Args:
            save_to_file: Whether to save results to COLUMNS_FILE
            
        Returns:
            List of column names (like ['chain-of-thought', 'napkin-math', ...])
        """
        logger.info("🔍 Discovering columns from /columnists page...")
        
        soup = self.get_webpage(COLUMNISTS_URL)
        if not soup:
            logger.error("Could not access columnists page")
            return []
        
        # Find all links that look like column URLs
        column_links = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            
            # Look for links that are just "/column-name" (no additional path)
            if href and href.startswith('/') and not href.startswith('//'):
                # Remove leading slash
                column_name = href.lstrip('/')
                
                # Filter out non-column URLs (these are structural pages)
                skip_patterns = [
                    'newsletter', 'columnists', 'search', 'login', 'subscribe', 
                    'about', 'team', 'podcast', 'studio', 'consulting', 'cdn-cgi',
                    'assets', ''  # empty string for bare "/"
                ]
                
                # Only keep simple column names (no slashes, no special chars)
                if ('/' not in column_name and 
                    column_name not in skip_patterns and 
                    column_name and  # not empty
                    len(column_name) > 2 and  # reasonable length
                    re.match(r'^[a-z0-9-]+$', column_name)):  # only lowercase, numbers, hyphens
                    
                    column_links.append(column_name)
        
        # Remove duplicates and sort
        columns = sorted(list(set(column_links)))
        self.stats.total_columns = len(columns)
        
        logger.info(f"✅ Discovered {len(columns)} columns: {columns}")
        
        if save_to_file:
            self._save_columns(columns)
            
        return columns

    def discover_articles_in_column(self, column_name: str, max_pages: Optional[int] = None) -> List[str]:
        """
        Get all article URLs from a specific column page, handling pagination.
        
        Args:
            column_name: The column name (e.g., 'chain-of-thought')
            max_pages: Limit pages for testing (None = all pages)
        
        Returns:
            List of full article URLs across all pages
        """
        logger.info(f"🔍 Discovering articles in column: {column_name}")
        
        all_article_urls = []
        page_num = 1
        
        # Keep going until we find a page with no articles
        while True:
            if max_pages and page_num > max_pages:
                logger.info(f"Reached max_pages limit ({max_pages}) for testing")
                break
                
            # Build the page URL - Every.to uses ?page=N format
            if page_num == 1:
                page_url = f"{BASE_URL}/{column_name}"
            else:
                page_url = f"{BASE_URL}/{column_name}?page={page_num}"
            
            logger.debug(f"Checking page {page_num}: {page_url}")
            
            soup = self.get_webpage(page_url)
            if not soup:
                logger.warning(f"Could not access page {page_num} for {column_name}")
                break
            
            # Find article links on this page
            page_articles = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                
                # Look for links that start with the column path
                if href and href.startswith(f'/{column_name}/'):
                    # Skip empty links (images/thumbnails without text)
                    link_text = link.get_text(strip=True)
                    if link_text:  # Only count links that have actual text
                        # Create full URL
                        full_url = urljoin(BASE_URL, href)
                        page_articles.append(full_url)
            
            # If no articles found, we've reached the end
            if not page_articles:
                logger.info(f"No articles found on page {page_num} - stopping pagination for {column_name}")
                break
            
            logger.info(f"Found {len(page_articles)} articles on page {page_num} of {column_name}")
            all_article_urls.extend(page_articles)
            page_num += 1
            
            # Be respectful - delay between page requests
            time.sleep(self.delay)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_articles = []
        for url in all_article_urls:
            if url not in seen:
                seen.add(url)
                unique_articles.append(url)
        
        logger.info(f"✅ Total: {len(unique_articles)} unique articles across {page_num - 1} pages in {column_name}")
        return unique_articles

    def discover_all_urls(self, columns: Optional[List[str]] = None, save_to_file: bool = True) -> List[str]:
        """
        Discover all article URLs across all columns.
        
        Args:
            columns: List of columns to process (None = discover columns first)
            save_to_file: Whether to save results to URLS_FILE
            
        Returns:
            List of all article URLs
        """
        logger.info("🔍 Starting URL discovery phase...")
        
        if columns is None:
            columns = self.discover_columns(save_to_file=False)
        
        if not columns:
            logger.error("No columns to process")
            return []
        
        all_article_urls = []
        
        for i, column_name in enumerate(columns):
            logger.info(f"Processing column {i+1}/{len(columns)}: {column_name}")
            article_urls = self.discover_articles_in_column(column_name)
            all_article_urls.extend(article_urls)
            
            # Be respectful - delay between columns
            time.sleep(self.delay)
        
        # Remove duplicates across all columns
        seen = set()
        unique_urls = []
        for url in all_article_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        self.stats.total_urls_discovered = len(unique_urls)
        self.stats.discovery_time = datetime.now().isoformat()
        
        logger.info(f"✅ Discovery complete! Found {len(unique_urls)} total unique articles")
        
        if save_to_file:
            self._save_urls(unique_urls)
            
        return unique_urls

    def scrape_articles(self, urls: Optional[List[str]] = None, start_index: int = 0) -> List[Dict]:
        """
        Scrape content from a list of article URLs.
        
        Args:
            urls: List of URLs to scrape (None = load from URLS_FILE)
            start_index: Index to start from (for resuming interrupted runs)
            
        Returns:
            List of article data dictionaries
        """
        logger.info("📄 Starting article scraping phase...")
        
        if urls is None:
            urls = self._load_urls()
        
        if not urls:
            logger.error("No URLs to scrape")
            return []
        
        # Resume from start_index if provided
        if start_index > 0:
            logger.info(f"Resuming from article {start_index + 1}")
            urls = urls[start_index:]
        
        articles = []
        failed_urls = []
        
        for i, url in enumerate(urls):
            actual_index = start_index + i
            logger.info(f"Scraping article {actual_index + 1}/{start_index + len(urls)}: {url}")
            
            try:
                # Use our extractor to get the article data
                article_data = extract_article_data(url)
                
                if article_data.get('title') and article_data.get('content'):
                    articles.append(article_data)
                    logger.info(f"✅ Successfully scraped: {article_data.get('title', 'Unknown')[:50]}...")
                else:
                    logger.warning(f"❌ Article missing title or content: {url}")
                    failed_urls.append(url)
                    
            except Exception as e:
                logger.error(f"❌ Failed to scrape {url}: {e}")
                failed_urls.append(url)
            
            # Be respectful - delay between articles
            time.sleep(self.delay)
            
            # Save progress every 25 articles
            if (i + 1) % 25 == 0:
                logger.info(f"💾 Progress checkpoint: {actual_index + 1} articles processed")
                self._save_articles(articles, f"checkpoint_{actual_index + 1}.json")
        
        self.stats.total_articles_scraped = len(articles)
        self.stats.failed_urls = failed_urls
        self.stats.scraping_time = datetime.now().isoformat()
        
        logger.info(f"✅ Scraping complete! Successfully scraped {len(articles)} articles")
        if failed_urls:
            logger.warning(f"❌ Failed to scrape {len(failed_urls)} articles")
        
        return articles

    # === TESTING & VALIDATION METHODS ===
    
    def test_single_column(self, column_name: str, max_pages: int = 2) -> Dict:
        """
        Test URL discovery for a single column (useful for debugging).
        
        Args:
            column_name: Column to test
            max_pages: Limit pages for quick testing
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"🧪 Testing single column: {column_name}")
        
        urls = self.discover_articles_in_column(column_name, max_pages=max_pages)
        
        # Test a sample of URLs
        sample_size = min(3, len(urls))
        sample_urls = urls[:sample_size]
        
        test_results = {
            "column": column_name,
            "total_urls_found": len(urls),
            "sample_urls": sample_urls,
            "sample_results": []
        }
        
        for url in sample_urls:
            try:
                article_data = extract_article_data(url)
                result = {
                    "url": url,
                    "success": bool(article_data.get('title') and article_data.get('content')),
                    "title": article_data.get('title', 'NO TITLE')[:50],
                    "content_length": len(article_data.get('content', '')),
                    "word_count": article_data.get('word_count', 0)
                }
                test_results["sample_results"].append(result)
                
            except Exception as e:
                test_results["sample_results"].append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(f"✅ Test complete for {column_name}")
        return test_results

    def validate_discovery(self) -> Dict:
        """
        Validate URL discovery by checking for expected patterns and coverage.
        
        Returns:
            Validation report dictionary
        """
        logger.info("🔍 Validating discovery results...")
        
        # Load discovered data
        columns = self._load_columns()
        urls = self._load_urls()
        
        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "columns_found": len(columns),
            "urls_found": len(urls),
            "validation_checks": {}
        }
        
        # Check 1: Do we have a reasonable number of columns?
        expected_min_columns = 5  # Every.to should have at least 5 active columns
        validation_report["validation_checks"]["sufficient_columns"] = {
            "pass": len(columns) >= expected_min_columns,
            "found": len(columns),
            "expected_min": expected_min_columns
        }
        
        # Check 2: Do URLs follow expected patterns?
        url_patterns = {}
        for url in urls:
            # Extract column from URL
            parts = url.split('/')
            if len(parts) >= 4:
                column = parts[3]
                url_patterns[column] = url_patterns.get(column, 0) + 1
        
        validation_report["validation_checks"]["url_distribution"] = url_patterns
        
        # Check 3: Are there obvious gaps?
        expected_columns = ["napkin-math", "chain-of-thought", "divinations"]  # Known major columns
        missing_expected = [col for col in expected_columns if col not in columns]
        validation_report["validation_checks"]["missing_expected_columns"] = missing_expected
        
        # Check 4: Sample a few URLs to ensure they're valid
        sample_urls = urls[:5] if urls else []
        sample_validation = []
        
        for url in sample_urls:
            try:
                soup = self.get_webpage(url)
                has_title = bool(soup and soup.find('h1'))
                sample_validation.append({
                    "url": url,
                    "accessible": bool(soup),
                    "has_title": has_title
                })
            except Exception as e:
                sample_validation.append({
                    "url": url,
                    "accessible": False,
                    "error": str(e)
                })
        
        validation_report["validation_checks"]["sample_url_validation"] = sample_validation
        
        # Save validation report
        self._save_json(validation_report, VALIDATION_FILE)
        
        # Print summary
        logger.info("=== VALIDATION SUMMARY ===")
        logger.info(f"Columns discovered: {len(columns)}")
        logger.info(f"URLs discovered: {len(urls)}")
        logger.info(f"URL distribution: {url_patterns}")
        if missing_expected:
            logger.warning(f"Missing expected columns: {missing_expected}")
        logger.info("===========================")
        
        return validation_report

    def compare_with_manual_count(self, manual_counts: Dict[str, int]) -> Dict:
        """
        Compare discovered URLs with manual counts for validation.
        
        Args:
            manual_counts: Dictionary like {"napkin-math": 50, "chain-of-thought": 75}
            
        Returns:
            Comparison report
        """
        logger.info("🔍 Comparing with manual baseline...")
        
        urls = self._load_urls()
        
        # Count URLs per column
        discovered_counts = {}
        for url in urls:
            parts = url.split('/')
            if len(parts) >= 4:
                column = parts[3]
                discovered_counts[column] = discovered_counts.get(column, 0) + 1
        
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "comparisons": {}
        }
        
        for column, manual_count in manual_counts.items():
            discovered_count = discovered_counts.get(column, 0)
            difference = discovered_count - manual_count
            percentage = (discovered_count / manual_count * 100) if manual_count > 0 else 0
            
            comparison["comparisons"][column] = {
                "manual_count": manual_count,
                "discovered_count": discovered_count,
                "difference": difference,
                "coverage_percentage": round(percentage, 1)
            }
        
        logger.info("=== BASELINE COMPARISON ===")
        for column, comp in comparison["comparisons"].items():
            logger.info(f"{column}: {comp['discovered_count']}/{comp['manual_count']} ({comp['coverage_percentage']}%)")
        logger.info("============================")
        
        return comparison

    # === FILE I/O METHODS ===
    
    def _save_columns(self, columns: List[str]):
        """Save discovered columns to file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "columns": columns
        }
        self._save_json(data, COLUMNS_FILE)
        logger.info(f"💾 Saved {len(columns)} columns to {COLUMNS_FILE}")
    
    def _save_urls(self, urls: List[str]):
        """Save discovered URLs to file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_count": len(urls),
            "urls": urls
        }
        self._save_json(data, URLS_FILE)
        logger.info(f"💾 Saved {len(urls)} URLs to {URLS_FILE}")
    
    def _save_articles(self, articles: List[Dict], filename: str = ARTICLES_FILE):
        """Save scraped articles to file"""
        # Add metadata to the output
        output_data = {
            "metadata": {
                "total_articles": len(articles),
                "scraped_at": datetime.now().isoformat(),
                "source": "every.to",
                "scraper_version": "2.0.0",
                "stats": self.stats.__dict__
            },
            "articles": articles
        }
        
        self._save_json(output_data, filename)
        logger.info(f"💾 Saved {len(articles)} articles to {filename}")
        
        # Print summary statistics
        if articles:
            word_counts = [article.get('word_count', 0) for article in articles]
            total_words = sum(word_counts)
            avg_words = total_words // len(articles) if articles else 0
            
            logger.info("=== SCRAPING SUMMARY ===")
            logger.info(f"Total articles: {len(articles)}")
            logger.info(f"Total words: {total_words:,}")
            logger.info(f"Average words per article: {avg_words:,}")
            logger.info("=======================")
    
    def _load_columns(self) -> List[str]:
        """Load columns from file"""
        data = self._load_json(COLUMNS_FILE)
        return data.get("columns", []) if data else []
    
    def _load_urls(self) -> List[str]:
        """Load URLs from file"""
        data = self._load_json(URLS_FILE)
        return data.get("urls", []) if data else []
    
    def _load_articles(self) -> List[Dict]:
        """Load articles from file"""
        data = self._load_json(ARTICLES_FILE)
        return data.get("articles", []) if data else []
    
    def _save_json(self, data: Dict, filename: str):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_json(self, filename: str) -> Optional[Dict]:
        """Load data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

def main():
    """Main function with command-line interface for testing"""
    parser = argparse.ArgumentParser(description="Every.to Modular Scraper")
    
    # Testing commands
    parser.add_argument('--test-columns', action='store_true', help='Test column discovery')
    parser.add_argument('--test-single-column', type=str, help='Test single column (e.g., napkin-math)')
    parser.add_argument('--test-single-article', type=str, help='Test single article URL')
    
    # Discovery commands
    parser.add_argument('--discover-only', action='store_true', help='Only discover URLs, don\'t scrape')
    parser.add_argument('--scrape-only', action='store_true', help='Only scrape (use existing URLs)')
    parser.add_argument('--full-run', action='store_true', help='Complete discovery + scraping')
    
    # Validation commands
    parser.add_argument('--validate-discovery', action='store_true', help='Validate discovery results')
    parser.add_argument('--resume-from', type=int, help='Resume scraping from article index')
    
    # Configuration
    parser.add_argument('--delay', type=float, default=1.5, help='Delay between requests')
    parser.add_argument('--max-pages', type=int, help='Limit pages for testing')
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = EveryToScraper(delay=args.delay)
    
    # Execute based on arguments
    if args.test_columns:
        columns = scraper.discover_columns()
        print(f"\n✅ Found {len(columns)} columns: {columns}")
        
    elif args.test_single_column:
        results = scraper.test_single_column(args.test_single_column, max_pages=args.max_pages or 2)
        print(f"\n✅ Test results for {args.test_single_column}:")
        print(json.dumps(results, indent=2))
        
    elif args.test_single_article:
        try:
            article_data = extract_article_data(args.test_single_article)
            print(f"\n✅ Article test successful:")
            print(f"Title: {article_data.get('title', 'NO TITLE')}")
            print(f"Author: {article_data.get('author', 'NO AUTHOR')}")
            print(f"Word count: {article_data.get('word_count', 0)}")
            print(f"Content preview: {article_data.get('content', '')[:200]}...")
        except Exception as e:
            print(f"\n❌ Article test failed: {e}")
            
    elif args.discover_only:
        urls = scraper.discover_all_urls()
        print(f"\n✅ Discovery complete: {len(urls)} URLs found")
        
    elif args.scrape_only:
        articles = scraper.scrape_articles(start_index=args.resume_from or 0)
        print(f"\n✅ Scraping complete: {len(articles)} articles scraped")
        
    elif args.validate_discovery:
        report = scraper.validate_discovery()
        print(f"\n✅ Validation complete - see {VALIDATION_FILE}")
        
    elif args.full_run:
        # Complete workflow
        logger.info("🚀 Starting full scraping workflow...")
        
        # Step 1: Discovery
        urls = scraper.discover_all_urls()
        if not urls:
            logger.error("No URLs discovered. Stopping.")
            return
            
        # Step 2: Validation
        scraper.validate_discovery()
        
        # Step 3: Scraping
        articles = scraper.scrape_articles(urls)
        
        # Step 4: Save final results
        scraper._save_articles(articles)
        
        logger.info("🎉 Full workflow complete!")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 