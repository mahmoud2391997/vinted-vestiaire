# eBay API Endpoint Documentation

## Overview
The eBay endpoint provides real-time product data from eBay's official API with advanced search, filtering, and pagination capabilities.

## Base URL
```
http://localhost:8099/ebay
```

## API Parameters

| Parameter | Type | Required | Default | Description | Example |
|-----------|------|----------|---------|-------------|---------|
| `search` | String | No | `laptop` | Search query for products | `apple%20macbook` |
| `page` | Integer | No | `1` | Page number for pagination | `2` |
| `items_per_page` | Integer | No | `50` | Number of items per page (max 50) | `10` |
| `min_price` | Float | No | `None` | Minimum price filter | `100` |
| `max_price` | Float | No | `None` | Maximum price filter | `500` |

## Response Format

```json
{
  "success": true,
  "data": [
    {
      "Title": "Apple MacBook Pro 13-inch M2 2022",
      "Price": "$1,299.00",
      "Brand": "Apple",
      "Size": "13-inch",
      "Image": "https://i.ebayimg.com/images/g/xxx/s-l500.jpg",
      "Link": "https://www.ebay.com/itm/xxx",
      "Condition": "New",
      "Seller": "trusted_seller"
    }
  ],
  "count": 5,
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "has_more": true,
    "items_per_page": 5,
    "total_items": 213,
    "start_index": 0,
    "end_index": 5
  },
  "error": null
}
```

## Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `Title` | String | Product title from eBay |
| `Price` | String | Price in USD format |
| `Brand` | String | Auto-detected brand name |
| `Size` | String | Extracted size information |
| `Image` | String | Product image URL |
| `Link` | String | Direct eBay product link |
| `Condition` | String | Item condition (New, Used, etc.) |
| `Seller` | String | Seller information |

## Usage Examples

### Basic Search
```bash
curl "http://localhost:8099/ebay?search=laptop"
```

### Search with Pagination
```bash
curl "http://localhost:8099/ebay?search=apple%20macbook&page=1&items_per_page=10"
```

### Price Filtering
```bash
curl "http://localhost:8099/ebay?search=nike%20shoes&min_price=50&max_price=200"
```

### Combined Parameters
```bash
curl "http://localhost:8099/ebay?search=sony%20camera&min_price=100&max_price=500&page=2&items_per_page=15"
```

## Brand Detection

The endpoint automatically detects and extracts brands from product titles. Supported brands include:

### Technology
- Apple, Samsung, Sony, LG, Microsoft, Dell, HP, Lenovo, Asus, Acer

### Fashion & Apparel
- Nike, Adidas, Puma, Reebok, Under Armour, New Balance, Converse, Vans

### Luxury Brands
- Louis Vuitton, Gucci, Prada, Chanel, Hermès, Rolex, Omega, Cartier

### Automotive
- Toyota, Honda, Ford, BMW, Mercedes, Audi, Tesla, Hyundai, Kia

### Photography
- Canon, Nikon, Fujifilm, Panasanic, Olympus, GoPro, DJI

## Size Detection

The endpoint automatically extracts size information from titles using patterns like:
- Clothing sizes: XS, S, M, L, XL, XXL, 3XL, 4XL
- Screen sizes: 13-inch, 15.6", 27"
- Shoe sizes: Size 10, Size 9.5
- Measurements: 100cm, 42mm

## Pagination

### Pagination Fields
| Field | Type | Description |
|-------|------|-------------|
| `current_page` | Integer | Current page number |
| `total_pages` | Integer | Total number of pages |
| `has_more` | Boolean | Whether more pages are available |
| `items_per_page` | Integer | Items per page |
| `total_items` | Integer | Total items available |
| `start_index` | Integer | Starting index of current page |
| `end_index` | Integer | Ending index of current page |

### Navigation Examples
```bash
# First page
curl "http://localhost:8099/ebay?search=laptop&page=1&items_per_page=10"

# Second page
curl "http://localhost:8099/ebay?search=laptop&page=2&items_per_page=10"

# Last page (check has_more: false)
curl "http://localhost:8099/ebay?search=laptop&page=5&items_per_page=10"
```

## Price Filtering

### Price Filter Examples
```bash
# Minimum price only
curl "http://localhost:8099/ebay?search=laptop&min_price=500"

# Maximum price only
curl "http://localhost:8099/ebay?search=laptop&max_price=1000"

# Price range
curl "http://localhost:8099/ebay?search=laptop&min_price=500&max_price=1000"
```

## Error Handling

The endpoint includes comprehensive error handling:

### Success Response
```json
{
  "success": true,
  "data": [...],
  "count": 10,
  "pagination": {...},
  "error": null
}
```

### Error Response
```json
{
  "success": true,
  "data": [],
  "count": 0,
  "pagination": {...},
  "error": "Error description"
}
```

## Rate Limits

- **Sandbox Environment**: ~5,000 requests per day
- **Production Environment**: Based on your eBay API plan
- **Recommended**: Add delays between requests for bulk operations

## Setup Instructions

### 1. Environment Variables
Set your eBay API credentials in the `.env` file:
```bash
export EBAY_APP_ID="your_app_id_here"
export EBAY_CERT_ID="your_cert_id_here"
```

### 2. Get eBay API Keys
1. Go to [eBay Developer Portal](https://developer.ebay.com)
2. Create a developer account
3. Generate API keys (App ID and Cert ID)
4. Configure your application for Buy API access

### 3. Start the Server
```bash
python3 test_server.py
```

## Advanced Features

### Search Operators
```bash
# AND search (default)
curl "http://localhost:8099/ebay?search=apple%20macbook"

# OR search (using comma)
curl "http://localhost:8099/ebay?search=(apple,macbook)"
```

### Combined Filters
```bash
# Brand + Price + Size + Condition
curl "http://localhost:8099/ebay?search=nike%20shoes&min_price=50&max_price=200&items_per_page=20"
```

## Production Deployment

### Vercel Environment Variables
```bash
EBAY_APP_ID=your_production_app_id
EBAY_CERT_ID=your_production_cert_id
```

### Docker Environment
```dockerfile
ENV EBAY_APP_ID=your_app_id
ENV EBAY_CERT_ID=your_cert_id
```

## Troubleshooting

### Common Issues

**Issue**: Getting sample data instead of real data
**Solution**: Check your eBay API credentials and ensure they're properly configured

**Issue**: "invalid_client" authentication error
**Solution**: Verify your App ID and Cert ID are correct and match the environment (sandbox/production)

**Issue**: No results for search query
**Solution**: Try broader search terms or check if items exist in the sandbox environment

**Issue**: Price filtering not working
**Solution**: Ensure price values are numeric and properly formatted

### Debug Mode
Add debug output by checking server logs for detailed error information.

## API Version

- **Current Version**: 1.0
- **API**: eBay Browse API v1
- **Authentication**: OAuth 2.0 Client Credentials Flow

## Support

For issues related to:
- **eBay API**: Check [eBay Developer Documentation](https://developer.ebay.com/)
- **Endpoint Implementation**: Review the code in `api/index.py`
- **Authentication**: Ensure proper API key configuration

---

**Note**: This endpoint uses eBay's sandbox environment by default. For production use, ensure you have production API keys and proper rate limiting.
