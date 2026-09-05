# 🎧 AI Shopping Decision Agent

An AI-powered shopping assistant that helps users make informed purchasing decisions based on their preferences, priorities, budget, and trade-offs. Rather than simply returning a list of products, the agent explains **why** a product is recommended and what the user gains or gives up with each alternative.

---

## 🚀 Key Features

- **Natural-language preference extraction** — understands user intent directly from free-form queries
- **Conversational follow-up questions** — asks clarifying questions when preferences are incomplete or ambiguous
- **Budget and battery-life constraints** — filters products against hard numeric limits
- **Gaming, ANC, and ENC preference handling** — matches use-case-specific requirements (low latency, noise cancellation, call quality)
- **Personalized product ranking** — scores and orders products based on the user's stated priorities
- **Explainable recommendations** — every suggestion comes with a clear rationale
- **Score breakdown** — transparent view of the ranking factors behind each recommendation
- **Alternative product suggestions** — surfaces close runner-up options
- **Trade-off analysis** — compares the top pick against alternatives across key attributes
- **Gemini-powered natural-language explanations** — generates fluent, context-aware justifications
- **Graceful fallback** — degrades to rule-based explanations when the LLM is unavailable

---

## 🧠 How It Works

The agent follows a multi-stage decision pipeline:

```text
User Query
    ↓
Preference Extraction
    ↓
Conversation / Follow-up Questions
    ↓
Hard Product Filtering
    ↓
Recommendation Ranking
    ↓
Explainability Engine
    ↓
Trade-off Analysis
    ↓
Gemini Explanation
    ↓
Final Recommendation
```

| Stage | Purpose |
|---|---|
| **Preference Extraction** | Parses the user's natural-language query into structured preferences (budget, use case, must-have features) |
| **Conversation / Follow-up Questions** | Fills in missing or ambiguous preferences through targeted clarifying questions |
| **Hard Product Filtering** | Removes products that violate non-negotiable constraints (e.g., budget cap, minimum battery life) |
| **Recommendation Ranking** | Scores the remaining products against weighted user priorities |
| **Explainability Engine** | Produces a breakdown of which factors drove each product's score |
| **Trade-off Analysis** | Compares the top recommendation against close alternatives, highlighting what's gained or sacrificed |
| **Gemini Explanation** | Converts the structured scoring and trade-off data into a natural, conversational explanation |
| **Final Recommendation** | Presents the ranked pick, its rationale, and alternatives to the user |

---

## 📌 Notes

- If the Gemini API is unavailable or fails, the agent falls back to a deterministic, rule-based explanation so the pipeline never breaks.
- The ranking and filtering stages are preference-driven, so the same product catalog can produce different results for different users.

---

## 🛣️ Roadmap Ideas

- [ ] Support additional product categories beyond audio devices
- [ ] Add persistent user profiles for returning users
- [ ] Expose the pipeline as an API for third-party integration


