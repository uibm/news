#!/usr/bin/env python3
"""
IBM News Aggregator - Fetch and filter IBM-related content from multiple RSS feeds
"""

import json
import time
import hashlib
import feedparser
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IBMNewsAggregator:
    def __init__(self, config_path: str = "config/rss_feeds.json"):
        """Initialize the IBM News Aggregator"""
        self.config_path = Path(config_path)
        self.output_dir = Path("data")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load configuration
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Compile IBM keywords for efficient matching
        self.ibm_patterns = self._compile_keywords()
        
        # Results storage
        self.articles = []
        self.stats = {
            "total_feeds_processed": 0,
            "total_articles_found": 0,
            "ibm_articles_found": 0,
            "categories_found": {},
            "processing_time": 0,
            "errors": []
        }

    def _compile_keywords(self) -> List[re.Pattern]:
        """Compile IBM keywords into regex patterns for efficient matching"""
        patterns = []
        keywords = self.config["ibm_keywords"]
        
        # Combine all keyword categories
        all_keywords = []
        for category in keywords.values():
            all_keywords.extend(category)
        
        # Create case-insensitive patterns
        for keyword in all_keywords:
            # Escape special regex characters and create word boundary pattern
            escaped = re.escape(keyword)
            pattern = rf'\b{escaped}\b'
            patterns.append(re.compile(pattern, re.IGNORECASE))
        
        return patterns

    def _is_ibm_related(self, title: str, description: str) -> tuple[bool, List[str]]:
        """Check if article content is IBM-related and return matched keywords"""
        content = f"{title} {description}".lower()
        matched_keywords = []
        
        for pattern in self.ibm_patterns:
            matches = pattern.findall(content)
            if matches:
                matched_keywords.extend(matches)
        
        return len(matched_keywords) > 0, list(set(matched_keywords))

    def _categorize_article(self, title: str, description: str, keywords: List[str]) -> str:
        """Categorize IBM article based on content and keywords"""
        content = f"{title} {description}".lower()
        
        # Define category patterns
        category_patterns = {
            "ai_watson": [r'\bai\b', r'watson', r'artificial intelligence', r'machine learning', r'neural'],
            "cloud_hybrid": [r'cloud', r'hybrid', r'kubernetes', r'containers', r'red hat'],
            "quantum": [r'quantum', r'qbit', r'quantum computing'],
            "enterprise": [r'enterprise', r'consulting', r'services', r'transformation'],
            "partnerships": [r'partner', r'deal', r'acquisition', r'collaboration', r'agreement'],
            "research": [r'research', r'innovation', r'breakthrough', r'technology'],
            "financial": [r'revenue', r'earnings', r'financial', r'stock', r'investor', r'quarterly']
        }
        
        # Score each category
        category_scores = {}
        for category, patterns in category_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, content):
                    score += 1
            category_scores[category] = score
        
        # Return category with highest score, default to 'latest'
        if category_scores and max(category_scores.values()) > 0:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return "latest"

    def _fetch_feed(self, feed_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed"""
        feed_name = feed_info["name"]
        feed_url = feed_info["url"]
        
        try:
            logger.info(f"Fetching feed: {feed_name} ({feed_url})")
            
            # Set user agent to avoid blocking
            headers = {
                'User-Agent': 'IBM News Aggregator Bot 1.0 (Educational/Research Purpose)'
            }
            
            # Fetch feed with timeout
            response = requests.get(feed_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning for {feed_name}: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries[:50]:  # Limit to latest 50 articles per feed
                try:
                    # Extract article data
                    title = getattr(entry, 'title', 'No title')
                    description = getattr(entry, 'description', '') or getattr(entry, 'summary', '')
                    link = getattr(entry, 'link', '')
                    
                    # Parse publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    
                    # Check if IBM-related
                    is_ibm, matched_keywords = self._is_ibm_related(title, description)
                    
                    if is_ibm:
                        # Categorize article
                        category = self._categorize_article(title, description, matched_keywords)
                        
                        # Generate unique ID
                        article_id = hashlib.md5(f"{title}{link}".encode()).hexdigest()
                        
                        article = {
                            "id": article_id,
                            "title": title,
                            "description": description,
                            "link": link,
                            "pub_date": pub_date.isoformat() if pub_date else None,
                            "source": feed_name,
                            "source_url": feed_url,
                            "category": category,
                            "matched_keywords": matched_keywords,
                            "priority": feed_info.get("priority", 2),
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        articles.append(article)
                        
                except Exception as e:
                    logger.error(f"Error processing article from {feed_name}: {str(e)}")
                    continue
            
            self.stats["total_articles_found"] += len(feed.entries)
            self.stats["ibm_articles_found"] += len(articles)
            
            logger.info(f"Found {len(articles)} IBM-related articles from {feed_name}")
            return articles
            
        except Exception as e:
            error_msg = f"Error fetching feed {feed_name}: {str(e)}"
            logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return []

    def fetch_all_feeds(self) -> None:
        """Fetch all RSS feeds and aggregate IBM-related content"""
        start_time = time.time()
        logger.info("Starting IBM news aggregation...")
        
        all_articles = []
        
        # Process each feed category
        for category_name, category_data in self.config["feed_categories"].items():
            logger.info(f"Processing category: {category_data['name']}")
            
            for feed_info in category_data["feeds"]:
                try:
                    articles = self._fetch_feed(feed_info)
                    all_articles.extend(articles)
                    self.stats["total_feeds_processed"] += 1
                    
                    # Small delay to be respectful to servers
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Unexpected error with feed {feed_info['name']}: {str(e)}")
                    continue
        
        # Remove duplicates and sort by priority and date
        seen_titles = set()
        unique_articles = []
        
        # Sort by priority (1 = highest) and then by date (newest first)
        all_articles.sort(key=lambda x: (
            x["priority"], 
            -(time.mktime(datetime.fromisoformat(x["pub_date"].replace('Z', '+00:00')).timetuple()) 
              if x["pub_date"] else 0)
        ))
        
        for article in all_articles:
            title_hash = hashlib.md5(article["title"].lower().encode()).hexdigest()
            if title_hash not in seen_titles:
                seen_titles.add(title_hash)
                unique_articles.append(article)
        
        self.articles = unique_articles[:100]  # Limit to top 100 articles
        
        # Update statistics
        self.stats["processing_time"] = time.time() - start_time
        
        # Count articles by category
        for article in self.articles:
            category = article["category"]
            self.stats["categories_found"][category] = self.stats["categories_found"].get(category, 0) + 1
        
        logger.info(f"Aggregation complete! Found {len(self.articles)} unique IBM articles")

    def save_results(self) -> None:
        """Save aggregated results to JSON files"""
        # Save articles
        articles_file = self.output_dir / "ibm_articles.json"
        with open(articles_file, 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, indent=2, ensure_ascii=False)
        
        # Save statistics
        stats_file = self.output_dir / "aggregation_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        # Save configuration copy for reference
        config_copy = self.output_dir / "config_used.json"
        with open(config_copy, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {self.output_dir}")

def main():
    """Main execution function"""
    try:
        aggregator = IBMNewsAggregator()
        aggregator.fetch_all_feeds()
        aggregator.save_results()
        
        # Print summary
        stats = aggregator.stats
        print(f"\n{'='*50}")
        print(f"IBM NEWS AGGREGATION SUMMARY")
        print(f"{'='*50}")
        print(f"Feeds processed: {stats['total_feeds_processed']}")
        print(f"Total articles scanned: {stats['total_articles_found']}")
        print(f"IBM articles found: {stats['ibm_articles_found']}")
        print(f"Processing time: {stats['processing_time']:.2f} seconds")
        print(f"\nCategories found:")
        for category, count in stats['categories_found'].items():
            print(f"  {category}: {count}")
        
        if stats['errors']:
            print(f"\nErrors encountered: {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"  - {error}")
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main()