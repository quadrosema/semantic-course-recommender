from langchain_core.tools import tool

from day1.skill_extraction import extract_skills
from day2.recommendation_pipeline import recommend_for_skills


@tool
def skill_extraction_agent(user_text: str) -> list[str]:
    """Extract technical skills from the user's text."""
    return extract_skills(user_text)


@tool
def course_recommendation_agent(skills: list[str], top_n: int = 3) -> dict:
    """Recommend courses based on a list of extracted skills."""
    return recommend_for_skills(skills, top_n=top_n)


if __name__ == "__main__":
    text = "I want to learn AI and backend development"
    extracted_skills = skill_extraction_agent.invoke({"user_text": text})
    result = course_recommendation_agent.invoke(
        {"skills": extracted_skills, "top_n": 3}
    )
    print(f"Extracted skills: {extracted_skills}")
    print(result)
