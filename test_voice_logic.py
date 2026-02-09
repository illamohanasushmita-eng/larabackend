import asyncio
import re
from datetime import datetime, timedelta

# Mocking the function logic since I can't easily import the full app structure without env vars
def process_text_mock(user_text):
    clean_text = user_text
    
    # Simple verb extraction simulation (from ai_service.py)
    action_verbs = ["call", "buy", "meet", "clean", "finish"]
    lower_clean = clean_text.lower()
    final_start_index = 0
    
    remind_match = re.search(r"remind\s+(?:me|us)\s+to\s+", lower_clean)
    if remind_match:
        final_start_index = remind_match.end()
    else:
        verb_pattern = r"\b(" + "|".join(action_verbs) + r")\b"
        verb_match = re.search(verb_pattern, lower_clean)
        if verb_match:
            final_start_index = verb_match.start()
            
    real_title = clean_text[final_start_index:].strip()
    
    # PRONOUN LOGIC (Exact Copy)
    replacements = [
        (r"\bI'm\b", "You're"),
        (r"\bI\b", "You"),
        (r"\bmy\b", "your"),
        (r"\bMy\b", "Your"),
        (r"\bme\b", "you"),
        (r"\bam\b", "are"),
    ]
    
    for pattern, replacement in replacements:
        real_title = re.sub(pattern, replacement, real_title, flags=re.IGNORECASE)
        
    return real_title.capitalize()

print("--- Voice Logic Test ---")
tests = [
    "Remind me to call my mom",
    "I need to fix my car",
    "Add meeting with my boss",
    "Buy milk for me",
    "I am going home",
    "Remind me that I'm awesome"
]

for t in tests:
    res = process_text_mock(t)
    print(f"In:  '{t}'\nOut: '{res}'\n")
