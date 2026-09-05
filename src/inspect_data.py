import pandas as pd

path = "data/raw/headphones.csv"

df = pd.read_csv(path)

print("=" * 60)
print("HEADPHONE DATASET")
print("=" * 60)

print("\nShape:")
print(df.shape)

print("\nColumns:")
for column in df.columns:
    print("-", column)

print("\nFirst 5 rows:")
print(df.head().to_string())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isnull().sum())

print("\nDuplicate rows:")
print(df.duplicated().sum())

print("\nSample titles:")
for title in df["Title"].sample(20, random_state=42):
    print("-", title)
    
import re

titles = df["Title"].fillna("")

patterns = {
    "playtime": r'(\d+)\s*(?:hours?|hrs?|h)\b.*?(?:playback|playtime)',
    "driver": r'(\d+(?:\.\d+)?)\s*mm\s*(?:driver)?',
    "ip_rating": r'\b(IP\d{1,2}[A-Z]?)\b',
    "bluetooth": r'\bBluetooth\s*(?:v(?:ersion)?\.?\s*)?(\d+(?:\.\d+)?)',
    "latency": r'(\d+)\s*ms\s*(?:low\s*)?latency',
}

for name, pattern in patterns.items():
    matches = titles.str.extract(pattern, flags=re.IGNORECASE, expand=False)
    
    print(f"\n{name}:")
    print("Products containing:", matches.notna().sum())
    print("Examples:")
    print(matches.dropna().head(10).tolist())