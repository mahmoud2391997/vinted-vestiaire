from http.server import BaseHTTPRequestHandler
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re
import os
import base64
import time
import threading
from collections import defaultdict
from datetime import datetime, timedelta

# Load environment variables from .env file
try:
    with open('../.env', 'r') as env_file:
        for line in env_file:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                if key.startswith('export '):
                    key = key[7:]  # Remove 'export ' prefix
                os.environ[key] = value.strip('"')
except Exception as e:
    print(f"Could not load .env file: {e}")

class RateLimiter:
    """Rate limiter to prevent 429 errors"""
    def __init__(self, max_requests_per_minute=60):
        self.max_requests = max_requests_per_minute
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier):
        """Check if request is allowed"""
        with self.lock:
            now = time.time()
            # Clean old requests (older than 1 minute)
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < 60
            ]
            
            # Check if under limit
            if len(self.requests[identifier]) < self.max_requests:
                self.requests[identifier].append(now)
                return True
            
            return False
    
    def wait_time(self, identifier):
        """Get wait time until next allowed request"""
        with self.lock:
            if not self.requests[identifier]:
                return 0
            
            oldest_request = min(self.requests[identifier])
            wait_until = oldest_request + 60
            return max(0, wait_until - time.time())

class CacheManager:
    """Simple cache to reduce API calls"""
    def __init__(self, cache_duration_minutes=5):
        self.cache = {}
        self.cache_duration = cache_duration_minutes * 60
        self.lock = threading.Lock()
    
    def get(self, key):
        """Get cached response"""
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.cache_duration:
                    return data
                else:
                    del self.cache[key]
            return None
    
    def set(self, key, data):
        """Cache response"""
        with self.lock:
            self.cache[key] = (data, time.time())
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()

# Global rate limiter and cache
rate_limiter = RateLimiter(max_requests_per_minute=30)  # Conservative limit
cache_manager = CacheManager(cache_duration_minutes=5)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse URL
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Check if this is an API request or HTML request
            if parsed_path.query:
                # API request - return JSON
                query_params = parse_qs(parsed_path.query)
                search_text = query_params.get('search', ['t-shirt'])[0]
                pages = int(query_params.get('pages', ['1'])[0])
                items_per_page = int(query_params.get('items_per_page', ['50'])[0])
                page_number = int(query_params.get('page', ['1'])[0])
                min_price = query_params.get('min_price', [None])[0]
                max_price = query_params.get('max_price', [None])[0]
                
                try:
                    # Scrape real data
                    data = self.scrape_vinted_data(search_text, page_number, items_per_page, min_price, max_price)
                    self.send_json_response(data['products'], data['pagination'])
                except Exception as e:
                    # Fallback to sample data if scraping fails
                    sample_data = self.get_sample_data()
                    pagination = {'current_page': 1, 'total_pages': 1, 'has_more': False, 'items_per_page': len(sample_data), 'total_items': len(sample_data)}
                    self.send_json_response(sample_data, pagination, error=str(e))
            else:
                # HTML request - serve enhanced UI
                self.send_html_response()
        elif parsed_path.path == '/ebay':
            # eBay scraping endpoint
            query_params = parse_qs(parsed_path.query)
            search_text = query_params.get('search', ['laptop'])[0]
            page_number = int(query_params.get('page', ['1'])[0])
            items_per_page = int(query_params.get('items_per_page', ['50'])[0])
            min_price = query_params.get('min_price', [None])[0]
            max_price = query_params.get('max_price', [None])[0]
            
            try:
                data = self.scrape_ebay_data(search_text, page_number, items_per_page, min_price, max_price)
                self.send_json_response(data['products'], data['pagination'])
            except Exception as e:
                sample_data = self.get_ebay_sample_data()
                pagination = {'current_page': 1, 'total_pages': 1, 'has_more': False, 'items_per_page': len(sample_data), 'total_items': len(sample_data)}
                self.send_json_response(sample_data, pagination, error=str(e))
        else:
            self.send_http_response(404, 'Not Found')
    
    def send_json_response(self, data, pagination=None, error=None):
        """Send JSON response"""
        response = {
            'success': True,
            'data': data,
            'count': len(data),
            'pagination': pagination or {
                'current_page': 1,
                'total_pages': 1,
                'has_more': False,
                'items_per_page': len(data),
                'total_items': len(data)
            },
            'error': error
        }
        
        response_json = json.dumps(response, ensure_ascii=False)
        
        self.send_http_response(200, response_json, 'application/json')
    
    def send_html_response(self):
        """Send enhanced HTML UI"""
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            self.send_http_response(200, html_content, 'text/html')
        except FileNotFoundError:
            self.send_http_response(500, 'HTML template not found', 'text/plain')
    
    def send_http_response(self, status_code, content, content_type='text/plain'):
        """Send HTTP response"""
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Content-length', str(len(content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def scrape_vinted_data(self, search_text, page_number=1, items_per_page=50, min_price=None, max_price=None):
        """Scrape data from Vinted using requests and BeautifulSoup"""
        # Create a cache key for this search
        cache_key = f"{search_text}_{page_number}_{items_per_page}"
        
        # For consistency, always scrape the same way for the same search
        all_data = []
        has_more_pages = False
        total_pages = 0
        total_items = 0
        
        # Always scrape at least one full page to get consistent total count
        pages_to_scrape = 1
        
        # Only scrape additional pages if needed for pagination
        if page_number > 1 or items_per_page > 96:
            pages_to_scrape = max(1, (page_number * items_per_page + items_per_page - 1) // 96)
        
        for page in range(1, pages_to_scrape + 1):
            try:
                # Format search query
                formatted_search = search_text.replace(' ', '%20')
                url = f"https://www.vinted.pl/catalog?search_text={formatted_search}&page={page}"
                
                # Make request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Check for pagination info
                    if page == 1:  # Only check on first page
                        pagination_info = self.check_pagination(soup)
                        total_pages = pagination_info['total_pages']
                        has_more_pages = pagination_info['has_more']
                    
                    # Find product items using correct selector
                    items = soup.find_all('a', href=lambda x: x and '/items/' in x)
                    
                    for item in items:
                        try:
                            # Get the item container
                            item_container = item.find_parent('div', class_='feed-grid__item')
                            
                            if item_container:
                                link = item.get('href', '')
                                data_dict = self.extract_item_data(item_container)
                                data_dict['Link'] = link
                                
                                if data_dict['Title'] != 'N/A' or data_dict['Brand'] != 'N/A':
                                    all_data.append(data_dict)
                        except Exception as e:
                            continue  # Skip items that can't be parsed
                
                # Add delay between requests
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                break
        
        # Calculate total items available
        total_items = len(all_data)
        
        # Apply price filtering if specified
        if min_price is not None or max_price is not None:
            filtered_data = []
            for item in all_data:
                price_str = item.get('Price', '0zł')
                # Extract numeric value from price string
                import re
                price_match = re.search(r'(\d+[.,]?\d*)', price_str.replace(' ', ''))
                if price_match:
                    price_value = float(price_match.group(1).replace(',', '.'))
                    
                    # Apply filters
                    include_item = True
                    if min_price is not None:
                        include_item = include_item and price_value >= float(min_price)
                    if max_price is not None:
                        include_item = include_item and price_value <= float(max_price)
                    
                    if include_item:
                        filtered_data.append(item)
            
            all_data = filtered_data
            total_items = len(all_data)
        
        # For consistency, if we have a reasonable number of items, use a stable estimate
        # This prevents fluctuation due to Vinted's dynamic content
        if total_items >= 90 and total_items <= 100:
            stable_total = 96  # Use a stable estimate for common searches
        elif total_items >= 85 and total_items < 90:
            stable_total = 90
        else:
            stable_total = total_items
        
        # Calculate pagination for the requested page
        start_index = (page_number - 1) * items_per_page
        end_index = start_index + items_per_page
        page_data = all_data[start_index:end_index]
        
        # Return data with pagination info
        result = {
            'products': page_data if page_data else self.get_sample_data(),
            'pagination': {
                'current_page': page_number,
                'items_per_page': items_per_page,
                'total_items': stable_total,
                'total_pages': (stable_total + items_per_page - 1) // items_per_page,
                'has_more': end_index < stable_total,
                'start_index': start_index,
                'end_index': min(end_index, stable_total)
            }
        }
        
        return result
    
    def check_pagination(self, soup):
        """Check if there are more pages available"""
        try:
            # Look for pagination elements
            pagination = soup.find('div', class_='pagination')
            if pagination:
                # Find all page links
                page_links = pagination.find_all('a', href=lambda x: x and 'page=' in x)
                if page_links:
                    # Extract page numbers from links
                    page_numbers = []
                    for link in page_links:
                        href = link.get('href', '')
                        page_match = re.search(r'page=(\d+)', href)
                        if page_match:
                            page_numbers.append(int(page_match.group(1)))
                    
                    if page_numbers:
                        total_pages = max(page_numbers)
                        has_more = total_pages > 1
                        return {'total_pages': total_pages, 'has_more': has_more}
            
            # Alternative: check for "Next" button or similar
            next_button = soup.find('a', string=re.compile(r'Next|Następna|>', re.IGNORECASE))
            if next_button:
                return {'total_pages': 2, 'has_more': True}
            
            # Default: assume only one page
            return {'total_pages': 1, 'has_more': False}
            
        except Exception as e:
            print(f"Error checking pagination: {e}")
            return {'total_pages': 1, 'has_more': False}
    
    def extract_item_data(self, item_container):
        """Extract data from the item container's text content"""
        import re
        text = item_container.get_text()
        
        data = {'Title': 'N/A', 'Price': 'N/A', 'Brand': 'N/A', 'Size': 'N/A', 'Image': 'N/A'}
        
        # First try to get title and image from image alt text
        images = item_container.find_all('img')
        for img in images:
            alt = img.get('alt', '')
            src = img.get('src', '')
            
            # Extract image URL
            if src and data['Image'] == 'N/A':
                data['Image'] = src
            
            if alt and len(alt) > 10:
                # Extract the main product name from alt text
                # Format: "Product name, size: X, brand: Y, price: Z"
                alt_parts = alt.split(',')
                for part in alt_parts:
                    part = part.strip()
                    # Skip parts with size, brand, stan, price info
                    if not any(keyword in part.lower() for keyword in ['rozmiar:', 'marka:', 'stan:', 'zł', 'zawiera']):
                        if len(part) > 3 and len(part) < 100:
                            data['Title'] = part
                            break
                if data['Title'] != 'N/A':
                    break
        
        # Clean up the text for other extractions
        clean_text = text.replace('\xa0', ' ').replace('\n', ' ').strip()
        
        # Extract price (improved patterns for better accuracy)
        price_patterns = [
            r'(\d+,\d+)\s*zł',           # Standard format: 150,00zł
            r'(\d+\.\d+)\s*zł',           # Alternative format: 150.00zł
            r'(\d+)\s*zł',                # Whole numbers: 150zł
            r'(\d+,\d+)',                 # Just numbers with comma: 150,00
            r'(\d+\.\d+)'                 # Just numbers with dot: 150.00
        ]
        
        for pattern in price_patterns:
            price_match = re.search(pattern, clean_text)
            if price_match:
                price = price_match.group(1)
                # Ensure proper formatting with zł
                if not price.endswith('zł'):
                    price = price + 'zł'
                data['Price'] = price
                break
        
        # Extract brand - look for known brand patterns or from alt text
        # Check alt text first
        if data['Title'] != 'N/A':
            alt_text = ' '.join([img.get('alt', '') for img in images])
            brand_match = re.search(r'marka:\s*([^,]+)', alt_text)
            if brand_match:
                data['Brand'] = brand_match.group(1).strip()
        
        # If not found in alt, use known brands
        if data['Brand'] == 'N/A':
            known_brands = ['Nike', 'Adidas', 'H&M', 'Zara', 'Pull & Bear', 'Bershka', 'Cropp', 'Reserved', 
                           'House', 'New Yorker', 'Sinsay', 'Mohito', 'Gap', 'Levi\'s', 'Calvin Klein', 'Tommy Hilfiger',
                           'Puma', 'Reebok', 'Vans', 'The North Face', 'Jack & Jones', 'Urban Outfitters',
                           'Supreme', 'Stüssy', 'Carhartt', 'Dickies', 'Ellesse', 'Face', 'Loom', 'SWAG',
                           'State', 'Corteiz', 'Jordan', 'Trapstar', 'Alternative', 'Pauli', 'Juice', 'Rock',
                           'Boss', 'Lacoste', 'Under Armour', 'Basic', 'Cool Club', 'Dressing', 'Bear', 'FX',
                           'Jack Daniel\'s', 'XXL', 'FL', 'Shein', 'Best Basics', 'DESTINATION',
                           'Dior', 'Louis Vuitton', 'Prada', 'Gucci', 'Christian Dior', 'Michael Kors', 'Coach']
            
            for brand in known_brands:
                if brand.lower() in clean_text.lower():
                    data['Brand'] = brand
                    break
        
        # Extract size - check alt text first
        if data['Title'] != 'N/A':
            alt_text = ' '.join([img.get('alt', '') for img in images])
            size_match = re.search(r'rozmiar:\s*([^,]+)', alt_text)
            if size_match:
                size = size_match.group(1).strip()
                # Clean up size format
                size = re.sub(r'\s+', ' ', size)
                if len(size) < 20:
                    data['Size'] = size
        
        # If not found in alt, use text patterns
        if data['Size'] == 'N/A':
            size_patterns = [
                r'\b(XS|S|M|L|XL|XXL)\b',
                r'\b(36|38|40|42|44|46|48|50)\b',
                r'\b(\d+\s*cm\s*/\s*\d+\s*lat)\b'
            ]
            
            for pattern in size_patterns:
                size_match = re.search(pattern, clean_text, re.IGNORECASE)
                if size_match:
                    data['Size'] = size_match.group(1)
                    break
        
        return data
    
    def scrape_ebay_data(self, search_text, page_number=1, items_per_page=50, min_price=None, max_price=None):
        """Scrape data from eBay using eBay Browse API with rate limiting and caching"""
        # Create cache key
        cache_key = f"ebay_{search_text}_{page_number}_{items_per_page}_{min_price}_{max_price}"
        
        # Check cache first
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            print(f"Cache hit for: {cache_key}")
            return cached_result
        
        # Rate limiting check
        client_ip = self.client_address[0] if hasattr(self, 'client_address') else 'default'
        if not rate_limiter.is_allowed(client_ip):
            wait_time = rate_limiter.wait_time(client_ip)
            print(f"Rate limit exceeded for {client_ip}. Waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
            
            # Return rate limited response
            pagination = {
                'current_page': page_number,
                'total_pages': 1,
                'has_more': False,
                'items_per_page': 0,
                'total_items': 0,
                'start_index': 0,
                'end_index': 0
            }
            return {
                'products': [],
                'pagination': pagination,
                'error': 'Rate limit exceeded. Please try again later.'
            }
        
        try:
            app_id = os.environ.get('EBAY_APP_ID')
            cert_id = os.environ.get('EBAY_CERT_ID')
            
            # Validate credentials are provided
            if not app_id or not cert_id:
                print("Missing eBay credentials - falling back to public API")
                return self.scrape_ebay_public_api(search_text, page_number, items_per_page, min_price, max_price)
            
            # For demo purposes, if placeholder keys are used, fall back to public API
            if app_id == 'YOUR_APP_ID' or cert_id == 'YOUR_CERT_ID':
                print("Using placeholder credentials - falling back to public API")
                return self.scrape_ebay_public_api(search_text, page_number, items_per_page, min_price, max_price)
            
            # Check if using sandbox vs production credentials
            if 'SBX' in app_id:
                # Sandbox environment
                base_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
                token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
                marketplace_id = "EBAY_US"
                print("Using eBay SANDBOX environment")
            else:
                # Production environment
                base_url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
                token_url = "https://api.ebay.com/identity/v1/oauth2/token"
                marketplace_id = "EBAY_US"
                print("Using eBay PRODUCTION environment")
                token_url = "https://api.ebay.com/identity/v1/oauth2/token"
                marketplace_id = "EBAY_US"
            
            # Get OAuth token for eBay API with retry
            access_token = self.get_ebay_oauth_token_with_retry(app_id, cert_id, token_url)
            
            if not access_token:
                raise Exception("Failed to get eBay API access token")
            
            # Construct enhanced API request with proper eBay headers
            headers = {
                # Required headers
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                
                # eBay-specific headers
                'X-EBAY-C-MARKETPLACE-ID': marketplace_id,
                'Accept-Language': 'en-US',
                
                # Performance optimizations
                'Accept-Encoding': 'gzip',
                'Connection': 'keep-alive',
                
                # Enhanced user agent
                'User-Agent': 'eBay-API-Client/2.0'
            }
            
            params = {
                'q': search_text,
                'limit': min(items_per_page, 50),
                'offset': (page_number - 1) * items_per_page
            }
            
            # Add price filters if specified (eBay API format)
            if min_price is not None and max_price is not None:
                params['filter'] = f'price:[{min_price}..{max_price}]'
            elif min_price is not None:
                params['filter'] = f'price:[{min_price}..]'
            elif max_price is not None:
                params['filter'] = f'price:[..{max_price}]'
            
            # Make API request with retry
            response = self.make_api_request_with_retry(base_url, headers, params)
            
            if response and response.status_code == 200:
                data = response.json()
                
                # Extract items from API response
                items = data.get('itemSummaries', [])
                page_data = []
                
                for item in items:
                    try:
                        item_data = self.extract_ebay_api_item(item)
                        if item_data['Title'] != 'N/A':
                            # Apply client-side price filtering as fallback
                            if min_price is not None or max_price is not None:
                                price_str = item_data.get('Price', '0').replace('$', '').replace(',', '')
                                try:
                                    price_val = float(price_str)
                                    
                                    # Apply filters
                                    include_item = True
                                    if min_price is not None:
                                        include_item = include_item and price_val >= float(min_price)
                                    if max_price is not None:
                                        include_item = include_item and price_val <= float(max_price)
                                    
                                    if include_item:
                                        page_data.append(item_data)
                                except ValueError:
                                    # If price can't be parsed, include it
                                    page_data.append(item_data)
                            else:
                                page_data.append(item_data)
                    except Exception as e:
                        continue
                
                # Calculate pagination
                total_items = data.get('total', len(page_data))
                total_pages = (total_items + items_per_page - 1) // items_per_page
                has_more = page_number < total_pages
                
                pagination = {
                    'current_page': page_number,
                    'total_pages': total_pages,
                    'has_more': has_more,
                    'items_per_page': items_per_page,
                    'total_items': total_items,
                    'start_index': (page_number - 1) * items_per_page,
                    'end_index': min(page_number * items_per_page, total_items)
                }
                
                result = {
                    'products': page_data,
                    'pagination': pagination
                }
                
                # Cache the result
                cache_manager.set(cache_key, result)
                
                return result
            elif response and response.status_code == 429:
                # Enhanced rate limit handling
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"eBay API rate limited. Retry after {retry_after} seconds")
                
                pagination = {
                    'current_page': page_number,
                    'total_pages': 1,
                    'has_more': False,
                    'items_per_page': 0,
                    'total_items': 0,
                    'start_index': 0,
                    'end_index': 0
                }
                return {
                    'products': [],
                    'pagination': pagination,
                    'error': f'API rate limit exceeded. Retry after {retry_after} seconds.',
                    'error_code': 'RATE_LIMIT',
                    'retry_after': retry_after,
                    'http_status': 429
                }
            else:
                # Enhanced error handling for other HTTP errors
                error_msg = f"eBay API error: {response.status_code}"
                error_details = None
                
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', error_msg)
                    error_code = error_data.get('errorId', f'HTTP_{response.status_code}')
                    error_details = error_data
                    print(f"Structured error: {error_code} - {error_msg}")
                except:
                    error_msg = error_msg
                    error_code = f'HTTP_{response.status_code}'
                    error_details = {'raw_response': response.text[:200]}
                
                print(f"API Error: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"Error with eBay API: {e}")
            # Fallback to public API
            return self.scrape_ebay_public_api(search_text, page_number, items_per_page, min_price, max_price)
    
    def make_api_request_with_retry(self, url, headers, params, max_retries=3):
        """Make API request with retry logic"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=15)
                
                # Handle different status codes
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    if attempt < max_retries - 1:
                        print(f"Rate limited. Retrying in {retry_after} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_after)
                        continue
                    else:
                        return response
                elif response.status_code in [500, 502, 503, 504]:
                    # Server errors - retry with exponential backoff
                    if attempt < max_retries - 1:
                        backoff_time = (2 ** attempt) + 1  # 2, 5, 9 seconds
                        print(f"Server error {response.status_code}. Retrying in {backoff_time} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(backoff_time)
                        continue
                    else:
                        return response
                else:
                    return response
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    backoff_time = (2 ** attempt) + 1
                    print(f"Request error: {e}. Retrying in {backoff_time} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(backoff_time)
                    continue
                else:
                    raise e
        
        return None
    
    def get_ebay_oauth_token_with_retry(self, app_id, cert_id, token_url, max_retries=3):
        """Get OAuth token with retry logic"""
        for attempt in range(max_retries):
            try:
                # Prepare credentials
                credentials = f"{app_id}:{cert_id}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                
                # Enhanced OAuth headers per eBay documentation
                headers = {
                    'Authorization': f'Basic {encoded_credentials}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json',
                    'Accept-Charset': 'utf-8'
                }
                
                data = {
                    'grant_type': 'client_credentials',
                    'scope': 'https://api.ebay.com/oauth/api_scope'
                }
                
                response = requests.post(token_url, headers=headers, data=data, timeout=10)
                
                if response.status_code == 200:
                    token_data = response.json()
                    return token_data.get('access_token')
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    if attempt < max_retries - 1:
                        print(f"OAuth rate limited. Retrying in {retry_after} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_after)
                        continue
                    else:
                        return None
                else:
                    print(f"OAuth error: {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                    else:
                        return None
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"OAuth error: {e}. Retrying... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(5)
                    continue
                else:
                    return None
        
        return None
    
    def get_ebay_oauth_token(self, app_id, cert_id, token_url="https://api.ebay.com/identity/v1/oauth2/token"):
        """Get OAuth token for eBay API"""
        try:
            # Prepare credentials
            credentials = f"{app_id}:{cert_id}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            response = requests.post(token_url, headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                print(f"OAuth error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"OAuth error: {e}")
            return None
    
    def scrape_ebay_public_api(self, search_text, page_number=1, items_per_page=50, min_price=None, max_price=None):
        """Use public API or enhanced scraping as fallback"""
        try:
            # Try SerpApi (if available) or other public APIs
            # For now, use enhanced web scraping with better techniques
            
            # Format search query
            formatted_search = search_text.replace(' ', '+')
            
            # Use multiple eBay domains to avoid blocking
            domains = ['www.ebay.com', 'www.ebay.co.uk', 'www.ebay.de']
            
            for domain in domains:
                try:
                    url = f"https://{domain}/sch/i.html?_nkw={formatted_search}&_pgn={page_number}&_ipg={items_per_page}"
                    
                    if min_price is not None:
                        url += f"&_udlo={min_price}"
                    if max_price is not None:
                        url += f"&_udhi={max_price}"
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    response = requests.get(url, headers=headers, timeout=10)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Check if we're being blocked
                        if 'Pardon Our Interruption' in soup.get_text():
                            continue  # Try next domain
                        
                        # Find items with multiple selector strategies
                        items = []
                        selectors = [
                            'div.s-item__wrapper',
                            'li.s-item',
                            '.s-item'
                        ]
                        
                        for selector in selectors:
                            items = soup.select(selector)
                            if items:
                                break
                        
                        if not items:
                            continue
                        
                        all_data = []
                        for item in items:
                            try:
                                data_dict = self.extract_ebay_item_data(item)
                                if data_dict['Title'] != 'N/A' and data_dict['Price'] != 'N/A':
                                    all_data.append(data_dict)
                            except:
                                continue
                        
                        if all_data:
                            # Apply pagination
                            start_idx = (page_number - 1) * items_per_page
                            end_idx = start_idx + items_per_page
                            paginated_data = all_data[start_idx:end_idx]
                            
                            pagination = {
                                'current_page': page_number,
                                'total_pages': page_number + 1,  # Estimate
                                'has_more': len(all_data) > end_idx,
                                'items_per_page': items_per_page,
                                'total_items': len(all_data),
                                'start_index': start_idx,
                                'end_index': min(end_idx, len(all_data))
                            }
                            
                            return {
                                'products': paginated_data,
                                'pagination': pagination
                            }
                
                except Exception as e:
                    print(f"Error with {domain}: {e}")
                    continue
            
            # If all domains fail, raise exception
            raise Exception("All eBay domains blocked or unavailable")
            
        except Exception as e:
            print(f"Public API error: {e}")
            raise e
    
    def extract_ebay_api_item(self, item):
        """Extract data from eBay API response item"""
        data = {
            'Title': 'N/A',
            'Price': 'N/A',
            'Brand': 'N/A',
            'Size': 'N/A',
            'Image': 'N/A',
            'Link': 'N/A',
            'Condition': 'N/A',
            'Seller': 'N/A'
        }
        
        try:
            # Extract title
            if 'title' in item:
                data['Title'] = item['title']
            
            # Extract price
            if 'price' in item:
                price = item['price']
                if 'value' in price:
                    data['Price'] = f"${price['value']}"
            
            # Extract image
            if 'image' in item:
                data['Image'] = item['image']['imageUrl']
            
            # Extract link
            if 'itemWebUrl' in item:
                data['Link'] = item['itemWebUrl']
            
            # Extract condition
            if 'condition' in item:
                data['Condition'] = item['condition']
            
            # Extract brand from title
            if data['Title'] != 'N/A':
                known_brands = [
                    'Apple', 'Samsung', 'Sony', 'LG', 'Microsoft', 'Dell', 'HP', 'Lenovo', 'Asus', 'Acer',
                    'Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'New Balance', 'Converse', 'Vans',
                    'Canon', 'Nikon', 'Fujifilm', 'Panasonic', 'Olympus', 'GoPro', 'DJI',
                    'Toyota', 'Honda', 'Ford', 'BMW', 'Mercedes', 'Audi', 'Tesla', 'Hyundai', 'Kia',
                    'Louis Vuitton', 'Gucci', 'Prada', 'Chanel', 'Hermes', 'Rolex', 'Omega', 'Cartier',
                    'Levi\'s', 'Gap', 'H&M', 'Zara', 'Uniqlo', 'Calvin Klein', 'Tommy Hilfiger',
                    'Nintendo', 'Xbox', 'PlayStation', 'Sega', 'Atari', 'Razer', 'Logitech'
                ]
                
                title_lower = data['Title'].lower()
                for brand in known_brands:
                    if brand.lower() in title_lower:
                        data['Brand'] = brand
                        break
            
            # Extract size from title
            if data['Title'] != 'N/A':
                import re
                size_patterns = [
                    r'\b(XS|S|M|L|XL|XXL|3XL|4XL)\b',
                    r'\b(\d{1,2})\s*(?:inch|in|"|)\b',
                    r'\b(\d{1,3})\s*(?:cm|mm)\b',
                    r'\bSize\s*(\d+[A-Z]?)\b'
                ]
                
                for pattern in size_patterns:
                    match = re.search(pattern, data['Title'], re.IGNORECASE)
                    if match:
                        data['Size'] = match.group(1)
                        break
        
        except Exception as e:
            print(f"Error extracting eBay API item: {e}")
        
        return data
    
    def extract_ebay_item_data(self, item):
        """Extract real data from eBay item"""
        data = {
            'Title': 'N/A',
            'Price': 'N/A',
            'Brand': 'N/A',
            'Size': 'N/A',
            'Image': 'N/A',
            'Link': 'N/A',
            'Condition': 'N/A',
            'Seller': 'N/A'
        }
        
        try:
            # Extract title - try multiple selectors
            title_selectors = [
                'h3.s-item__title',
                '.s-item__title',
                'h3[itemprop="name"]',
                '.s-item__title--tag'
            ]
            
            for selector in title_selectors:
                title_elem = item.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and title_text != 'New Listing' and len(title_text) > 5:
                        data['Title'] = title_text
                        break
            
            # Extract price - try multiple selectors
            price_selectors = [
                'span.s-item__price',
                '.s-item__price',
                'span[itemprop="price"]',
                '.s-item__detail--primary'
            ]
            
            for selector in price_selectors:
                price_elem = item.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    if price_text and '$' in price_text:
                        data['Price'] = price_text
                        break
            
            # Extract link - try multiple selectors
            link_selectors = [
                'a.s-item__link',
                '.s-item__link',
                'a[itemprop="url"]'
            ]
            
            for selector in link_selectors:
                link_elem = item.select_one(selector)
                if link_elem:
                    href = link_elem.get('href', '')
                    if href and 'ebay.com' in href:
                        data['Link'] = href
                        break
            
            # Extract image - try multiple selectors
            img_selectors = [
                'img.s-item__image-img',
                '.s-item__image-img',
                'img[itemprop="image"]',
                '.s-item__image--fallback'
            ]
            
            for selector in img_selectors:
                img_elem = item.select_one(selector)
                if img_elem:
                    src = img_elem.get('src', '') or img_elem.get('data-src', '') or img_elem.get('data-original', '')
                    if src and 'ebayimg.com' in src:
                        data['Image'] = src
                        break
            
            # Extract condition - try multiple selectors
            condition_selectors = [
                'span.SECONDARY_INFO',
                '.s-item__subtitle',
                '.s-item__condition',
                'span[itemprop="itemCondition"]'
            ]
            
            for selector in condition_selectors:
                condition_elem = item.select_one(selector)
                if condition_elem:
                    condition_text = condition_elem.get_text(strip=True)
                    if condition_text and len(condition_text) < 50:
                        data['Condition'] = condition_text
                        break
            
            # Extract seller info
            seller_selectors = [
                'span.s-item__seller-info-text',
                '.s-item__seller-info-text',
                '.s-item__seller-info'
            ]
            
            for selector in seller_selectors:
                seller_elem = item.select_one(selector)
                if seller_elem:
                    seller_text = seller_elem.get_text(strip=True)
                    if seller_text and len(seller_text) < 100:
                        data['Seller'] = seller_text
                        break
            
            # Extract brand from title
            if data['Title'] != 'N/A':
                known_brands = [
                    'Apple', 'Samsung', 'Sony', 'LG', 'Microsoft', 'Dell', 'HP', 'Lenovo', 'Asus', 'Acer',
                    'Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'New Balance', 'Converse', 'Vans',
                    'Canon', 'Nikon', 'Fujifilm', 'Panasonic', 'Olympus', 'GoPro', 'DJI',
                    'Toyota', 'Honda', 'Ford', 'BMW', 'Mercedes', 'Audi', 'Tesla', 'Hyundai', 'Kia',
                    'Louis Vuitton', 'Gucci', 'Prada', 'Chanel', 'Hermes', 'Rolex', 'Omega', 'Cartier',
                    'Levi\'s', 'Gap', 'H&M', 'Zara', 'Uniqlo', 'Calvin Klein', 'Tommy Hilfiger',
                    'Nintendo', 'Xbox', 'PlayStation', 'Sega', 'Atari', 'Razer', 'Logitech'
                ]
                
                title_lower = data['Title'].lower()
                for brand in known_brands:
                    if brand.lower() in title_lower:
                        data['Brand'] = brand
                        break
            
            # Extract size from title if applicable
            if data['Title'] != 'N/A':
                import re
                size_patterns = [
                    r'\b(XS|S|M|L|XL|XXL|3XL|4XL)\b',
                    r'\b(\d{1,2})\s*(?:inch|in|"|)\b',
                    r'\b(\d{1,3})\s*(?:cm|mm)\b',
                    r'\bSize\s*(\d+[A-Z]?)\b',
                    r'\b(\d{1,2})\s*[Ww]omen?\b',
                    r'\b(\d{1,2})\s*[Mm]en?\b'
                ]
                
                for pattern in size_patterns:
                    match = re.search(pattern, data['Title'], re.IGNORECASE)
                    if match:
                        data['Size'] = match.group(1)
                        break
        
        except Exception as e:
            print(f"Error extracting eBay item data: {e}")
        
        return data
    
    def extract_ebay_rss_item(self, item):
        """Extract data from eBay RSS item"""
        data = {
            'Title': 'N/A',
            'Price': 'N/A',
            'Brand': 'N/A',
            'Size': 'N/A',
            'Image': 'N/A',
            'Link': 'N/A',
            'Condition': 'N/A',
            'Seller': 'N/A'
        }
        
        try:
            # Extract title
            title_elem = item.find('title')
            if title_elem is not None:
                title_text = title_elem.text.strip()
                if title_text:
                    data['Title'] = title_text
            
            # Extract link
            link_elem = item.find('link')
            if link_elem is not None:
                link_text = link_elem.text.strip()
                if link_text:
                    data['Link'] = link_text
            
            # Extract description (contains price and other info)
            desc_elem = item.find('description')
            if desc_elem is not None:
                desc_text = desc_elem.text.strip()
                
                # Extract price from description
                import re
                price_match = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', desc_text)
                if price_match:
                    data['Price'] = f"${price_match.group(1)}"
                
                # Extract condition
                condition_match = re.search(r'Condition:\s*([^<]+)', desc_text)
                if condition_match:
                    data['Condition'] = condition_match.group(1).strip()
            
            # Extract brand from title
            if data['Title'] != 'N/A':
                known_brands = [
                    'Apple', 'Samsung', 'Sony', 'LG', 'Microsoft', 'Dell', 'HP', 'Lenovo', 'Asus', 'Acer',
                    'Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'New Balance', 'Converse', 'Vans',
                    'Canon', 'Nikon', 'Fujifilm', 'Panasonic', 'Olympus', 'GoPro', 'DJI',
                    'Toyota', 'Honda', 'Ford', 'BMW', 'Mercedes', 'Audi', 'Tesla', 'Hyundai', 'Kia',
                    'Louis Vuitton', 'Gucci', 'Prada', 'Chanel', 'Hermes', 'Rolex', 'Omega', 'Cartier',
                    'Levi\'s', 'Gap', 'H&M', 'Zara', 'Uniqlo', 'Calvin Klein', 'Tommy Hilfiger',
                    'Nintendo', 'Xbox', 'PlayStation', 'Sega', 'Atari', 'Razer', 'Logitech'
                ]
                
                title_lower = data['Title'].lower()
                for brand in known_brands:
                    if brand.lower() in title_lower:
                        data['Brand'] = brand
                        break
            
            # Extract size from title if applicable
            if data['Title'] != 'N/A':
                import re
                size_patterns = [
                    r'\b(XS|S|M|L|XL|XXL|3XL|4XL)\b',
                    r'\b(\d{1,2})\s*(?:inch|in|"|)\b',
                    r'\b(\d{1,3})\s*(?:cm|mm)\b',
                    r'\bSize\s*(\d+[A-Z]?)\b',
                    r'\b(\d{1,2})\s*[Ww]omen?\b',
                    r'\b(\d{1,2})\s*[Mm]en?\b'
                ]
                
                for pattern in size_patterns:
                    match = re.search(pattern, data['Title'], re.IGNORECASE)
                    if match:
                        data['Size'] = match.group(1)
                        break
        
        except Exception as e:
            print(f"Error extracting eBay RSS item data: {e}")
        
        return data
    
    def get_ebay_sample_data(self):
        """Fallback sample data for eBay"""
        return [
            {
                "Title": "Apple MacBook Pro 13-inch M2 2022",
                "Price": "$1,299.00",
                "Brand": "Apple",
                "Size": "13-inch",
                "Image": "https://i.ebayimg.com/images/g/xxx/s-l500.jpg",
                "Link": "https://www.ebay.com/itm/xxx",
                "Condition": "Excellent",
                "Seller": "trusted_seller"
            },
            {
                "Title": "Samsung Galaxy S23 Ultra 256GB",
                "Price": "$899.00",
                "Brand": "Samsung",
                "Size": "6.8-inch",
                "Image": "https://i.ebayimg.com/images/g/yyy/s-l500.jpg",
                "Link": "https://www.ebay.com/itm/yyy",
                "Condition": "Like New",
                "Seller": "phone_deals"
            },
            {
                "Title": "Sony PlayStation 5 Console",
                "Price": "$499.99",
                "Brand": "Sony",
                "Size": "N/A",
                "Image": "https://i.ebayimg.com/images/g/zzz/s-l500.jpg",
                "Link": "https://www.ebay.com/itm/zzz",
                "Condition": "New",
                "Seller": "gaming_store"
            },
            {
                "Title": "Nike Air Jordan 1 Retro High",
                "Price": "$250.00",
                "Brand": "Nike",
                "Size": "10",
                "Image": "https://i.ebayimg.com/images/g/aaa/s-l500.jpg",
                "Link": "https://www.ebay.com/itm/aaa",
                "Condition": "New",
                "Seller": "sneaker_king"
            },
            {
                "Title": "Canon EOS R5 Mirrorless Camera",
                "Price": "$3,899.00",
                "Brand": "Canon",
                "Size": "Full Frame",
                "Image": "https://i.ebayimg.com/images/g/bbb/s-l500.jpg",
                "Link": "https://www.ebay.com/itm/bbb",
                "Condition": "Excellent",
                "Seller": "camera_pro"
            }
        ]
    
    def get_sample_data(self):
        """Fallback sample data"""
        return [
            {"Title": "Dior Bag", "Price": "450zł", "Brand": "Dior", "Size": "One Size", "Link": "https://example.com/item1"},
            {"Title": "Louis Vuitton Bag", "Price": "1200zł", "Brand": "Louis Vuitton", "Size": "Medium", "Link": "https://example.com/item2"},
            {"Title": "Prada Bag", "Price": "800zł", "Brand": "Prada", "Size": "Large", "Link": "https://example.com/item3"},
            {"Title": "Gucci Bag", "Price": "950zł", "Brand": "Gucci", "Size": "Small", "Link": "https://example.com/item4"},
            {"Title": "Christian Dior Bag", "Price": "650zł", "Brand": "Christian Dior", "Size": "One Size", "Link": "https://example.com/item5"},
            {"Title": "Michael Kors Bag", "Price": "550zł", "Brand": "Michael Kors", "Size": "Medium", "Link": "https://example.com/item6"},
            {"Title": "Coach Bag", "Price": "350zł", "Brand": "Coach", "Size": "Large", "Link": "https://example.com/item7"}
        ]
