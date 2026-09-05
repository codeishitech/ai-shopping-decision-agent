import pandas as pd


class RecommendationEngine:

    def __init__(self, products_df):

        self.df = products_df.copy()

    # ---------------------------------------------------------
    # HARD CONSTRAINTS
    # ---------------------------------------------------------

    def apply_hard_constraints(self, preferences):

        df = self.df.copy()

        budget = preferences.budget
        min_playtime = preferences.min_playtime
        required_anc = preferences.anc
        required_enc = preferences.enc

        # Budget
        if budget is not None:

            df = df[
                df["Selling_Price"] <= budget
            ]

        # Minimum playtime
        if min_playtime is not None:

            df = df[
                df["Playtime_Hours"].notna()
                & (
                    df["Playtime_Hours"]
                    >= min_playtime
                )
            ]

        # ANC
        if required_anc is True:

            df = df[
                df["ANC"]
                .fillna(False)
                .astype(bool)
                == True
            ]

        # ENC
        if required_enc is True:

            df = df[
                df["ENC"]
                .fillna(False)
                .astype(bool)
                == True
            ]

        return df

    # ---------------------------------------------------------
    # NORMALIZATION
    # ---------------------------------------------------------

    def normalize(
        self,
        series,
        higher_is_better=True
    ):

        series = pd.to_numeric(
            series,
            errors="coerce"
        )

        min_val = series.min()
        max_val = series.max()

        if pd.isna(min_val) or pd.isna(max_val):

            return pd.Series(
                0.5,
                index=series.index
            )

        if max_val == min_val:

            return pd.Series(
                1.0,
                index=series.index
            )

        normalized = (
            series - min_val
        ) / (
            max_val - min_val
        )

        if not higher_is_better:

            normalized = 1 - normalized

        return normalized.fillna(0.5)

    # ---------------------------------------------------------
    # FEATURE SCORES
    # ---------------------------------------------------------

    def calculate_feature_scores(self, df):

        df = df.copy()

        # Playtime
        df["score_playtime"] = self.normalize(
            df["Playtime_Hours"],
            higher_is_better=True
        )

        # Latency
        df["score_latency"] = self.normalize(
            df["Latency_ms"],
            higher_is_better=False
        )

        # Price
        df["score_price"] = self.normalize(
            df["Selling_Price"],
            higher_is_better=False
        )

        # Gaming
        df["score_gaming"] = (
            df["Gaming"]
            .fillna(False)
            .astype(bool)
            .astype(float)
        )

        # ANC
        df["score_anc"] = (
            df["ANC"]
            .fillna(False)
            .astype(bool)
            .astype(float)
        )

        # ENC
        df["score_enc"] = (
            df["ENC"]
            .fillna(False)
            .astype(bool)
            .astype(float)
        )

        return df

    # ---------------------------------------------------------
    # PRIORITY WEIGHTS
    # ---------------------------------------------------------

    def get_weights(self, priorities):

        if not priorities:

            return {
                "price": 0.20,
                "playtime": 0.20,
                "gaming": 0.20,
                "latency": 0.15,
                "anc": 0.15,
                "enc": 0.10
            }

        # Remove duplicates while preserving order
        unique_priorities = list(
            dict.fromkeys(priorities)
        )

        raw_weights = {}

        for i, priority in enumerate(
            unique_priorities
        ):

            raw_weights[priority] = (
                len(unique_priorities) - i
            )

        total = sum(
            raw_weights.values()
        )

        return {
            key: value / total
            for key, value in raw_weights.items()
        }

    # ---------------------------------------------------------
    # FINAL SCORE
    # ---------------------------------------------------------

    def calculate_final_score(
        self,
        df,
        priorities
    ):

        df = df.copy()

        weights = self.get_weights(
            priorities
        )

        df["final_score"] = 0.0

        score_columns = {
            "price": "score_price",
            "playtime": "score_playtime",
            "gaming": "score_gaming",
            "latency": "score_latency",
            "anc": "score_anc",
            "enc": "score_enc"
        }

        for preference, weight in weights.items():

            column = score_columns.get(
                preference
            )

            if column in df.columns:

                df["final_score"] += (
                    df[column] * weight
                )

        return df

    # ---------------------------------------------------------
    # SCORE BREAKDOWN
    # ---------------------------------------------------------

    def get_score_breakdown(
        self,
        product,
        preferences
    ):

        weights = self.get_weights(
            preferences.priorities
        )

        score_columns = {
            "price": "score_price",
            "playtime": "score_playtime",
            "gaming": "score_gaming",
            "latency": "score_latency",
            "anc": "score_anc",
            "enc": "score_enc"
        }

        breakdown = {}

        for preference, weight in weights.items():

            column = score_columns.get(
                preference
            )

            if (
                column
                and column in product.index
            ):

                feature_score = float(
                    product[column]
                )

                contribution = (
                    feature_score * weight
                )

                breakdown[preference] = {
                    "feature_score": round(
                        feature_score,
                        3
                    ),
                    "weight": round(
                        weight,
                        3
                    ),
                    "contribution": round(
                        contribution,
                        3
                    )
                }

        return breakdown

    # ---------------------------------------------------------
    # MAIN RECOMMENDATION
    # ---------------------------------------------------------

    def recommend(
        self,
        preferences,
        top_k=3
    ):

        filtered_df = (
            self.apply_hard_constraints(
                preferences
            )
        )

        if filtered_df.empty:

            return pd.DataFrame()

        # Remove duplicate products
        if "Product_ID" in filtered_df.columns:

            filtered_df = (
                filtered_df
                .sort_values("Selling_Price")
                .drop_duplicates(
                    "Product_ID"
                )
            )

        # Feature scores
        filtered_df = (
            self.calculate_feature_scores(
                filtered_df
            )
        )

        # Final score
        filtered_df = (
            self.calculate_final_score(
                filtered_df,
                preferences.priorities
            )
        )

        # Rank
        return (
            filtered_df
            .sort_values(
                "final_score",
                ascending=False
            )
            .head(top_k)
        )