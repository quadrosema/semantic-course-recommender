import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from courses_data import courses
from embeddings import embed_texts, embed_text
from skill_extraction import extract_skills


_course_texts = [f"{c['title']}: {c['description']}" for c in courses]
_course_embeddings = embed_texts(_course_texts)


def build_user_vector(skills: list[str]) -> np.ndarray:
    skill_embeddings = embed_texts(skills)
    return np.mean(skill_embeddings, axis=0)


def rank_courses(user_vector: np.ndarray, top_n: int = 3):
    scores = cosine_similarity(user_vector.reshape(1, -1), _course_embeddings)[0]
    ranked_indices = np.argsort(scores)[::-1][:top_n]
    return [(courses[i], float(scores[i])) for i in ranked_indices]


def explain_match(skills: list[str], course: dict) -> str:
    course_text = f"{course['title']}: {course['description']}"
    course_vec = embed_text(course_text)
    skill_embeddings = embed_texts(skills)
    skill_scores = cosine_similarity(skill_embeddings, course_vec.reshape(1, -1)).flatten()
    best_skill = skills[int(np.argmax(skill_scores))]
    return f"Recommended because your interest in '{best_skill}' closely matches this course's focus."


def recommend(skills: list[str] = None, user_text: str = None, top_n: int = 3) -> dict:
    if skills is None:
        if user_text is None:
            raise ValueError("Provide either `skills` or `user_text`.")
        skills = extract_skills(user_text)

    if not skills:
        return {
            "skills": [],
            "recommendations": [],
            "message": "No skills could be identified from the input.",
        }

    user_vector = build_user_vector(skills)
    ranked = rank_courses(user_vector, top_n=top_n)

    recommendations = []
    for course, score in ranked:
        recommendations.append({
            "title": course["title"],
            "category": course["category"],
            "similarity_score": round(score, 4),
            "explanation": explain_match(skills, course),
        })

    return {
        "skills": skills,
        "recommendations": recommendations,
        "message": None,
    }


if __name__ == "__main__":
    test_cases = [
        "I want to learn AI and backend development",
        "I'm interested in improving my cloud and security skills",
        "I want to get better at design and building user interfaces",
    ]

    for text in test_cases:
        result = recommend(user_text=text, top_n=3)
        print(f"\nInput: {text!r}")
        print(f"Extracted skills: {result['skills']}")
        if result["message"]:
            print(result["message"])
        for i, rec in enumerate(result["recommendations"], 1):
            print(f"  {i}. {rec['title']} ({rec['category']}) — score: {rec['similarity_score']}")
            print(f"     {rec['explanation']}")
