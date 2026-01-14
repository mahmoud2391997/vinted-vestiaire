# eBay API Setup Guide

To use real eBay data instead of sample data, you need to set up eBay API credentials.

## Steps to Get eBay API Keys

1. **Create eBay Developer Account**
   - Go to [https://developer.ebay.com](https://developer.ebay.com)
   - Sign up for a free developer account

2. **Create Application**
   - Go to "My Account" → "Application Keys"
   - Click "Add a new application"
   - Fill in the application details
   - Choose the production environment

3. **Get Your Credentials**
   - You'll receive:
     - **App ID (Client ID)**
     - **Dev ID** 
     - **Cert ID (Client Secret)**
   - You need the **App ID** and **Cert ID** for this integration

4. **Set Environment Variables**
   
   **Option 1: Set in your terminal**
   ```bash
   export EBAY_APP_ID="your_app_id_here"
   export EBAY_CERT_ID="your_cert_id_here"
   ```
   
   **Option 2: Set in Vercel (for deployment)**
   - Go to your Vercel dashboard
   - Select your project
   - Go to "Settings" → "Environment Variables"
   - Add:
     - `EBAY_APP_ID` = your_app_id_here
     - `EBAY_CERT_ID` = your_cert_id_here

## API Features

When API keys are configured, the eBay endpoint will:

- ✅ Use official eBay Browse API
- ✅ Get real-time product data
- ✅ Support price filtering
- ✅ Support pagination
- ✅ Return accurate product information
- ✅ Include real images and links

## Fallback Behavior

Without API keys, the system will:
- ⚠️ Try enhanced web scraping
- ⚠️ Fall back to sample data if blocked
- ⚠️ Show mock data for development

## Testing

Once you've set up the API keys, test the endpoint:

```bash
curl "http://localhost:8099/ebay?search=laptop&page=1&items_per_page=5"
```

You should see real eBay products instead of sample data.

## API Limits

- **Rate Limit**: ~5,000 requests per day (free tier)
- **Pagination**: Up to 50 items per page
- **Search**: Supports keywords, price filters, categories

## Troubleshooting

**Issue**: Still getting sample data after setting keys
- **Solution**: Restart your server after setting environment variables

**Issue**: "Invalid application credentials" error
- **Solution**: Double-check your App ID and Cert ID are correct

**Issue**: Rate limit errors
- **Solution**: Wait a few minutes between requests or upgrade your plan
