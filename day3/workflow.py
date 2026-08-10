import json
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from day3.agents import course_recommendation_agent, skill_extraction_agent
from sqlalchemy import insert
from day2.database import (
    DATABASE_URL,
    get_engine,
    recommendation_logs,
)


class RecommendationState(TypedDict, total=False):
    user_text: str
    top_n: int
    skills: list[str]
    recommendations: list[dict]
    message: str | None
    valid: bool


def validate_input_node(state: RecommendationState) -> dict:
    """Validate the user's input before running the recommendation pipeline."""
    user_text = state.get("user_text", "").strip()
    top_n = state.get("top_n", 3)

    if not user_text:
        return {
            "valid": False,
            "skills": [],
            "recommendations": [],
            "message": "Please provide some text describing what you want to learn.",
        }

    if not isinstance(top_n, int) or top_n < 1:
        return {
            "valid": False,
            "skills": [],
            "recommendations": [],
            "message": "top_n must be a positive integer.",
        }

    return {
        "valid": True,
        "user_text": user_text,
        "top_n": min(top_n, 10),
        "message": None,
    }


def route_after_validation(state: RecommendationState) -> str:
    """Route valid input to extraction or invalid input directly to the end."""
    if state.get("valid", False):
        return "extract_skills"

    return END


def extract_skills_node(state: RecommendationState) -> dict:
    """Extract technical skills from the user's text."""
    try:
        skills = skill_extraction_agent.invoke(
            {"user_text": state["user_text"]}
        )

        if not skills:
            return {
                "skills": [],
                "recommendations": [],
                "message": "I couldn't identify any relevant skills from your request.",
            }

        return {
            "skills": skills,
            "message": None,
        }

    except Exception as exc:
        print(f"Skill extraction error: {exc}")

        return {
            "skills": [],
            "recommendations": [],
            "message": (
                "I couldn't extract skills from your request. "
                "Please try rephrasing it."
            ),
        }


def recommend_courses_node(state: RecommendationState) -> dict:
    """Generate course recommendations from extracted skills."""
    if not state.get("skills"):
        return {
            "recommendations": [],
            "message": state.get(
                "message",
                "No skills were identified, so recommendations "
                "could not be generated.",
            ),
        }

    try:
        result = course_recommendation_agent.invoke(
            {
                "skills": state["skills"],
                "top_n": state.get("top_n", 3),
            }
        )

        recommendations = result.get("recommendations", [])

        if not recommendations:
            return {
                "recommendations": [],
                "message": (
                    "No matching courses were found for the "
                    "extracted skills."
                ),
            }

        return {
            "recommendations": recommendations,
            "message": result.get("message"),
        }

    except Exception as exc:
        print(f"Recommendation error: {exc}")

        return {
            "recommendations": [],
            "message": (
                "I couldn't generate course recommendations "
                "right now. Please try again."
            ),
        }


def build_recommendation_workflow():
    workflow = StateGraph(RecommendationState)

    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("extract_skills", extract_skills_node)
    workflow.add_node("recommend_courses", recommend_courses_node)

    workflow.add_edge(START, "validate_input")

    workflow.add_conditional_edges(
        "validate_input",
        route_after_validation,
        {
            "extract_skills": "extract_skills",
            END: END,
        },
    )

    workflow.add_edge("extract_skills", "recommend_courses")
    workflow.add_edge("recommend_courses", END)

    return workflow.compile()


recommendation_workflow = build_recommendation_workflow()


def recommend_with_workflow(
    user_text: str,
    top_n: int = 3,
    user_id: int | None = None,
) -> dict:
    """Run the complete recommendation workflow."""
    result = recommendation_workflow.invoke(
        {
            "user_text": user_text,
            "top_n": top_n,
        }
    )
    if user_id is not None and result.get("recommendations"):
        log_recommendations(
            user_id=user_id,
            recommendations=result["recommendations"],
    )

    return {
        "skills": result.get("skills", []),
        "recommendations": result.get("recommendations", []),
        "message": result.get("message"),
    }


if __name__ == "__main__":
    output = recommend_with_workflow(
        "I want to learn AI and backend development"
    )

    print(json.dumps(output, indent=2))


def log_recommendations(
    user_id: int,
    recommendations: list[dict],
    database_url: str = DATABASE_URL,
) -> None:
    """Store generated recommendations for an existing user."""
    if not recommendations:
        return

    with get_engine(database_url).begin() as connection:
        for rank, recommendation in enumerate(recommendations, start=1):
            connection.execute(
                insert(recommendation_logs).values(
                    user_id=user_id,
                    course_id=recommendation["course_id"],
                    rank=rank,
                    similarity_score=recommendation["similarity_score"],
                    explanation=recommendation["explanation"],
                )
            )
