# IBM Stock Dashboard 📈

A beautiful, real-time stock dashboard built with Flask and Yahoo Finance.

## Features

- 🔴 **Live Stock Data** - Real-time price updates from Yahoo Finance
- 📊 **Interactive Charts** - Historical price data with multiple timeframes (1D, 5D, 1M, 3M, 6M, 1Y, 5Y)
- 📰 **Latest News** - Recent news articles about the stock
- 🎨 **Modern UI** - Bloomberg terminal-inspired dark theme
- 🔍 **Search Any Stock** - Look up any ticker symbol (IBM, AAPL, GOOGL, etc.)

## Quick Start

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python app.py
```

### 4. Open Dashboard

Navigate to [http://localhost:5000](http://localhost:5000) in your browser.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/stock/<ticker>` | Get current stock data |
| `GET /api/stock/<ticker>/history/<period>` | Get historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 5y) |
| `GET /api/stock/<ticker>/news` | Get latest news |

## Tech Stack

- **Backend**: Python, Flask, yfinance
- **Frontend**: Vanilla JS, Chart.js
- **Styling**: Custom CSS with JetBrains Mono & Outfit fonts

---

*Designed by Dang Hoang, AI Eng.*

