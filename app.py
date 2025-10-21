"""
Yelp Top Places API - FastAPI service with Bayesian re-ranking
Finds nearby restaurants/businesses and ranks by credible rating score.
"""
import os
import time
from typing import Optional, List
from datetime import datetime, timedelta

import requests
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse
from cachetools import TTLCache
from pydantic import BaseModel, Field

# ============================================================================
# Configuration
# ============================================================================
YELP_API_KEY = os.getenv("YELP_API_KEY")
if not YELP_API_KEY:
    raise RuntimeError("YELP_API_KEY environment variable required")

YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"
USER_AGENT = "YelpTopPlacesAPI/1.0 (Foodie MVP)"

# Bayesian average parameters
PRIOR_RATING = 3.8  # C: global average rating assumption
DAMPING_FACTOR = 150  # m: minimum reviews needed to trust rating

# Cache: 10-minute TTL, max 500 entries
cache = TTLCache(maxsize=500, ttl=600)

app = FastAPI(
    title="Yelp Top Places API",
    description="Find top-reviewed nearby places with Bayesian re-ranking",
    version="1.0.0"
)

# ============================================================================
# Models
# ============================================================================
class BusinessResult(BaseModel):
    name: str
    rating: float
    review_count: int
    score: float = Field(..., description="Bayesian credibility score")
    price: Optional[str] = None
    distance_m: int
    address: str
    url: str
    yelp_id: str

class TopPlacesResponse(BaseModel):
    term: str
    center: dict
    count: int
    results: List[BusinessResult]
    attribution: str = "Results powered by Yelp"

# ============================================================================
# Bayesian Score Calculation
# ============================================================================
def calculate_bayesian_score(rating: float, review_count: int) -> float:
    """
    Calculate Bayesian average to dampen low-sample outliers.
    
    score = (v/(v+m)) * R + (m/(v+m)) * C
    - R: business rating (0-5)
    - v: review count
    - C: prior rating (3.8)
    - m: damping factor (150)
    
    Example: 5.0★ with 3 reviews → ~3.88, but 4.6★ with 1200 reviews → ~4.58
    """
    v = review_count
    m = DAMPING_FACTOR
    R = rating
    C = PRIOR_RATING
    
    return (v / (v + m)) * R + (m / (v + m)) * C

# ============================================================================
# Yelp API Client
# ============================================================================
def search_yelp(
    term: str,
    latitude: float,
    longitude: float,
    radius_m: int = 5000,
    limit: int = 10,
    open_now: bool = False,
    price: Optional[str] = None
) -> List[dict]:
    """
    Call Yelp Fusion API /v3/businesses/search.
    Returns list of business dicts.
    """
    headers = {
        "Authorization": f"Bearer {YELP_API_KEY}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    
    params = {
        "term": term,
        "latitude": latitude,
        "longitude": longitude,
        "radius": min(radius_m, 40000),  # Yelp max is 40km
        "limit": min(limit * 5, 50),  # Request more for better re-ranking pool
    }
    
    if open_now:
        params["open_now"] = True
    
    if price:
        # Price is comma-separated "1,2,3,4"
        params["price"] = price.replace(" ", "")
    
    try:
        response = requests.get(
            YELP_SEARCH_URL,
            headers=headers,
            params=params,
            timeout=10
        )
        
        # Handle rate limiting
        if response.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Yelp API rate limit exceeded. Please retry in a moment."
            )
        
        # Handle other HTTP errors
        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Yelp API error: {response.status_code} - {response.text[:200]}"
            )
        
        data = response.json()
        return data.get("businesses", [])
        
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Yelp API request timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Yelp API request failed: {str(e)}")

# ============================================================================
# Main Endpoint
# ============================================================================
@app.get("/top", response_model=TopPlacesResponse)
def get_top_places(
    term: str = Query(..., description="Search term (e.g., 'pizza', 'sushi')"),
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_m: int = Query(5000, ge=100, le=40000, description="Search radius in meters"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    open_now: bool = Query(False, description="Filter to open businesses only"),
    price: Optional[str] = Query(None, description="Price levels: 1,2,3,4")
):
    """
    Search for top-rated nearby places using Yelp Fusion API.
    Re-ranks results using Bayesian average to favor high-volume ratings.
    
    Example:
        GET /top?term=sushi&lat=43.6532&lng=-79.3832&radius_m=5000&limit=10&open_now=true&price=1,2
    """
    # Validate price format
    if price:
        valid_prices = {"1", "2", "3", "4"}
        price_parts = set(price.replace(" ", "").split(","))
        if not price_parts.issubset(valid_prices):
            raise HTTPException(
                status_code=400,
                detail="Invalid price format. Use comma-separated values: 1,2,3,4"
            )
    
    # Create cache key
    cache_key = f"{term}|{lat}|{lng}|{radius_m}|{open_now}|{price or ''}"
    
    # Check cache
    if cache_key in cache:
        return cache[cache_key]
    
    # Fetch from Yelp
    businesses = search_yelp(
        term=term,
        latitude=lat,
        longitude=lng,
        radius_m=radius_m,
        limit=limit,
        open_now=open_now,
        price=price
    )
    
    # Calculate Bayesian scores and transform results
    scored_results = []
    for biz in businesses:
        rating = biz.get("rating", 0)
        review_count = biz.get("review_count", 0)
        score = calculate_bayesian_score(rating, review_count)
        
        # Build address string
        location = biz.get("location", {})
        address = ", ".join(location.get("display_address", []))
        
        scored_results.append(BusinessResult(
            name=biz.get("name", "Unknown"),
            rating=rating,
            review_count=review_count,
            score=round(score, 2),
            price=biz.get("price"),
            distance_m=int(biz.get("distance", 0)),
            address=address,
            url=biz.get("url", ""),
            yelp_id=biz.get("id", "")
        ))
    
    # Sort by Bayesian score (descending)
    scored_results.sort(key=lambda x: x.score, reverse=True)
    
    # Limit results
    final_results = scored_results[:limit]
    
    # Build response
    response = TopPlacesResponse(
        term=term,
        center={"lat": lat, "lng": lng, "radius_m": radius_m},
        count=len(final_results),
        results=final_results
    )
    
    # Cache response
    cache[cache_key] = response
    
    return response

# ============================================================================
# Simple HTML UI (Optional)
# ============================================================================
@app.get("/", response_class=HTMLResponse)
def index():
    """Simple web UI for testing the API"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Yelp Top Places API</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
            h1 { color: #d32323; }
            .form-group { margin: 15px 0; }
            label { display: block; margin-bottom: 5px; font-weight: 500; }
            input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #d32323; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background: #a91b1b; }
            .results { margin-top: 30px; }
            .business { border: 1px solid #eee; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .business h3 { margin: 0 0 10px 0; color: #333; }
            .meta { color: #666; font-size: 14px; }
            .score { color: #d32323; font-weight: bold; }
            .attribution { margin-top: 20px; padding: 10px; background: #f9f9f9; border-radius: 4px; font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>🍕 Yelp Top Places Finder</h1>
        <p>Find top-reviewed nearby places with smart Bayesian re-ranking</p>
        
        <div class="form-group">
            <label>What are you looking for?</label>
            <input type="text" id="term" placeholder="e.g., sushi, pizza, coffee" value="pizza">
        </div>
        
        <div class="form-group">
            <label>Latitude</label>
            <input type="number" step="0.0001" id="lat" placeholder="43.6532" value="43.6532">
        </div>
        
        <div class="form-group">
            <label>Longitude</label>
            <input type="number" step="0.0001" id="lng" placeholder="-79.3832" value="-79.3832">
        </div>
        
        <div class="form-group">
            <label>Radius (meters)</label>
            <input type="number" id="radius" value="5000" min="100" max="40000">
        </div>
        
        <div class="form-group">
            <label>Max Results</label>
            <input type="number" id="limit" value="10" min="1" max="50">
        </div>
        
        <button onclick="searchPlaces()">Search</button>
        
        <div class="results" id="results"></div>
        
        <script>
            async function searchPlaces() {
                const term = document.getElementById('term').value;
                const lat = document.getElementById('lat').value;
                const lng = document.getElementById('lng').value;
                const radius = document.getElementById('radius').value;
                const limit = document.getElementById('limit').value;
                
                const url = `/top?term=${encodeURIComponent(term)}&lat=${lat}&lng=${lng}&radius_m=${radius}&limit=${limit}`;
                
                document.getElementById('results').innerHTML = '<p>Loading...</p>';
                
                try {
                    const response = await fetch(url);
                    const data = await response.json();
                    
                    if (!response.ok) {
                        throw new Error(data.detail || 'Error fetching results');
                    }
                    
                    let html = `<h2>Found ${data.count} results for "${data.term}"</h2>`;
                    
                    data.results.forEach((biz, idx) => {
                        html += `
                            <div class="business">
                                <h3>${idx + 1}. ${biz.name}</h3>
                                <div class="meta">
                                    <span class="score">Score: ${biz.score}</span> | 
                                    Rating: ${biz.rating}★ (${biz.review_count} reviews) | 
                                    ${biz.price || 'N/A'} | 
                                    ${Math.round(biz.distance_m)}m away
                                </div>
                                <div class="meta">${biz.address}</div>
                                <a href="${biz.url}" target="_blank">View on Yelp →</a>
                            </div>
                        `;
                    });
                    
                    html += `<div class="attribution">${data.attribution}</div>`;
                    
                    document.getElementById('results').innerHTML = html;
                } catch (error) {
                    document.getElementById('results').innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "yelp-top-places-api",
        "cache_size": len(cache)
    }
