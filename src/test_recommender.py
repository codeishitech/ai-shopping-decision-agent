import pandas as pd
from ranker import rank_products
from models import UserPreferences
from recommender import filter_products


df = pd.read_csv("data/processed/headphones_clean.csv")

preferences = UserPreferences(
    budget=1500,
    min_playtime=30,
    connectivity="Bluetooth",
    gaming=True,
    priorities=[
        "price",
        "playtime",
        "gaming",
        "latency"
    ]
)

results = filter_products(df, preferences)


print("Matching products:", len(results))
print()

print(
    results[
        ["Title", "Selling_Price", "Playtime_Hours", "Brand"]
    ].head(10).to_string(index=False)
)

ranked = rank_products(results, preferences)

print("\nTOP 10 RECOMMENDATIONS:")
print(
    ranked[
        ["Title", "Selling_Price", "Playtime_Hours", "Gaming", "Score"]
    ].head(10).to_string(index=False)
)



from explainer import explain_product


top_product = ranked.iloc[0]

explanation = explain_product(
    top_product,
    preferences
)

print("\nWHY THIS PRODUCT?")
for reason in explanation["reasons"]:
    print("✓", reason)

print("\nTRADE-OFFS:")
for tradeoff in explanation["tradeoffs"]:
    print("—", tradeoff)
    
    
    
from tradeoff import compare_products


best = ranked.iloc[0]
alternative = ranked.iloc[1]

print("\nWHY NOT THE SECOND PRODUCT?")

reasons = compare_products(
    best,
    alternative,
    preferences
)

for reason in reasons:
    print("—", reason)