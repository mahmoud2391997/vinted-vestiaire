# eBay Country Filtering Documentation

## Overview

This document describes the enhanced country filtering functionality for eBay scraping in the Vinted scraping application. The feature allows users to search eBay listings across multiple countries and marketplaces, with automatic currency conversion and domain mapping.

## Supported Countries

The eBay country filtering supports **28 countries** across multiple continents:

### Europe
- **UK** - United Kingdom (`ebay.co.uk`) - Currency: £
- **DE** - Germany (`ebay.de`) - Currency: €
- **FR** - France (`ebay.fr`) - Currency: €
- **IT** - Italy (`ebay.it`) - Currency: €
- **ES** - Spain (`ebay.es`) - Currency: €
- **NL** - Netherlands (`ebay.nl`) - Currency: €
- **BE** - Belgium (`ebay.be`) - Currency: €
- **AT** - Austria (`ebay.at`) - Currency: €
- **CH** - Switzerland (`ebay.ch`) - Currency: CHF
- **PL** - Poland (`ebay.pl`) - Currency: zł
- **IE** - Ireland (`ebay.ie`) - Currency: €

### Americas
- **US** - United States (`ebay.com`) - Currency: $
- **CA** - Canada (`ebay.ca`) - Currency: C$
- **MX** - Mexico (`ebay.com.mx`) - Currency: MX$
- **AR** - Argentina (`ebay.com.ar`) - Currency: AR$
- **BR** - Brazil (`ebay.com.br`) - Currency: R$
- **CL** - Chile (`ebay.cl`) - Currency: CL$
- **CO** - Colombia (`ebay.com.co`) - Currency: COL$
- **CR** - Costa Rica (`ebay.co.cr`) - Currency: ₡
- **PA** - Panama (`ebay.com.pa`) - Currency: B/
- **PE** - Peru (`ebay.com.pe`) - Currency: S/
- **VE** - Venezuela (`ebay.com.ve`) - Currency: Bs

### Asia-Pacific
- **AU** - Australia (`ebay.com.au`) - Currency: A$
- **HK** - Hong Kong (`ebay.com.hk`) - Currency: HK$
- **MY** - Malaysia (`ebay.com.my`) - Currency: RM
- **PH** - Philippines (`ebay.ph`) - Currency: ₱
- **SG** - Singapore (`ebay.sg`) - Currency: S$
- **TW** - Taiwan (`ebay.com.tw`) - Currency: NT$
- **IN** - India (`ebay.in`) - Currency: ₹

## API Usage

### Endpoint
```
GET /api/ebay
```

### Parameters
- `search_text` (required): Search query string
- `country` (optional): Country code (default: 'uk')
- `page` (optional): Page number (default: 1)
- `items_per_page` (optional): Items per page (default: 50)
- `min_price` (optional): Minimum price filter
- `max_price` (optional): Maximum price filter

### Example Requests

#### Basic Search with Country
```bash
GET /api/ebay?search_text=iphone%2015&country=us
```

#### Search with Price Filters
```bash
GET /api/ebay?search_text=macbook&country=de&min_price=500&max_price=1500
```

#### Pagination
```bash
GET /api/ebay?search_text=nike%20shoes&country=au&page=2&items_per_page=25
```

## Implementation Details

### Country Mapping

The system uses three mapping dictionaries for each country:

1. **Domain Mapping**: Maps country codes to eBay domains
2. **Currency Mapping**: Maps country codes to local currency symbols
3. **Marketplace ID Mapping**: Maps country codes to eBay API marketplace IDs

### Error Handling

- **Invalid Country**: If an unsupported country code is provided, the system defaults to 'us' and logs a warning
- **Fallback Domains**: If scraping fails for the primary domain, the system attempts fallback domains
- **Validation**: Country codes are case-insensitive and validated against supported countries

### Scraping Methods

The country filtering is implemented across multiple scraping methods:

1. **`scrape_ebay_working`**: Primary scraping method using Vinted technique
2. **`scrape_ebay_direct`**: Direct web scraping with updated selectors
3. **`scrape_ebay_public_api_enhanced`**: Enhanced public API scraping
4. **`scrape_ebay_api`**: Official eBay API integration

Each method includes country-specific domain mapping and validation.

## Response Format

The API returns a JSON response with the following structure:

```json
{
  "products": [
    {
      "Title": "Product Title",
      "Price": "$99.99",
      "URL": "https://ebay.com/itm/...",
      "Image": "https://i.ebayimg.com/...",
      "Location": "Country, State",
      "Seller": "seller_name",
      "Condition": "New",
      "Shipping": "Free shipping"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 10,
    "has_more": true,
    "total_items": 500
  }
}
```

## Configuration

### Environment Variables

For eBay API integration, set the following environment variables:

```bash
EBAY_APP_ID=your_ebay_app_id
EBAY_CERT_ID=your_ebay_cert_id
```

### Sandbox vs Production

The system automatically detects sandbox vs production credentials:
- Sandbox credentials contain 'SBX' in the APP_ID
- Production credentials are used for live data

## Best Practices

### Rate Limiting
- Built-in rate limiter prevents 429 errors
- Cache manager reduces redundant API calls
- Random delays between requests

### User Agents
- Rotating user agents to avoid detection
- Browser-like headers for authentic requests

### Error Recovery
- Multiple fallback methods for robustness
- Graceful degradation when scraping fails
- Comprehensive logging for debugging

## Testing

### Test Different Countries
```bash
# Test European markets
curl "http://localhost:5001/api/ebay?search_text=iphone&country=de"
curl "http://localhost:5001/api/ebay?search_text=iphone&country=fr"

# Test Asian markets
curl "http://localhost:5001/api/ebay?search_text=iphone&country=jp"
curl "http://localhost:5001/api/ebay?search_text=iphone&country=au"

# Test American markets
curl "http://localhost:5001/api/ebay?search_text=iphone&country=ca"
curl "http://localhost:5001/api/ebay?search_text=iphone&country=mx"
```

### Invalid Country Handling
```bash
# Should default to US and show warning
curl "http://localhost:5001/api/ebay?search_text=iphone&country=invalid"
```

## Troubleshooting

### Common Issues

1. **Country Not Supported**
   - Check the country code against the supported list
   - Ensure country code is lowercase in API calls

2. **Scraping Failures**
   - Check eBay domain accessibility
   - Verify user agent headers
   - Review rate limiting logs

3. **Currency Display**
   - Currency symbols are automatically mapped
   - Prices are displayed in local currency format

### Debug Logging

Enable debug logging to trace country filtering:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Language Support**: Localized search queries
- **Currency Conversion**: Real-time exchange rates
- **Regional Filters**: State/province level filtering
- **Price Normalization**: Convert all prices to base currency

### Additional Countries
- Japan (`ebay.co.jp`)
- South Korea (`ebay.co.kr`)
- More Latin American markets

## Contributing

When adding new country support:

1. Add domain mapping to `country_domains`
2. Add currency mapping to `country_currencies`
3. Add marketplace ID mapping to `country_marketplaces`
4. Update documentation
5. Add test cases

## Version History

- **v2.0**: Enhanced country support from 8 to 28 countries
- **v1.5**: Added country validation and error handling
- **v1.0**: Initial implementation with basic country support
