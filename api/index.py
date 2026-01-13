from http.server import BaseHTTPRequestHandler
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode
import re

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            query_params = parse_qs(parsed_path.query)
            
            # Extract parameters
            search_text = query_params.get('search', [''])[0]
            brand = query_params.get('brand', [''])[0]
            category = query_params.get('category', [''])[0]
            min_price = query_params.get('min_price', [''])[0]
            max_price = query_params.get('max_price', [''])[0]
            country = query_params.get('country', ['pl'])[0] # Default to Poland
            pages = int(query_params.get('pages', ['1'])[0])

            try:
                # Scrape data with the new parameters
                data = self.scrape_vinted_data(
                    search_text=search_text,
                    brand=brand,
                    category=category,
                    min_price=min_price,
                    max_price=max_price,
                    country=country,
                    pages=pages
                )
                self.send_json_response(data)
            except Exception as e:
                self.send_json_response([], error=str(e), status_code=500)
        else:
            self.send_http_response(404, 'Not Found', 'text/plain')

    def send_json_response(self, data, error=None, status_code=200):
        response = {
            'success': error is None,
            'data': data,
            'count': len(data),
            'error': error
        }
        response_json = json.dumps(response, ensure_ascii=False)
        self.send_http_response(status_code, response_json, 'application/json')

    def send_http_response(self, status_code, content, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', f'{content_type}; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def scrape_vinted_data(self, search_text, brand, category, min_price, max_price, country, pages):
        all_data = []
        
        # Combine search terms for a more effective search
        full_search_text = f'{search_text} {brand} {category}'.strip()

        for page in range(1, pages + 1):
            try:
                # Build Vinted URL with all parameters
                base_url = f'https://www.vinted.{country}/catalog'
                params = {
                    'search_text': full_search_text,
                    'price_from': min_price,
                    'price_to': max_price,
                    'page': page
                }
                # Clean up parameters - remove any that are empty
                params = {k: v for k, v in params.items() if v}
                
                url = f'{base_url}?{urlencode(params)}'
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Vinted embeds its data in a script tag as JSON. This is more reliable than scraping visible HTML.
                script_tag = soup.find('script', {'data-js-react-on-rails-store': 'MainStore'})
                if not script_tag:
                    break # Stop if the data structure isn't found

                json_data = json.loads(script_tag.string)
                items = json_data.get('items', {}).get('byId', {})

                if not items:
                    break

                for item_id, item_details in items.items():
                    # Filter out items that are not visible or are reserved
                    if item_details and item_details.get('is_visible') and not item_details.get('is_reserved'):
                        all_data.append({
                            'Title': item_details.get('title', 'N/A'),
                            'Price': item_details.get('price', 'N/A'),
                            'Currency': item_details.get('currency', 'N/A'),
                            'Brand': item_details.get('brand_title', 'N/A'),
                            'Size': item_details.get('size_title', 'N/A'),
                            'URL': item_details.get('url', '#'),
                            'ImageURL': item_details.get('photo', {}).get('url', '')
                        })

            except requests.exceptions.RequestException as e:
                raise Exception(f'Failed to fetch data from Vinted: {e}')
            except Exception as e:
                raise Exception(f'Error processing page {page}: {e}')
        
        return all_data
