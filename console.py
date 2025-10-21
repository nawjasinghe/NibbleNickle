"""
Interactive Console for Yelp Top Places API
Allows you to input your own search queries and see results
"""
import os
import sys
import json

# Set API key before importing app
os.environ["YELP_API_KEY"] = "INSERTKEY"

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def print_header():
    print("\n" + "=" * 70)
    print("🍕 YELP TOP PLACES - INTERACTIVE SEARCH")
    print("=" * 70)
    print("Find top-rated places near you with smart Bayesian ranking\n")

def get_input(prompt, default=None, type_func=str):
    """Get user input with optional default value"""
    if default is not None:
        prompt = f"{prompt} [{default}]"
    
    value = input(f"{prompt}: ").strip()
    
    if not value and default is not None:
        return type_func(default)
    
    if not value:
        return None
    
    try:
        return type_func(value)
    except ValueError:
        print(f"Invalid input, using default: {default}")
        return type_func(default) if default else None

def search_places():
    """Interactive search function"""
    print("\n📍 Enter your search parameters:\n")
    
    # Get search term
    term = get_input("What are you looking for? (e.g., pizza, sushi, coffee)", "shawarma")
    if not term:
        print("❌ Search term is required!")
        return
    
    # Get location
    print("\n📍 Location:")
    lat = get_input("  Latitude", 45.4215, float)
    lng = get_input("  Longitude", -75.6972, float)
    
    # Get optional filters
    print("\n🎛️  Filters (press Enter to skip):")
    radius_m = get_input("  Radius in meters", 5000, int)
    limit = get_input("  Max results", 10, int)
    
    open_now_input = get_input("  Open now only? (y/n)", "n")
    open_now = open_now_input.lower() in ['y', 'yes', 'true', '1']
    
    price = get_input("  Price levels (1,2,3,4)", "")
    
    # Build params
    params = {
        "term": term,
        "lat": lat,
        "lng": lng,
        "radius_m": radius_m,
        "limit": limit,
        "open_now": open_now
    }
    
    if price:
        params["price"] = price
    
    # Make request
    print("\n🔍 Searching...")
    print("-" * 70)
    
    try:
        response = client.get("/top", params=params)
        
        if response.status_code != 200:
            print(f"❌ Error {response.status_code}: {response.json().get('detail', 'Unknown error')}")
            return
        
        data = response.json()
        
        # Display results
        print(f"\n✅ Found {data['count']} results for '{data['term']}'")
        print(f"📍 Near ({data['center']['lat']}, {data['center']['lng']})")
        print(f"📏 Within {data['center']['radius_m']}m radius\n")
        print("=" * 70)
        
        for i, place in enumerate(data['results'], 1):
            print(f"\n{i}. {place['name']}")
            print(f"   ⭐ Rating: {place['rating']}★ ({place['review_count']} reviews)")
            print(f"   🎯 Bayesian Score: {place['score']} (credibility-adjusted)")
            
            if place['price']:
                print(f"   💰 Price: {place['price']}")
            
            print(f"   📍 Distance: {place['distance_m']}m ({place['distance_m']/1000:.1f}km)")
            print(f"   📫 Address: {place['address']}")
            print(f"   🔗 URL: {place['url']}")
        
        print("\n" + "=" * 70)
        print(f"ℹ️  {data['attribution']}")
        print("=" * 70)
        
        # Save option
        save = input("\n💾 Save results to file? (y/n): ").strip().lower()
        if save in ['y', 'yes']:
            filename = input("Filename [results.json]: ").strip() or "results.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved to {filename}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_examples():
    """Show example searches"""
    print("\n📚 EXAMPLE SEARCHES:\n")
    
    examples = [
        {
            "name": "Ottawa Shawarma",
            "params": "term=shawarma, lat=45.4215, lng=-75.6972, radius=10km"
        },
        {
            "name": "Toronto Sushi",
            "params": "term=sushi, lat=43.6532, lng=-79.3832, radius=5km"
        },
        {
            "name": "Montreal Coffee (Budget)",
            "params": "term=coffee, lat=45.5017, lng=-73.5673, price=1,2"
        },
        {
            "name": "Vancouver Pizza (Open Now)",
            "params": "term=pizza, lat=49.2827, lng=-123.1207, open_now=true"
        }
    ]
    
    for i, ex in enumerate(examples, 1):
        print(f"{i}. {ex['name']}")
        print(f"   {ex['params']}\n")

def main():
    """Main interactive loop"""
    print_header()
    
    while True:
        print("\n" + "=" * 70)
        print("MENU:")
        print("  1. New Search")
        print("  2. Show Examples")
        print("  3. Quit")
        print("=" * 70)
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            search_places()
        elif choice == '2':
            show_examples()
        elif choice == '3':
            print("\n👋 Thanks for using Yelp Top Places API!")
            break
        else:
            print("❌ Invalid option. Please choose 1, 2, or 3.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)
