from conversation import ConversationState
from pipeline import load_products
from recommender import RecommendationEngine
from explainer import explain_product
from tradeoff import compare_products
from llm import generate_response

def filter_products(df, preferences):

    results = df.copy()

    # ---------------------------------------------------------
    # Budget
    # ---------------------------------------------------------

    if preferences.budget is not None:

        results = results[
            results["Selling_Price"] <= preferences.budget
        ]

    # ---------------------------------------------------------
    # Minimum playtime
    # ---------------------------------------------------------

    if preferences.min_playtime is not None:

        results = results[
            results["Playtime_Hours"].notna()
            & (
                results["Playtime_Hours"]
                >= preferences.min_playtime
            )
        ]

    # ---------------------------------------------------------
    # Connectivity
    # ---------------------------------------------------------

    if preferences.connectivity is not None:

        results = results[
            results["Connectivity_Type"]
            .fillna("")
            .str.contains(
                preferences.connectivity,
                case=False,
                na=False
            )
        ]

    # ---------------------------------------------------------
    # Gaming
    # ---------------------------------------------------------

    if preferences.gaming is True:

        results = results[
            results["Gaming"]
            .fillna(False)
            .astype(bool)
            == True
        ]

    # ---------------------------------------------------------
    # ANC
    # ---------------------------------------------------------

    if preferences.anc is True:

        results = results[
            results["ANC"]
            .fillna(False)
            .astype(bool)
            == True
        ]

    # ---------------------------------------------------------
    # ENC
    # ---------------------------------------------------------

    if preferences.enc is True:

        results = results[
            results["ENC"]
            .fillna(False)
            .astype(bool)
            == True
        ]

    return results


def get_follow_up_question(preferences, state=None):

    # ---------------------------------------------------------
    # 1. Budget
    # ---------------------------------------------------------

    if preferences.budget is None:

        return (
            "What's your maximum budget?",
            "budget"
        )

    # ---------------------------------------------------------
    # 2. Latency
    #
    # Only ask this once.
    # ---------------------------------------------------------

    gaming_requested = getattr(
        preferences,
        "gaming",
        False
    )

    latency_already_addressed = getattr(
        state,
        "latency_addressed",
        False
    )

    latency_is_priority = (
        "latency"
        in getattr(
            preferences,
            "priorities",
            []
        )
    )

    if (
        gaming_requested
        and not latency_already_addressed
        and not latency_is_priority
    ):

        return (
            "Since you're looking for gaming earbuds, "
            "is low latency important to you?",
            "latency"
        )

    # ---------------------------------------------------------
    # 3. Battery
    # ---------------------------------------------------------

    if preferences.min_playtime is None:

        return (
            "How much battery life would you like at minimum?",
            "min_playtime"
        )

    return None, None


class ShoppingAgent:

    def __init__(self):

        self.state = ConversationState()

        self.products = load_products()

        self.engine = RecommendationEngine(
            self.products
        )

    def process(self, text, top_n=3):

        # ---------------------------------------------------------
        # 1. Initialize or update conversation
        # ---------------------------------------------------------

        if self.state.preferences is None:

            preferences = self.state.initialize(text)

        else:

            preferences = self.state.update(text)

        # ---------------------------------------------------------
        # 2. Follow-up question
        # ---------------------------------------------------------

        follow_up, pending_key = get_follow_up_question(
            preferences,
            state=self.state
        )

        if follow_up:

            self.state.set_pending_preference(
                pending_key
            )

            self.state.add_assistant_message(
                follow_up
            )

            return {
                "type": "follow_up",
                "preferences": preferences,
                "recommendations": [],
                "follow_up": follow_up
            }

        # ---------------------------------------------------------
        # 3. No more follow-ups
        # ---------------------------------------------------------

        self.state.clear_pending_preference()

        # ---------------------------------------------------------
        # 4. Hard filtering
        # ---------------------------------------------------------

        filtered_df = filter_products(
            self.products,
            preferences
        )

        if filtered_df.empty:

            message = (
                "I couldn't find an exact match for all "
                "of your requirements. We can broaden the "
                "budget or relax one of the feature "
                "requirements if you'd like."
            )

            self.state.add_assistant_message(message)

            return {
                "type": "results",
                "preferences": preferences,
                "recommendations": [],
                "message": message
            }

        # ---------------------------------------------------------
        # 5. Ranking
        # ---------------------------------------------------------

        filtered_engine = RecommendationEngine(
            filtered_df
        )

        ranked = filtered_engine.recommend(
            preferences,
            top_k=top_n
        )

        if ranked.empty:

            message = (
                "I found products within your filters, "
                "but couldn't rank them reliably."
            )

            self.state.add_assistant_message(message)

            return {
                "type": "results",
                "preferences": preferences,
                "recommendations": [],
                "message": message
            }

        # ---------------------------------------------------------
        # 6. Build recommendation objects
        # ---------------------------------------------------------

        recommendations = []

        for _, product in ranked.iterrows():

            explanation = explain_product(
                product,
                preferences
            )

            breakdown = filtered_engine.get_score_breakdown(
                product,
                preferences
            )

            recommendations.append({
                "product": product,
                "explanation": explanation,
                "score_breakdown": breakdown,
                "final_score": float(
                    product.get("final_score", 0)
                )
            })

        # ---------------------------------------------------------
        # 7. Trade-off analysis
        # ---------------------------------------------------------

        tradeoff = None

        if len(recommendations) > 1:

            best_product = recommendations[0]["product"]
            all_tradeoffs={}
            for alternative in recommendations[1:]:
                alternative_product = alternative["product"]
    
                differences = compare_products(
            best_product,
            alternative_product,
            preferences
        )
        
                if differences:
                    alternative_name = str(
                alternative_product["Title"]
            )
                    all_tradeoffs[alternative_name] = differences 
            if all_tradeoffs:
                tradeoff = all_tradeoffs
        # ---------------------------------------------------------
        # 8. Result object
        # ---------------------------------------------------------

        result = {
            "type": "results",
            "preferences": preferences,
            "recommendations": recommendations,
            "tradeoff": tradeoff
        }

        # ---------------------------------------------------------
        # 9. Gemini explanation
        # ---------------------------------------------------------

        try:

            conversation_history = getattr(
                self.state,
                "messages",
                []
            )

            gemini_response = generate_response(
    user_query=text,
    result=result
)

            result["gemini_response"] = gemini_response

            if gemini_response:

                self.state.add_assistant_message(
                    gemini_response
                )

        except Exception as e:

            # Gemini must NEVER break the recommender.

            result["gemini_response"] = None
            result["llm_error"] = str(e)

        return result