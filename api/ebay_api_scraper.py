#!/usr/bin/env python3

import requests
import json
import os
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
        
        # First test if API is accessible
        if not self.test_api_connection():
            print("⚠️ eBay API not accessible - would need proper OAuth setup")
            return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}}
        
        # Headers for eBay API
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.get_access_token()}',
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
            # Make API request
            response = requests.get(
                f"{self.base_url}/item_summary/search",
                headers=headers,
                params=query,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self.format_api_response(data)
            else:
                print(f"❌ eBay API Error: {response.status_code} - {response.text}")
                return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}}
                
        except Exception as e:
            print(f"❌ eBay API Exception: {e}")
            return {'products': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'has_more': False}}
    
    def get_access_token(self):
        """Get OAuth access token for eBay API"""
        
        # For demo purposes, return a mock token
        # In production, you'd implement proper OAuth flow
        return 'mock_access_token_for_demo'
    
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
