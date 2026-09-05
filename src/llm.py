import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found. Check the .env file."
    )

client = genai.Client(api_key=api_key)

def generate_response(
    preferences,
    recommendations,
    tradeoff=None,
    conversation_history=None
):
    if not recommendations:
        return (
            "I couldn't find an exact match for all your requirements."
        )

    best = recommendations[0]
    product = best["product"]

    fallback = (
        f"I recommend {product['Title']} at "
        f"₹{product['Selling_Price']:.0f}. "
        f"It is the highest-ranked option based on your preferences."
    )

    try:
        products = []

        for item in recommendations:
            p = item["product"]
            e = item["explanation"]

            products.append({
                "title": str(p["Title"]),
                "price": float(p["Selling_Price"]),
                "score": float(p["final_score"]),
                "reasons": e["reasons"],
                "tradeoffs": e["tradeoffs"],
                "score_breakdown": item["score_breakdown"]
            })

        prompt = f"""
You are an AI shopping decision assistant.

User preferences:
{preferences}

Recommendation engine results:
{products}

Trade-off analysis:
{tradeoff}

The recommendation engine has already ranked the products.

Explain the result using ONLY this data.

Act like a helpful real-world shopkeeper:
- Recommend the best option.
- Explain why it fits the user's priorities.
- Mention the strongest alternative.
- Clearly explain important trade-offs.
- If there is a trade-off, explain what the user would gain
  or lose by choosing the alternative.
- Do not invent specifications, prices, features, or products.
- Keep the answer concise.

Give:
1. Best choice
2. Why it fits
3. Main alternative
4. Trade-offs
5. Final recommendation
"""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        if response.text:
            return response.text

        return fallback

    except Exception as e:
        print(f"\nGemini unavailable: {e}")
        return fallback