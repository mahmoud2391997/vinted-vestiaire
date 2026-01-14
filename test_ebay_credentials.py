import os
import requests
import base64

# Load environment variables
with open('.env', 'r') as env_file:
    for line in env_file:
        if line.strip() and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            if key.startswith('export '):
                key = key[7:]
            os.environ[key] = value.strip('"')

app_id = os.environ.get('EBAY_APP_ID')
cert_id = os.environ.get('EBAY_CERT_ID')

print(f'App ID: {app_id}')
print(f'Cert ID: {cert_id}')

# Check if using sandbox or production
if 'SBX' in app_id:
    print('Using SANDBOX environment')
    token_url = 'https://api.sandbox.ebay.com/identity/v1/oauth2/token'
else:
    print('Using PRODUCTION environment')
    token_url = 'https://api.ebay.com/identity/v1/oauth2/token'

# Test OAuth token
try:
    credentials = f'{app_id}:{cert_id}'
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'client_credentials',
        'scope': 'https://api.ebay.com/oauth/api_scope'
    }
    
    print('Requesting OAuth token...')
    response = requests.post(token_url, headers=headers, data=data, timeout=10)
    
    print(f'Status Code: {response.status_code}')
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        print(f'✅ OAuth Token obtained successfully!')
        print(f'Token type: {token_data.get("token_type")}')
        print(f'Expires in: {token_data.get("expires_in")} seconds')
        
        # Test a simple API call
        if 'SBX' in app_id:
            search_url = 'https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search'
        else:
            search_url = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
        
        search_headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        params = {'q': 'laptop', 'limit': 5}
        
        print('Testing search API...')
        search_response = requests.get(search_url, headers=search_headers, params=params, timeout=10)
        print(f'Search Status Code: {search_response.status_code}')
        
        if search_response.status_code == 200:
            search_data = search_response.json()
            items = search_data.get('itemSummaries', [])
            print(f'✅ API test successful! Found {len(items)} items')
            if items:
                print(f'First item: {items[0].get("title", "N/A")}')
        else:
            print(f'❌ Search API failed: {search_response.text}')
    else:
        print(f'❌ OAuth failed: {response.text}')
        
except Exception as e:
    print(f'❌ Error: {e}')
