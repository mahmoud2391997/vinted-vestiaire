# Enhanced Vinted Product Scraper

A modern, responsive web scraper for Vinted.pl with real-time data extraction, advanced search capabilities, and beautiful UI. Built for Vercel deployment with serverless architecture.

## 🌟 Features

### 🎨 Enhanced User Interface
- **Modern Design** - Beautiful gradient backgrounds and card-based layouts
- **Responsive Layout** - Works perfectly on mobile and desktop devices
- **Real-time Search** - Instant product search with loading states
- **Brand Filtering** - Quick filter chips for luxury brands
- **Category Selection** - Dropdown filters for bags, shoes, clothing, accessories
- **Product Cards** - Rich display with images, prices, sizes, and direct Vinted links
- **Smooth Animations** - Hover effects and transitions for better UX

### 🔍 Advanced Search Capabilities
- **Text Search** - Search for any product type (bags, shoes, dresses, etc.)
- **Brand Filtering** - Pre-configured luxury brand chips:
  - Dior, Louis Vuitton, Prada, Gucci
  - Christian Dior, Michael Kors, Coach
  - Nike, Adidas, Zara, H&M, Levi's
- **Category Filtering** - Bags, Shoes, Clothing, Accessories
- **Pagination Support** - Fetch multiple pages of results
- **Real-time Results** - Dynamic product grid with count display

### 📊 Data Extraction
- **Real Product Names** - Extracted from image alt text
- **Brand Recognition** - 50+ known luxury and popular brands
- **Price Extraction** - Clean currency formatting (zł)
- **Size Detection** - Multiple size patterns (S/M/L, numeric, cm/lat)
- **Image URLs** - Real product images from Vinted
- **Direct Links** - Each product links to original Vinted listing

## 🚀 Deployment

### Vercel Ready
- **Serverless Architecture** - Compatible with Vercel's platform
- **JSON API** - Backend serves structured data for frontend
- **Static Assets** - All resources self-contained
- **Environment Variables** - Configurable for different markets

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run local server
python3 test_server.py

# Access at
http://localhost:8093/
```

## 📡 API Endpoints

### Main Interface
- **URL**: `/` (serves enhanced HTML UI)
- **Method**: GET
- **Response**: HTML with modern interface

### Data API
- **URL**: `/?search={term}&pages={number}`
- **Method**: GET
- **Response**: JSON with product data

#### API Parameters
| Parameter | Type | Description | Default | Example |
|-----------|------|-------------|---------|---------|
| `search` | String | Main search query | `bags` |
| `pages` | Integer | Number of pages to scrape | `2` |

#### API Response Structure
```json
{
  "success": true,
  "data": [
    {
      "Title": "Product Name",
      "Price": "450zł",
      "Brand": "Dior",
      "Size": "One Size",
      "Image": "https://images.vinted.net/...",
      "Link": "https://www.vinted.pl/items/..."
    }
  ],
  "count": 96,
  "error": null
}
```

## 🛠️ Technology Stack

### Backend
- **Python 3.9+** - Core scraping logic
- **Requests** - HTTP client for web scraping
- **BeautifulSoup4** - HTML parsing and data extraction
- **Regex** - Pattern matching for brands, prices, sizes
- **JSON** - Structured data responses

### Frontend
- **HTML5** - Modern semantic markup
- **CSS3** - Responsive design with animations
- **JavaScript ES6+** - Dynamic search and filtering
- **Fetch API** - Modern AJAX requests
- **Grid Layout** - CSS Grid for responsive design

### Deployment
- **Vercel** - Serverless hosting platform
- **Python Runtime** - Serverless function execution
- **Static Hosting** - HTML/CSS/JS assets

## 📱 Usage Examples

### Search for Luxury Bags
```bash
curl "http://localhost:8093/?search=dior%20bag&pages=2"
```

### Filter by Brand
```javascript
// Frontend automatically filters when brand chips are clicked
// Backend supports brand-specific searches
```

### Multiple Pages
```bash
curl "http://localhost:8093/?search=bags&pages=5"
# Returns ~480 products (96 items × 5 pages)
```

## 🔧 Configuration

### Environment Variables
- `VINTED_COUNTRY` - Target country code (default: `pl`)
- `VINTED_DOMAIN` - Custom domain override
- `REQUEST_TIMEOUT` - Scraping timeout in seconds (default: `10`)

### Supported Countries
- Poland (`pl`) - vinted.pl
- France (`fr`) - vinted.fr  
- Germany (`de`) - vinted.de
- Spain (`es`) - vinted.es
- And more...

## 📈 Performance

### Scraping Features
- **Rate Limiting** - 1-second delays between requests
- **Error Handling** - Graceful fallback to sample data
- **Timeout Protection** - 10-second request timeouts
- **User Agent Rotation** - Realistic browser headers
- **Data Validation** - Quality checks before returning results

### Response Times
- **Single Page**: ~2-3 seconds
- **Multiple Pages**: ~5-10 seconds (depending on page count)
- **Brand Filtering**: Sub-second response times

## 🛡️ Security & Compliance

### Web Scraping Best Practices
- **Respectful Requests** - Appropriate delays between calls
- **User Agent Headers** - Standard browser identification
- **Error Handling** - Graceful degradation on failures
- **Data Sanitization** - Clean text extraction and encoding

### Vercel Security
- **HTTPS Only** - Secure connections required
- **CORS Headers** - Proper cross-origin handling
- **Input Validation** - Parameter sanitization
- **Rate Limiting** - Built-in request throttling

## 🚀 Deployment Guide

### Quick Start
1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd vinted-scraper
   ```

2. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

4. **Configure** (if needed)
   - Set custom domain
   - Configure environment variables
   - Set up analytics

### Advanced Configuration
```json
// vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

## 📊 Sample Use Cases

### Fashion E-commerce
- **Price Monitoring** - Track luxury bag prices across markets
- **Brand Analysis** - Compare availability by brand
- **Market Research** - Identify trending products and styles

### Personal Shopping
- **Deal Hunting** - Find best prices for specific items
- **Wishlist Tracking** - Monitor availability of desired products
- **Size Alerts** - Get notified when your size becomes available

### Business Intelligence
- **Competitor Analysis** - Track pricing strategies
- **Market Trends** - Identify popular brands and categories
- **Inventory Planning** - Research product availability patterns

## 🔄 Maintenance

### Monitoring
- **Error Logging** - Comprehensive error tracking
- **Performance Metrics** - Response time monitoring
- **Success Rates** - Scraping effectiveness tracking

### Updates
- **Brand Lists** - Regularly updated brand recognition
- **Selector Updates** - Adapt to Vinted website changes
- **Feature Enhancements** - Continuous UI/UX improvements

## 📞 Troubleshooting

### Common Issues
- **Empty Results** - Check search terms and brand spelling
- **Slow Loading** - Increase timeout or reduce page count
- **Image Missing** - Verify image extraction logic
- **Encoding Issues** - Check character encoding settings

### Debug Mode
```bash
# Enable verbose logging
export DEBUG=true
python3 test_server.py
```

## 📄 License

MIT License - Free for commercial and personal use

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Built with ❤️ for the fashion and e-commerce community**
