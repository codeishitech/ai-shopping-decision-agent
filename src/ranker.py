import pandas as pd


def rank_products(df, preferences):

    results = df.copy()

    # Keep only the best variant of each product
    results = (
        results.sort_values("Selling_Price")
        .drop_duplicates("Product_ID")
    )

    scores = []

    for _, product in results.iterrows():

        score = 0

        # Price
        if "price" in preferences.priorities:
            if preferences.budget is not None:
                price_score = max(
                    0,
                    1 - (product["Selling_Price"] / preferences.budget)
                )
                score += price_score * 40

        # Playtime
        if "playtime" in preferences.priorities:
            if preferences.min_playtime is not None:
                playtime = product["Playtime_Hours"]

                if pd.notna(playtime):
                    playtime_score = min(
                        playtime / preferences.min_playtime,
                        2
                    ) / 2

                    score += playtime_score * 40

        # Gaming
        if "gaming" in preferences.priorities:
            if product["Gaming"]:
                score += 20
                # Low latency
        if "latency" in preferences.priorities:
            latency = product["Latency_ms"]

            if pd.notna(latency):
                # Lower latency = better
                latency_score = max(0, 1 - latency / 100)
                score += latency_score * 20

        # ANC
        if "anc" in preferences.priorities:
            if product["ANC"]:
                score += 20

        # ENC
        if "enc" in preferences.priorities:
            if product["ENC"]:
                score += 20
        scores.append(round(score, 2))

    results["Score"] = scores

    return results.sort_values(
        "Score",
        ascending=False
    )