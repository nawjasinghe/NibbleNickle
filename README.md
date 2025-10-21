# 🍕 NibbleNickle - Smart Food Discovery API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)
![Yelp API](https://img.shields.io/badge/Yelp-Fusion_API_v3-red?logo=yelp)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Find the best-rated restaurants near you with intelligent Bayesian ranking**

[Features](#-features) • [Quick Start](#-quick-start) • [API Docs](#-api-documentation) • [Demo](#-interactive-demo)

</div>

---

## 🎯 What Makes This Special?

Traditional restaurant searches rank by raw star ratings, leading to misleading results where a restaurant with **5.0★ from 3 reviews** beats one with **4.6★ from 1,200 reviews**. 

**NibbleNickle** solves this using **Bayesian credibility scoring** to surface truly popular, consistently great places.

### The Algorithm

```python
score = (v/(v+m)) * R + (m/(v+m)) * C
```

Where:
- `R` = Restaurant's rating (0-5 stars)
- `v` = Number of reviews
- `C` = 3.8 (prior/global average)
- `m` = 150 (confidence threshold)

**Result:** High-volume favorites rise to the top, while low-sample outliers get reality-checked.

---

## ✨ Features

- 🎯 **Bayesian Re-Ranking** - Credible scores that favor proven favorites
- 🔍 **Yelp Fusion API** - Real-time data from millions of businesses
- ⚡ **Smart Caching** - 10-minute TTL cache reduces API calls
- 🌐 **Web UI** - Built-in interactive search interface
- 🖥️ **Console CLI** - Interactive terminal for quick searches
- 🔧 **Production-Ready** - Comprehensive error handling, validation, health checks
- 📍 **Location Filters** - Search by radius, price level, open status
- 📊 **Rich Metadata** - Ratings, reviews, distance, price, addresses, URLs

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [Yelp Fusion API Key](https://www.yelp.com/developers/v3/manage_app) (free)

### Installation

```bash
# Clone the repository
git clone https://github.com/nawjasinghe/NibbleNickle.git
cd NibbleNickle

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your Yelp API key
```

### Running the API

```bash
# Set your API key (Windows PowerShell)
$env:YELP_API_KEY="your_key_here"

# Or create a .env file with:
# YELP_API_KEY=your_key_here

# Start the server
uvicorn app:app --reload --port 8000
```

🌐 **Access the web UI:** http://localhost:8000

---

## 📖 API Documentation

### `GET /top` - Search Top Places

Find top-rated places with smart ranking.

#### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `term` | string | ✅ | Search term | `pizza`, `sushi`, `coffee` |
| `latitude` | float | ✅ | Search latitude | `45.4215` |
| `longitude` | float | ✅ | Search longitude | `-75.6972` |
| `radius` | int | ❌ | Radius in meters (100-40000) | `5000` |
| `limit` | int | ❌ | Max results (1-50) | `10` |
| `open_now` | bool | ❌ | Only show open businesses | `true` |
| `price` | string | ❌ | Price levels (1-4, comma-separated) | `1,2,3` |

#### Example Request

```bash
curl "http://localhost:8000/top?term=shawarma&latitude=45.4215&longitude=-75.6972&radius=5000&limit=10"
```

#### Example Response

```json
{
  "term": "shawarma",
  "location": {"latitude": 45.4215, "longitude": -75.6972},
  "total_results": 15,
  "results": [
    {
      "name": "Shawarma Palace",
      "rating": 4.1,
      "review_count": 291,
      "score": 4.0,
      "price": "$$",
      "distance_m": 1709,
      "address": "464 Rideau Street, Ottawa, ON K1N 5Z4",
      "url": "https://www.yelp.com/biz/shawarma-palace-ottawa",
      "yelp_id": "shawarma-palace-ottawa"
    }
  ]
}
```

### `GET /health` - Health Check

Returns service status and cache statistics.

```json
{
  "status": "healthy",
  "service": "yelp-top-places-api",
  "cache_size": 12
}
```

---

## 💻 Interactive Demo

### Web UI

Start the server and visit http://localhost:8000 for a beautiful web interface:

<div align="center">
<img src="https://via.placeholder.com/800x400/4CAF50/FFFFFF?text=Web+UI+Search+Interface" alt="Web UI Demo" width="600"/>
</div>

### Console CLI

```bash
python console.py
```

Interactive terminal with:
- 🎯 Custom search prompts
- 📍 Location presets (Ottawa, Toronto, Montreal, Vancouver)
- 💾 Save results to JSON
- 🎨 Emoji-formatted output

---

## 🧪 Testing

Comprehensive test suite included:

```bash
python run_tests.py
```

**Test Coverage:**
- ✅ Basic search validation
- ✅ Filter functionality (price, open now, radius)
- ✅ Bayesian ranking verification
- ✅ Error handling (400, 422, 429 status codes)
- ✅ Parameter validation
- ✅ Cache performance

---

## 🏗️ Project Structure

```
NibbleNickle/
├── app.py                 # Main FastAPI application (358 lines)
├── console.py             # Interactive CLI tool
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .gitignore            # Git exclusions
├── README.md             # This file
└── __pycache__/          # Python cache (ignored)
```

---

## 🛠️ Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern async web framework
- **[Yelp Fusion API](https://www.yelp.com/developers)** - Business data source
- **[Pydantic](https://pydantic-docs.helpmanual.io/)** - Data validation
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server
- **[Cachetools](https://cachetools.readthedocs.io/)** - In-memory caching

---

## 🎓 Why Bayesian Ranking?

### The Problem

| Restaurant | Rating | Reviews | Raw Score |
|------------|--------|---------|-----------|
| Hidden Gem Cafe | ⭐⭐⭐⭐⭐ 5.0 | 3 | **5.0** ❌ |
| Popular Favorite | ⭐⭐⭐⭐⭐ 4.6 | 1,200 | **4.6** |

### Our Solution

| Restaurant | Rating | Reviews | **Bayesian Score** |
|------------|--------|---------|-------------------|
| Hidden Gem Cafe | ⭐⭐⭐⭐⭐ 5.0 | 3 | **3.82** |
| Popular Favorite | ⭐⭐⭐⭐⭐ 4.6 | 1,200 | **4.58** ✅ |

**Result:** The established favorite wins, as it should!

---

## 📝 Usage Examples

### Find Best Pizza in Toronto

```bash
curl "http://localhost:8000/top?term=pizza&latitude=43.6532&longitude=-79.3832&limit=5"
```

### Find Cheap Sushi Open Now

```bash
curl "http://localhost:8000/top?term=sushi&latitude=43.6532&longitude=-79.3832&price=1,2&open_now=true"
```

### Find Coffee Within 1km

```bash
curl "http://localhost:8000/top?term=coffee&latitude=45.4215&longitude=-75.6972&radius=1000"
```

---

## 🤝 Contributing

Contributions welcome! Feel free to:

- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests
- ⭐ Star the repo!

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **Yelp** for providing the Fusion API
- Powered by real-time data from [Yelp.com](https://www.yelp.com)
- Bayesian statistics for credible ranking

---

<div align="center">

**Made with ❤️ and 🍕**

[⭐ Star this repo](https://github.com/nawjasinghe/NibbleNickle) | [🐛 Report Bug](https://github.com/nawjasinghe/NibbleNickle/issues) | [💡 Request Feature](https://github.com/nawjasinghe/NibbleNickle/issues)

</div>
