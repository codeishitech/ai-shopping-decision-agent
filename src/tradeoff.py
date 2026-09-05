def compare_products(best, alternative, preferences):
    
    tradeoffs = []

    # ---------------------------------------------------------
    # PRICE
    # ---------------------------------------------------------
    if "price" in preferences.priorities:

        best_price = best["Selling_Price"]
        alt_price = alternative["Selling_Price"]

        if alt_price > best_price:
            difference = alt_price - best_price

            tradeoffs.append(
                f"the alternative costs ₹{difference:.0f} more"
            )

        elif alt_price < best_price:
            difference = best_price - alt_price

            tradeoffs.append(
                f"the alternative costs ₹{difference:.0f} less"
            )

    # ---------------------------------------------------------
    # PLAYTIME
    # ---------------------------------------------------------
    if "playtime" in preferences.priorities:

        best_playtime = best["Playtime_Hours"]
        alt_playtime = alternative["Playtime_Hours"]

        if (
            best_playtime == best_playtime
            and alt_playtime == alt_playtime
        ):

            if alt_playtime > best_playtime:
                difference = alt_playtime - best_playtime

                tradeoffs.append(
                    f"the alternative offers {difference:.0f} "
                    "more hours of playtime"
                )

            elif alt_playtime < best_playtime:
                difference = best_playtime - alt_playtime

                tradeoffs.append(
                    f"the alternative offers {difference:.0f} "
                    "fewer hours of playtime"
                )

    # ---------------------------------------------------------
    # LATENCY
    # ---------------------------------------------------------
    if "latency" in preferences.priorities:

        best_latency = best["Latency_ms"]
        alt_latency = alternative["Latency_ms"]

        if (
            best_latency == best_latency
            and alt_latency == alt_latency
        ):

            if alt_latency < best_latency:
                difference = best_latency - alt_latency

                tradeoffs.append(
                    f"the alternative has {difference:.0f} ms "
                    "lower latency"
                )

            elif alt_latency > best_latency:
                difference = alt_latency - best_latency

                tradeoffs.append(
                    f"the alternative has {difference:.0f} ms "
                    "higher latency"
                )

    # ---------------------------------------------------------
    # GAMING
    # ---------------------------------------------------------
    if "gaming" in preferences.priorities:

        if best["Gaming"] and not alternative["Gaming"]:
            tradeoffs.append(
                "the alternative is not marked as gaming-focused"
            )

        elif not best["Gaming"] and alternative["Gaming"]:
            tradeoffs.append(
                "the alternative is marked as gaming-focused"
            )

    # ---------------------------------------------------------
    # ANC
    # ---------------------------------------------------------
    if "anc" in preferences.priorities:

        if best["ANC"] and not alternative["ANC"]:
            tradeoffs.append(
                "the alternative does not list ANC"
            )

        elif not best["ANC"] and alternative["ANC"]:
            tradeoffs.append(
                "the alternative offers ANC"
            )

    # ---------------------------------------------------------
    # ENC
    # ---------------------------------------------------------
    if "enc" in preferences.priorities:

        if best["ENC"] and not alternative["ENC"]:
            tradeoffs.append(
                "the alternative does not list ENC"
            )

        elif not best["ENC"] and alternative["ENC"]:
            tradeoffs.append(
                "the alternative offers ENC"
            )

    return tradeoffs