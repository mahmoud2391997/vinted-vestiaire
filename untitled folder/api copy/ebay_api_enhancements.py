"""
eBay API Enhancements Based on Official Documentation
Improvements to make the API more compliant with eBay REST standards
"""

import os
import requests
import base64
import json
from datetime import datetime

class EnhancedeBayAPI:
    """
    Enhanced eBay API implementation following official eBay REST documentation
    """
    
    # eBay API Environments
    PRODUCTION_API = "https://api.ebay.com"
    SANDBOX_API = "https://api.sandbox.ebay.com"
    
    # Marketplace IDs from official documentation
    MARKETPLACE_IDS = {
        'US': 'EBAY_US',
        'GB': 'EBAY_GB', 
        'DE': 'EBAY_DE',
        'CA': 'EBAY_CA',
        'AU': 'EBAY_AU',
        'FR': 'EBAY_FR',
        'IT': 'EBAY_IT',
        'ES': 'EBAY_ES',
        'NL': 'EBAY_NL',
        'BE': 'EBAY_BE',
        'AT': 'EBAY_AT',
        'CH': 'EBAY_CH',
        'PL': 'EBAY_PL',
        'HK': 'EBAY_HK',
        'IE': 'EBAY_IE',
        'MY': 'EBAY_MY',
        'PH': 'EBAY_PH',
        'SG': 'EBAY_SG',
        'TW': 'EBAY_TW',
        'MOTORS_US': 'EBAY_MOTORS_US'
    }
    
    # Language/Locale mappings
    LOCALE_MAPPING = {
        'US': 'en-US',
        'GB': 'en-GB', 
        'DE': 'de-DE',
        'CA': 'en-CA',
        'FR': 'fr-FR',
        'IT': 'it-IT',
        'ES': 'es-ES',
        'NL': 'nl-NL',
        'BE': ['nl-BE', 'fr-BE'],
        'AT': 'de-AT',
        'CH': 'de-CH',
        'PL': 'pl-PL'
    }
    
    def __init__(self, app_id=None, cert_id=None, marketplace='US'):
        self.app_id = app_id or os.environ.get('EBAY_APP_ID')
        self.cert_id = cert_id or os.environ.get('EBAY_CERT_ID')
        self.marketplace = marketplace.upper()
        
        # Determine environment
        if self.app_id and 'SBX' in self.app_id:
            self.base_url = self.SANDBOX_API
            self.environment = 'sandbox'
        else:
            self.base_url = self.PRODUCTION_API
            self.environment = 'production'
            
        self.marketplace_id = self.MARKETPLACE_IDS.get(self.marketplace, 'EBAY_US')
        self.locale = self.LOCALE_MAPPING.get(self.marketplace, 'en-US')
        
    def get_oauth_headers(self):
        """
        Get OAuth token with proper headers per eBay documentation
        """
        token_url = f"{self.base_url}/identity/v1/oauth2/token"
        
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{self.app_id}:{self.cert_id}".encode()).decode()}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Accept-Charset': 'utf-8'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': 'https://api.ebay.com/oauth/api_scope'
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data, timeout=10)
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
            else:
                print(f"OAuth Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"OAuth Exception: {e}")
            return None
    
    def get_api_headers(self, access_token):
        """
        Construct proper API headers per eBay documentation
        """
        return {
            # Required headers
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            
            # eBay-specific headers
            'X-EBAY-C-MARKETPLACE-ID': self.marketplace_id,
            'X-EBAY-C-ENDUSERCTX': f'affiliateCampaignId=<code>,affiliateReferenceId=<reference>',  # Optional
            
            # Recommended headers
            'Accept-Language': self.locale,
            'Accept-Encoding': 'gzip',  # Performance optimization
            'Content-Language': self.locale.split('-')[0],  # Primary language
            
            # Standard headers
            'User-Agent': 'eBay-API-Client/2.0',
            'Connection': 'keep-alive'
        }
    
    def build_search_params(self, search_text, page_number=1, items_per_page=50, 
                       category_ids=None, aspect_filter=None, sort=None):
        """
        Build search parameters with proper URL encoding
        """
        params = {
            'q': search_text,
            'limit': min(items_per_page, 50),  # eBay limit
            'offset': (page_number - 1) * items_per_page
        }
        
        # Optional parameters
        if category_ids:
            params['category_ids'] = category_ids
            
        if aspect_filter:
            params['aspect_filter'] = aspect_filter
            
        if sort:
            params['sort'] = sort
            
        return params
    
    def build_price_filter(self, min_price=None, max_price=None, currency='USD'):
        """
        Build price filter according to eBay format
        """
        if min_price is not None and max_price is not None:
            return f'price:[{min_price}..{max_price}]'
        elif min_price is not None:
            return f'price:[{min_price}..]'
        elif max_price is not None:
            return f'price:[..{max_price}]'
        return None
    
    def search_items(self, search_text, page_number=1, items_per_page=50,
                   min_price=None, max_price=None, category_ids=None):
        """
        Enhanced search with proper eBay API implementation
        """
        # Get OAuth token
        access_token = self.get_oauth_headers()
        if not access_token:
            return {
                'success': False,
                'error': 'Authentication failed',
                'error_code': 'AUTH_ERROR'
            }
        
        # Build request
        headers = self.get_api_headers(access_token)
        params = self.build_search_params(search_text, page_number, items_per_page, category_ids)
        
        # Add price filters
        price_filter = self.build_price_filter(min_price, max_price)
        if price_filter:
            params['filter'] = price_filter
        
        # Make API request
        search_url = f"{self.base_url}/buy/browse/v1/item_summary/search"
        
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return self.format_response(data, page_number, items_per_page)
            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After', 60)
                return {
                    'success': False,
                    'error': f'Rate limit exceeded. Retry after {retry_after} seconds.',
                    'error_code': 'RATE_LIMIT',
                    'retry_after': retry_after
                }
            else:
                return self.format_error_response(response)
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'error_code': 'NETWORK_ERROR'
            }
    
    def format_response(self, data, page_number, items_per_page):
        """
        Format response according to your API structure
        """
        items = data.get('itemSummaries', [])
        formatted_items = []
        
        for item in items:
            formatted_item = {
                'Title': item.get('title', 'N/A'),
                'Price': f"${item.get('price', {}).get('value', 0):.2f}" if item.get('price') else 'N/A',
                'Brand': self.extract_brand(item),
                'Size': self.extract_size(item),
                'Image': item.get('image', {}).get('imageUrl', 'N/A'),
                'Link': item.get('itemWebUrl', 'N/A'),
                'Condition': item.get('condition', 'N/A'),
                'Seller': item.get('seller', {}).get('username', 'N/A'),
                'Category': item.get('categoryId', 'N/A'),
                'ItemID': item.get('itemId', 'N/A')
            }
            formatted_items.append(formatted_item)
        
        total_items = data.get('total', 0)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        return {
            'success': True,
            'data': formatted_items,
            'count': len(formatted_items),
            'pagination': {
                'current_page': page_number,
                'total_pages': total_pages,
                'has_more': page_number < total_pages,
                'items_per_page': items_per_page,
                'total_items': total_items,
                'start_index': (page_number - 1) * items_per_page,
                'end_index': min(page_number * items_per_page, total_items)
            },
            'error': None
        }
    
    def format_error_response(self, response):
        """
        Format error response according to eBay error structure
        """
        try:
            error_data = response.json()
        except:
            error_data = {}
        
        return {
            'success': False,
            'error': error_data.get('message', f'HTTP {response.status_code} error'),
            'error_code': error_data.get('errorId', f'HTTP_{response.status_code}'),
            'http_status': response.status_code,
            'details': error_data
        }
    
    def extract_brand(self, item):
        """
        Extract brand from item data
        """
        # Try different brand fields
        if 'aspect' in item:
            aspects = item['aspect']
            if 'Brand' in aspects:
                return aspects['Brand']
        
        # Fallback to title analysis
        title = item.get('title', '').lower()
        known_brands = ['apple', 'samsung', 'dell', 'hp', 'lenovo', 'asus', 'acer']
        for brand in known_brands:
            if brand in title:
                return brand.capitalize()
        
        return 'N/A'
    
    def extract_size(self, item):
        """
        Extract size from item data
        """
        if 'aspect' in item:
            aspects = item['aspect']
            if 'Size' in aspects:
                return aspects['Size']
        
        return 'N/A'

# Usage example
if __name__ == "__main__":
    # Initialize with environment variables
    api = EnhancedeBayAPI(marketplace='US')
    
    # Test search
    result = api.search_items('laptop', page_number=1, items_per_page=5)
    print(json.dumps(result, indent=2))
