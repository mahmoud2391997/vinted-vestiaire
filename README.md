# Vercel Web Scraper App

## Deployment Instructions

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy:
```bash
vercel --prod
```

## Project Structure
- `api/index.py` - Serverless function for Vercel
- `vercel.json` - Vercel configuration
- `requirements.txt` - Python dependencies

## Notes
- This version uses sample data for demonstration
- The original Selenium scraper won't work on Vercel (serverless limitations)
- For real scraping, consider using external APIs or server-based scraping
