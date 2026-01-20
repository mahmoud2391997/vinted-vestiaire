#!/usr/bin/env python3

import requests
import json
import os
import base64
from datetime import datetime

class eBayAPIScraper:
    """eBay API scraper for production use"""
    
    def __init__(self):
        # Load environment variables
        self.app_id = os.environ.get('EBAY_APP_ID', '-au-PRD-c47e7b8cc-74398d07')
        self.cert_id = os.environ.get('EBAY_CERT_ID', 'PRD-47e7b8cc3c35-9de7-466d-b49f-c75b')
        self.base_url = "https://api.ebay.com/buy/browse/v1"
        
        # Country mappings for eBay API
        self.country_mapping = {
            'us': 'EBAY_US',
            'uk': 'EBAY_GB', 
            'de': 'EBAY_DE',
            'fr': 'EBAY_FR',
            'it': 'EBAY_IT',
            'es': 'EBAY_ES',
            'ca': 'EBAY_CA',
            'au': 'EBAY_AU'
        }
    
    def search_items(self, search_text, country='us', limit=10, min_price=None, max_price=None):
        """Search items using eBay Browse API"""
        
        # Get access token first
        access_token = self.get_access_token()
        if not access_token:
            print("❌ Failed to get eBay API access token")
            return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}}
        
        # Headers for eBay API
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}',
            'X-EBAY-C-MARKETPLACE-ID': self.country_mapping.get(country, 'EBAY_US'),
            'X-EBAY-C-ENDUSERCTX': 'affiliateCampaignId=123&affiliateReferenceId=456'
        }
        
        # Build search query
        query = {
            'q': search_text,
            'limit': str(limit),
            'fieldgroups': 'FULL',  # Get full item details
            'filter': ''
        }
        
        # Add price filters if specified
        filters = []
        if min_price:
            filters.append(f'price:[{min_price}..]')
        if max_price:
            filters.append(f'price:[..{max_price}]')
        
        if filters:
            query['filter'] = ','.join(filters)
        
        try:
            # Make API request with comprehensive error handling
            response = requests.get(
                f"{self.base_url}/item_summary/search",
                headers=headers,
                params=query,
                timeout=15
            )
            
            # Handle different HTTP status codes
            if response.status_code == 200:
                data = response.json()
                return self.format_api_response(data)
            elif response.status_code == 401:
                print("❌ eBay API: Invalid or expired token")
                return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}, 'error': 'Authentication failed'}
            elif response.status_code == 403:
                print("❌ eBay API: Access forbidden - check API permissions")
                return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}, 'error': 'Access forbidden'}
            elif response.status_code == 429:
                print("❌ eBay API: Rate limit exceeded - please try again later")
                return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}, 'error': 'Rate limit exceeded'}
            elif response.status_code == 500:
                print("❌ eBay API: Internal server error - please try again later")
                return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}, 'error': 'Server error'}
            else:
                print(f"❌ eBay API Error: {response.status_code} - {response.text}")
                return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}, 'error': f'API error: {response.status_code}'}
                
        except requests.exceptions.Timeout:
            print("❌ eBay API: Request timeout")
            return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}, 'error': 'Request timeout'}
        except requests.exceptions.ConnectionError:
            print("❌ eBay API: Connection error")
            return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}, 'error': 'Connection error'}
        except requests.exceptions.RequestException as e:
            print(f"❌ eBay API: Request exception: {e}")
            return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}, 'error': 'Request failed'}
        except Exception as e:
            print(f"❌ eBay API: Unexpected error: {e}")
            return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}, 'error': 'Unexpected error'}
    
    def get_access_token(self):
        """Get OAuth access token for eBay API"""
        
        # Load credentials from environment
        app_id = os.getenv('EBAY_APP_ID')
        cert_id = os.getenv('EBAY_CERT_ID')
        
        if not app_id or not cert_id:
            print("❌ Missing eBay API credentials")
            return None
        
        try:
            # eBay OAuth 2.0 token endpoint
            token_url = "https://api.ebay.com/identity/v1/oauth2/token"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()}'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            response = requests.post(token_url, headers=headers, data=data, timeout=15)
            
            # Handle token request errors
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                if access_token:
                    print("✅ Successfully obtained eBay API access token")
                    return access_token
                else:
                    print("❌ Token response missing access token")
                    return None
            elif response.status_code == 400:
                print("❌ Token request: Bad request - check credentials")
                return None
            elif response.status_code == 401:
                print("❌ Token request: Invalid credentials")
                return None
            elif response.status_code == 403:
                print("❌ Token request: Forbidden - check app permissions")
                return None
            elif response.status_code == 429:
                print("❌ Token request: Rate limit exceeded")
                return None
            else:
                print(f"❌ Token request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Token request: Timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("❌ Token request: Connection error")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Token request: Request failed - {e}")
            return None
        except Exception as e:
            print(f"❌ Token request: Unexpected error - {e}")
            return None
    
    def test_api_connection(self):
        """Test if eBay API is accessible"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.get_access_token()}',
                'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
            }
            
            response = requests.get(
                f"{self.base_url}/item_summary/search",
                headers=headers,
                params={'q': 'test', 'limit': '1'},
                timeout=5
            )
            
            return response.status_code == 200
        except:
            return False
    
    def format_api_response(self, api_data):
        """Format eBay API response to match our standard format"""
        
        products = []
        
        if 'itemSummaries' in api_data:
            for item in api_data['itemSummaries']:
                try:
                    # Extract price
                    price = 'N/A'
                    if 'price' in item and 'value' in item['price']:
                        price_value = item['price']['value']
                        price_currency = item['price'].get('currency', 'USD')
                        price = f"{price_currency} {price_value}"
                    
                    # Extract image
                    image = 'N/A'
                    if 'image' in item and 'imageUrl' in item['image']:
                        image = item['image']['imageUrl']
                    
                    # Extract title and brand
                    title = item.get('title', 'N/A')
                    brand = self.extract_brand_from_title(title)
                    
                    # Extract condition
                    condition = item.get('condition', 'N/A')
                    if isinstance(condition, str):
                        condition = condition
                    elif isinstance(condition, dict) and 'conditionName' in condition:
                        condition = condition['conditionName']
                    
                    product = {
                        'Title': title,
                        'Price': price,
                        'Brand': brand,
                        'Size': 'N/A',  # API doesn't always provide size
                        'Image': image,
                        'Link': item.get('itemWebUrl', 'N/A'),
                        'Condition': condition,
                        'Seller': item.get('seller', {}).get('username', 'N/A')
                    }
                    
                    products.append(product)
                    
                except Exception as e:
                    print(f"Error formatting item: {e}")
                    continue
        
        # Pagination
        total_items = len(products)
        pagination = {
            'current_page': 1,
            'total_pages': 1,
            'has_more': False,
            'items_per_page': total_items,
            'total_items': total_items
        }
        
        return {
            'products': products,
            'pagination': pagination
        }
    
    def extract_brand_from_title(self, title):
        """Extract brand from item title"""
        if not title or title == 'N/A':
            return 'N/A'
        
        # Common brand patterns
        brands = [
            'Apple', 'Samsung', 'Nike', 'Adidas', 'Sony', 'LG', 'Microsoft', 
            'Dell', 'HP', 'Canon', 'Nikon', 'Rolex', 'Omega', 'Gucci', 'Prada',
            'Louis Vuitton', 'Chanel', 'Dior', 'Hermès', 'Burberry', 'Coach'
        ]
        
        title_lower = title.lower()
        for brand in brands:
            if brand.lower() in title_lower:
                return brand
        
        return 'N/A'

# Test function
def test_ebay_api():
    """Test eBay API scraper"""
    scraper = eBayAPIScraper()
    
    print("🔍 Testing eBay API scraper...")
    
    # Test search
    result = scraper.search_items('iPhone', country='us', limit=3)
    
    print(f"✅ Found {len(result['products'])} items")
    for i, item in enumerate(result['products'][:3]):
        print(f"{i+1}. {item['Title']}: {item['Price']}")
    
    return result

if __name__ == "__main__":
    test_ebay_api()
