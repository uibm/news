/**
 * IBM News Dashboard JavaScript
 * Handles navigation, filtering, and interactive features
 */

class IBMDashboard {
    constructor() {
        this.currentCategory = 'all';
        this.articles = [];
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupSearch();
        this.setupKeyboardShortcuts();
        this.updateLastRefresh();
        
        // Show all articles by default
        this.showCategory('all');
    }

    setupNavigation() {
        const navButtons = document.querySelectorAll('.nav-btn');
        
        navButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const category = e.currentTarget.getAttribute('data-category');
                this.showCategory(category);
                this.setActiveNav(e.currentTarget);
            });
        });
    }

    setActiveNav(activeButton) {
        // Remove active class from all buttons
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active class to clicked button
        activeButton.classList.add('active');
    }

    showCategory(category) {
        this.currentCategory = category;
        
        // Hide all sections
        document.querySelectorAll('.top-stories, .category-section').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show the selected section
        if (category === 'all') {
            document.querySelector('.top-stories').style.display = 'block';
        } else {
            const section = document.getElementById(`section-${category}`);
            if (section) {
                section.style.display = 'block';
            }
        }
        
        // Update URL without page reload
        this.updateURL(category);
        
        // Analytics tracking (if needed)
        this.trackCategoryView(category);
    }

    setupSearch() {
        // Add search functionality
        const searchContainer = document.createElement('div');
        searchContainer.className = 'search-container';
        searchContainer.innerHTML = `
            <div class="search-box">
                <i class="fas fa-search"></i>
                <input type="text" id="search-input" placeholder="Search IBM news..." />
                <button id="clear-search" class="clear-btn" style="display: none;">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Insert search box after navigation
        const nav = document.querySelector('.category-nav');
        nav.parentNode.insertBefore(searchContainer, nav.nextSibling);
        
        // Add search styles
        const searchStyles = `
            .search-container {
                background: var(--card-background);
                padding: 1rem 0;
                border-bottom: 1px solid var(--border-color);
            }
            
            .search-box {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 2rem;
                position: relative;
                display: flex;
                align-items: center;
            }
            
            .search-box i {
                position: absolute;
                left: 3rem;
                color: var(--text-secondary);
                z-index: 10;
            }
            
            #search-input {
                width: 100%;
                max-width: 400px;
                padding: 0.75rem 1rem 0.75rem 2.5rem;
                border: 2px solid var(--border-color);
                border-radius: var(--border-radius);
                font-size: 1rem;
                transition: border-color 0.3s ease;
            }
            
            #search-input:focus {
                outline: none;
                border-color: var(--primary-color);
            }
            
            .clear-btn {
                position: absolute;
                right: 2rem;
                background: none;
                border: none;
                cursor: pointer;
                color: var(--text-secondary);
                padding: 0.5rem;
                margin-left: 0.5rem;
            }
            
            .clear-btn:hover {
                color: var(--primary-color);
            }
            
            .search-results {
                margin-top: 1rem;
                padding: 1rem;
                background: var(--background-color);
                border-radius: var(--border-radius);
            }
            
            .no-results {
                text-align: center;
                color: var(--text-secondary);
                padding: 2rem;
            }
        `;
        
        // Add styles to head
        const style = document.createElement('style');
        style.textContent = searchStyles;
        document.head.appendChild(style);
        
        // Setup search functionality
        const searchInput = document.getElementById('search-input');
        const clearBtn = document.getElementById('clear-search');
        
        let searchTimeout;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();
            
            if (query) {
                clearBtn.style.display = 'block';
                searchTimeout = setTimeout(() => this.performSearch(query), 300);
            } else {
                clearBtn.style.display = 'none';
                this.clearSearch();
            }
        });
        
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearBtn.style.display = 'none';
            this.clearSearch();
            searchInput.focus();
        });
        
        // Search on Enter
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch(searchInput.value.trim());
            }
        });
    }

    performSearch(query) {
        if (!query) {
            this.clearSearch();
            return;
        }
        
        const results = this.searchArticles(query);
        this.displaySearchResults(results, query);
    }

    searchArticles(query) {
        const searchTerms = query.toLowerCase().split(' ');
        const allArticles = this.getAllArticles();
        
        return allArticles.filter(article => {
            const searchText = `${article.title} ${article.description} ${article.matched_keywords.join(' ')}`.toLowerCase();
            return searchTerms.every(term => searchText.includes(term));
        });
    }

    getAllArticles() {
        const articles = [];
        
        // Get articles from all sections
        document.querySelectorAll('.article-card, .article-item').forEach(element => {
            const titleElement = element.querySelector('.article-title a');
            const descElement = element.querySelector('.article-description');
            const keywordsElements = element.querySelectorAll('.keyword-tag');
            
            if (titleElement && descElement) {
                const keywords = Array.from(keywordsElements).map(el => el.textContent);
                articles.push({
                    title: titleElement.textContent,
                    description: descElement.textContent,
                    link: titleElement.href,
                    matched_keywords: keywords,
                    element: element
                });
            }
        });
        
        return articles;
    }

    displaySearchResults(results, query) {
        // Hide all sections
        document.querySelectorAll('.top-stories, .category-section').forEach(section => {
            section.style.display = 'none';
        });
        
        // Create or update search results section
        let searchSection = document.getElementById('search-results-section');
        if (!searchSection) {
            searchSection = document.createElement('section');
            searchSection.id = 'search-results-section';
            searchSection.className = 'category-section';
            document.querySelector('.dashboard-main').appendChild(searchSection);
        }
        
        if (results.length === 0) {
            searchSection.innerHTML = `
                <h2><i class="fas fa-search"></i> Search Results for "${query}"</h2>
                <div class="no-results">
                    <i class="fas fa-search" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i>
                    <p>No articles found matching your search.</p>
                    <p>Try different keywords or browse by category.</p>
                </div>
            `;
        } else {
            const articlesHtml = results.map(article => `
                <article class="article-item">
                    <div class="article-content">
                        <h3 class="article-title">
                            <a href="${article.link}" target="_blank" rel="noopener">
                                ${this.highlightSearchTerms(article.title, query)}
                            </a>
                        </h3>
                        <p class="article-description">
                            ${this.highlightSearchTerms(article.description, query)}
                        </p>
                        <div class="article-keywords">
                            ${article.matched_keywords.map(keyword => 
                                `<span class="keyword-tag">${keyword}</span>`
                            ).join('')}
                        </div>
                    </div>
                </article>
            `).join('');
            
            searchSection.innerHTML = `
                <h2><i class="fas fa-search"></i> Search Results for "${query}" (${results.length})</h2>
                <div class="articles-list">
                    ${articlesHtml}
                </div>
            `;
        }
        
        searchSection.style.display = 'block';
        
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
    }

    highlightSearchTerms(text, query) {
        if (!query) return text;
        
        const terms = query.toLowerCase().split(' ');
        let highlightedText = text;
        
        terms.forEach(term => {
            const regex = new RegExp(`(${term})`, 'gi');
            highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
        });
        
        return highlightedText;
    }

    clearSearch() {
        const searchSection = document.getElementById('search-results-section');
        if (searchSection) {
            searchSection.style.display = 'none';
        }
        
        // Show the previously active category
        this.showCategory(this.currentCategory);
        
        // Restore active navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            if (btn.getAttribute('data-category') === this.currentCategory) {
                btn.classList.add('active');
            }
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only handle shortcuts if not typing in an input
            if (e.target.tagName === 'INPUT') return;
            
            switch(e.key) {
                case '/':
                    e.preventDefault();
                    document.getElementById('search-input').focus();
                    break;
                case 'Escape':
                    const searchInput = document.getElementById('search-input');
                    if (searchInput.value) {
                        searchInput.value = '';
                        document.getElementById('clear-search').style.display = 'none';
                        this.clearSearch();
                    }
                    break;
                case '1':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.showCategory('all');
                        this.setActiveNav(document.querySelector('[data-category="all"]'));
                    }
                    break;
                case '2':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.showCategory('latest');
                        this.setActiveNav(document.querySelector('[data-category="latest"]'));
                    }
                    break;
            }
        });
    }

    updateURL(category) {
        const url = new URL(window.location);
        if (category === 'all') {
            url.searchParams.delete('category');
        } else {
            url.searchParams.set('category', category);
        }
        window.history.replaceState({}, '', url);
    }

    trackCategoryView(category) {
        // Analytics tracking placeholder
        console.log(`Category viewed: ${category}`);
    }

    updateLastRefresh() {
        const updateInfo = document.querySelector('.update-info');
        if (updateInfo) {
            const now = new Date();
            const timeString = now.toLocaleString();
            updateInfo.innerHTML = `<i class="fas fa-clock"></i> Last viewed: ${timeString}`;
        }
    }

    // Auto-refresh functionality (optional)
    setupAutoRefresh(intervalMinutes = 30) {
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                window.location.reload();
            }
        }, intervalMinutes * 60 * 1000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new IBMDashboard();
    
    // Check for category in URL
    const urlParams = new URLSearchParams(window.location.search);
    const category = urlParams.get('category');
    if (category) {
        dashboard.showCategory(category);
        const navBtn = document.querySelector(`[data-category="${category}"]`);
        if (navBtn) {
            dashboard.setActiveNav(navBtn);
        }
    }
    
    // Setup auto-refresh (optional - uncomment if needed)
    // dashboard.setupAutoRefresh(30); // 30 minutes
});

// Add mark styling for search highlights
document.addEventListener('DOMContentLoaded', () => {
    const markStyles = `
        mark {
            background: linear-gradient(90deg, var(--accent-color), #ffab40);
            color: white;
            padding: 0.1rem 0.2rem;
            border-radius: 3px;
            font-weight: 600;
        }
    `;
    
    const style = document.createElement('style');
    style.textContent = markStyles;
    document.head.appendChild(style);
});
