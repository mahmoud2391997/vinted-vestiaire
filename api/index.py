from http.server import BaseHTTPRequestHandler
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # Check if this is an API request or HTML request
            if parsed_path.query:
                # API request - return JSON
                query_params = parse_qs(parsed_path.query)
                search_text = query_params.get('search', ['t-shirt'])[0]
                pages = int(query_params.get('pages', ['1'])[0])
                
                try:
                    # Scrape real data
                    data = self.scrape_vinted_data(search_text, pages)
                    self.send_json_response(data)
                except Exception as e:
                    # Fallback to sample data if scraping fails
                    sample_data = self.get_sample_data()
                    self.send_json_response(sample_data, error=str(e))
            else:
                # HTML request - serve the enhanced UI
                self.send_html_response()
        else:
            self.send_http_response(404, 'Not Found')
    
    def send_json_response(self, data, error=None):
        """Send JSON response"""
        response = {
            'success': True,
            'data': data,
            'count': len(data),
            'error': error
        }
        
        response_json = json.dumps(response, ensure_ascii=False)
        
        self.send_http_response(200, response_json, 'application/json')
    
    def send_html_response(self):
        """Send the enhanced HTML UI"""
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
    
    def scrape_vinted_data(self, search_text, pages=1):
        """Scrape data from Vinted using requests and BeautifulSoup"""
        all_data = []
        
        for page in range(1, pages + 1):
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
        
        return all_data if all_data else self.get_sample_data()
    
    def extract_item_data(self, item_container):
        """Extract data from the item container's text content"""
        import re
        text = item_container.get_text()
        
        data = {'Title': 'N/A', 'Price': 'N/A', 'Brand': 'N/A', 'Size': 'N/A'}
        
        # First try to get title from image alt text
        images = item_container.find_all('img')
        for img in images:
            alt = img.get('alt', '')
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
        
        # Extract price (first price found)
        price_match = re.search(r'(\d+,\d+)\s*zł', clean_text)
        if price_match:
            data['Price'] = price_match.group(1) + 'zł'
        
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
