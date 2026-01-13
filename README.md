
# Vinted Scraper API

This project provides a serverless API endpoint to scrape product data from Vinted.

## API Usage

The API is served from the `/api` path.

### Request

Make a `GET` request to the endpoint with the following query parameters:

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `search` | String | The main search query (e.g., "dior bag"). | `''` |
| `brand` | String | The brand to filter by (e.g., "Dior"). | `''` |
| `category`| String | The category to filter by (e.g., "bags"). | `''` |
| `min_price`| Integer| The minimum price. | `''` |
| `max_price`| Integer| The maximum price. | `''` |
| `country` | String | The two-letter country code for the Vinted domain (e.g., `pl`, `fr`, `de`). | `pl` |
| `pages` | Integer | The number of pages to scrape. | `1` |

**Example Request:**

```
https://vinted-scraping.vercel.app/api?search=gucci%20bag&brand=gucci&min_price=100&max_price=500&country=fr
```

### Response Structure

The API returns a JSON object with the following structure:

```json
{
  "success": true,
  "data": [
    {
      "Title": "Gucci shoulder bag",
      "Price": "350.00",
      "Currency": "EUR",
      "Brand": "Gucci",
      "Size": "One Size",
      "URL": "https://www.vinted.fr/items/123456-gucci-shoulder-bag",
      "ImageURL": "https://images.vinted.net/..."
    }
  ],
  "count": 1,
  "error": null
}
```
