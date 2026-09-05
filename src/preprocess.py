import pandas as pd
import re

INPUT_PATH = "data/raw/headphones.csv"
OUTPUT_PATH = "data/processed/headphones_clean.csv"

# 1. Load dataset
df = pd.read_csv(INPUT_PATH)

print("Original rows:", len(df))


# 2. Remove exact duplicates
df = df.drop_duplicates()
# Create a product identity ignoring colour variants
df["Product_ID"] = (
    df["Brand"].astype(str).str.strip()
    + "_"
    + df["Model"].astype(str).str.strip()
)

print("After removing exact duplicates:", len(df))



# 3. Calculate discount
df["Discount_Percent"] = (
    (df["Actual_Price"] - df["Selling_Price"])
    / df["Actual_Price"]
    * 100
).round(2)


# 4. Extract playtime
import re

def extract_playtime(title):
    if not isinstance(title, str):
        return None
        
    # Matches integers or floats followed optionally by spaces and playtime units
    pattern = r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b"
    match = re.search(pattern, title, re.IGNORECASE)

    if match:
        return float(match.group(1))

    return None


df["Playtime_Hours"] = df["Title"].apply(extract_playtime)


def extract_driver_size(title):
    pattern = r"(\d+(?:\.\d+)?)\s*mm\s*driver"
    match = re.search(pattern, title, re.IGNORECASE)

    if match:
        return float(match.group(1))

    return None


df["Driver_Size_mm"] = df["Title"].apply(extract_driver_size)

def extract_bluetooth_version(title):
    pattern = r"Bluetooth\s*v(?:ersion)?\.?\s*(\d+(?:\.\d+)?)"
    match = re.search(pattern, title, re.IGNORECASE)

    if match:
        return float(match.group(1))

    return None


df["Bluetooth_Version"] = df["Title"].apply(extract_bluetooth_version)


# 7. Extract latency

def extract_latency(title):
    if not isinstance(title, str):
        return None

    # Matches numbers followed by 'ms', optional words like 'low/ultra low', 
    # and optional keywords 'latency' or 'delay'
    pattern = r"(\d+)\s*ms\b"
    match = re.search(pattern, title, re.IGNORECASE)

    if match:
        return float(match.group(1))

    return None

df["Latency_ms"] = df["Title"].apply(extract_latency)


# 8. Detect useful features
df["Gaming"] = df["Title"].str.contains(
    "gaming", case=False, na=False
)

df["ANC"] = df["Title"].str.contains(
    r"\bANC\b|active noise",
    case=False,
    regex=True,
    na=False
)

df["ENC"] = df["Title"].str.contains(
    r"\bENC\b|ENx",
    case=False,
    regex=True,
    na=False
)



# 9. Save
df.to_csv(OUTPUT_PATH, index=False)

print("\nSaved cleaned dataset to:")
print(OUTPUT_PATH)

print("\nNew columns:")
print([
    "Discount_Percent",
    "Playtime_Hours",
    "Driver_Size_mm",
    "Bluetooth_Version",
    "Latency_ms",
    "Gaming",
    "ANC",
    "ENC"
])