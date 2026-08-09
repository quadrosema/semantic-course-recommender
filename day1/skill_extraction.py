import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

SYSTEM_PROMPT = (
    "You extract professional/technical skills from a user's message. "
    "Return ONLY a JSON array of short skill strings (e.g. [\"backend development\", \"machine learning\"]). "
    "No explanation, no markdown, just the JSON array. If no skills are mentioned, return []."
)


def extract_skills(user_text: str) -> list[str]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()

    try:
        skills = json.loads(raw)
        if isinstance(skills, list):
            return [str(s).strip() for s in skills if str(s).strip()]
    except json.JSONDecodeError:
        pass

    print(f"Warning: could not parse skill extraction response: {raw!r}")
    return []


if __name__ == "__main__":
    test_inputs = [
        "I want to learn AI and backend development",
        "I'm interested in improving my cloud and security skills",
        "Not sure what I want yet",
    ]

    for text in test_inputs:
        skills = extract_skills(text)
        print(f"Input: {text!r}")
        print(f"Extracted skills: {skills}\n")