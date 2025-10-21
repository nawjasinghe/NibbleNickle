def find_item(options, preference):
    pref = (preference or "").strip().lower()
    if not pref:
        return None

    best_key = None
    best_price = float('inf')
    print("Calculating Best Deals")
    for key, value in options.items():
        if isinstance(value, (int, float)) and pref in key.lower() and value < best_price:
            best_key, best_price = key, float(value)

    return (best_key, best_price) if best_key is not None else None
  
