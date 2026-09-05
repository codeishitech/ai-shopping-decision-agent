def explain_product(product, preferences):
    """
    Generate human-readable reasons and trade-offs
    for a recommended product.
    """

    reasons = []
    tradeoffs = []

    # ---------------------------------------------------------
    # PRICE
    # ---------------------------------------------------------
    if preferences.budget is not None:
        price = product["Selling_Price"]

        if price <= preferences.budget:
            reasons.append(
                f"fits your ₹{preferences.budget:.0f} budget"
            )
        else:
            tradeoffs.append(
                f"costs ₹{price - preferences.budget:.0f} over your budget"
            )

    # ---------------------------------------------------------
    # PLAYTIME
    # ---------------------------------------------------------
    if preferences.min_playtime is not None:
        playtime = product["Playtime_Hours"]

        if playtime == playtime:  # checks for NaN
            if playtime >= preferences.min_playtime:
                reasons.append(
                    f"offers {playtime:.0f} hours of advertised playtime"
                )
            else:
                tradeoffs.append(
                    f"offers only {playtime:.0f} hours "
                    f"against your {preferences.min_playtime:.0f}-hour target"
                )
        else:
            tradeoffs.append(
                "playtime information is unavailable"
            )

    # ---------------------------------------------------------
    # GAMING
    # ---------------------------------------------------------
    if preferences.gaming is True:
        if bool(product["Gaming"]):
            reasons.append(
                "is marked as suitable for gaming"
            )
        else:
            tradeoffs.append(
                "is not marked as a gaming-focused product"
            )

    # ---------------------------------------------------------
    # LATENCY
    # ---------------------------------------------------------
    if "latency" in preferences.priorities:

        latency = product["Latency_ms"]

        if latency == latency:
            reasons.append(
                f"has an advertised latency of {latency:.0f} ms"
            )
        else:
            tradeoffs.append(
                "latency information is unavailable"
            )

    # ---------------------------------------------------------
    # ANC
    # ---------------------------------------------------------
    if preferences.anc is True:
        if bool(product["ANC"]):
            reasons.append(
                "supports ANC"
            )
        else:
            tradeoffs.append(
                "does not have ANC according to the product data"
            )

    # ---------------------------------------------------------
    # ENC
    # ---------------------------------------------------------
    if preferences.enc is True:
        if bool(product["ENC"]):
            reasons.append(
                "supports ENC for calls"
            )
        else:
            tradeoffs.append(
                "does not have ENC according to the product data"
            )

    return {
        "reasons": reasons,
        "tradeoffs": tradeoffs
    }