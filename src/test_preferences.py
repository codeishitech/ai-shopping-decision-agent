from preferences import extract_preferences


query = """
I need wireless gaming earbuds under ₹1500.
Battery should be at least 30 hours.
Low latency is really important.
I also want good call quality.
"""


preferences = extract_preferences(query)

print("Budget:", preferences.budget)
print("Minimum playtime:", preferences.min_playtime)
print("Gaming:", preferences.gaming)
print("ANC:", preferences.anc)
print("ENC:", preferences.enc)
print("Priorities:", preferences.priorities)