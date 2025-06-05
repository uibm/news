#!/usr/bin/env python3
"""
Generate HTML dashboard from IBM news data
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardGenerator:
    def __init__(self):
        self.data_dir = Path("data")
        self.templates_dir = Path("templates")
        self.output_dir = Path("docs")
        self.assets_dir = Path("assets")
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
        
        # Setup Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        
    def load_data(self):
        """Load processed IBM news data"""
        try:
            # Load articles
            with open(self.data_dir / "ibm_articles.json", 'r', encoding='utf-8') as f:
                self.articles = json.load(f)
            
            # Load statistics
            with open(self.data_dir / "aggregation_stats.json", 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
                
            # Load configuration
            with open(self.data_dir / "config_used.json", 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                
            logger.info(f"Loaded {len(self.articles)} articles")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def organize_by_category(self):
        """Organize articles by category"""
        categories = {}
        
        for article in self.articles:
            category = article["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(article)
        
        # Sort articles within each category by date (newest first)
        for category in categories:
            categories[category].sort(
                key=lambda x: x["pub_date"] or "1970-01-01T00:00:00+00:00", 
                reverse=True
            )
        
        return categories
    
    def get_latest_articles(self, limit=10):
        """Get the latest articles across all categories"""
        sorted_articles = sorted(
            self.articles,
            key=lambda x: x["pub_date"] or "1970-01-01T00:00:00+00:00",
            reverse=True
        )
        return sorted_articles[:limit]
    
    def generate_html(self):
        """Generate the main HTML dashboard"""
        try:
            template = self.env.get_template('dashboard.html')
            
            # Organize data
            categories = self.organize_by_category()
            latest_articles = self.get_latest_articles()
            
            # Prepare template context
            context = {
                'articles': self.articles,
                'categories': categories,
                'latest_articles': latest_articles,
                'stats': self.stats,
                'config': self.config,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'total_articles': len(self.articles)
            }
            
            # Render template
            html_content = template.render(**context)
            
            # Write to output file
            output_file = self.output_dir / "index.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Dashboard generated: {output_file}")
            
        except Exception as e:
            logger.error(f"Error generating HTML: {e}")
            raise
    
    def copy_assets(self):
        """Copy CSS, JS, and other assets to output directory"""
        try:
            import shutil
            
            if self.assets_dir.exists():
                # Copy entire assets directory
                output_assets = self.output_dir / "assets"
                if output_assets.exists():
                    shutil.rmtree(output_assets)
                shutil.copytree(self.assets_dir, output_assets)
                logger.info("Assets copied to output directory")
            else:
                logger.warning("Assets directory not found")
                
        except Exception as e:
            logger.error(f"Error copying assets: {e}")

def main():
    """Main execution function"""
    try:
        generator = DashboardGenerator()
        generator.load_data()
        generator.generate_html()
        generator.copy_assets()
        
        print("✅ Dashboard generation complete!")
        print(f"📱 View your dashboard: docs/index.html")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()