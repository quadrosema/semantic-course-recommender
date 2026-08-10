import json

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import insert, select

from day1.embeddings import MODEL_NAME, embed_texts
from day2.database import (
    DATABASE_URL,
    courses,
    create_schema,
    embeddings,
    get_engine,
    skills,
    user_skills,
    users,
)


def _load_embeddings(connection, entity_type: str, entity_ids: list[int]) -> dict[int, np.ndarray]:
    if not entity_ids:
        return {}

    rows = connection.execute(
        select(embeddings.c.entity_id, embeddings.c.vector).where(
            embeddings.c.entity_type == entity_type,
            embeddings.c.entity_id.in_(entity_ids),
            embeddings.c.model_name == MODEL_NAME,
        )
    ).mappings()
    return {
        row["entity_id"]: np.asarray(row["vector"], dtype=np.float32)
        for row in rows
    }


def _ensure_embeddings(
    connection, entity_type: str, texts_by_id: dict[int, str]
) -> dict[int, np.ndarray]:
    vectors = _load_embeddings(connection, entity_type, list(texts_by_id))
    missing_ids = [entity_id for entity_id in texts_by_id if entity_id not in vectors]

    if missing_ids:
        generated_vectors = embed_texts([texts_by_id[entity_id] for entity_id in missing_ids])
        connection.execute(
            insert(embeddings),
            [
                {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "model_name": MODEL_NAME,
                    "vector": vector.tolist(),
                }
                for entity_id, vector in zip(missing_ids, generated_vectors)
            ],
        )
        vectors.update(
            {
                entity_id: np.asarray(vector, dtype=np.float32)
                for entity_id, vector in zip(missing_ids, generated_vectors)
            }
        )

    return vectors


def _explain_match(
    skill_names: list[str], skill_vectors: np.ndarray, course_vector: np.ndarray
) -> str:
    skill_scores = cosine_similarity(skill_vectors, course_vector.reshape(1, -1)).flatten()
    best_skill = skill_names[int(np.argmax(skill_scores))]
    return f"Recommended because your interest in '{best_skill}' closely matches this course's focus."


def _rank_courses(
    connection, skill_names: list[str], skill_vectors: np.ndarray, top_n: int
) -> list[dict]:
    """Rank stored courses against the provided skill vectors."""
    course_rows = connection.execute(
        select(courses.c.id, courses.c.title, courses.c.description, courses.c.category)
        .order_by(courses.c.id)
    ).mappings().all()
    if not course_rows:
        return []

    course_texts = {
        row["id"]: f"{row['title']}: {row['description']}" for row in course_rows
    }
    course_vectors_by_id = _ensure_embeddings(connection, "course", course_texts)
    course_vectors = np.vstack(
        [course_vectors_by_id[row["id"]] for row in course_rows]
    )
    user_vector = np.mean(skill_vectors, axis=0)
    scores = cosine_similarity(user_vector.reshape(1, -1), course_vectors)[0]
    ranked_indexes = np.argsort(scores)[::-1][:top_n]

    recommendations = []
    for index in ranked_indexes:
        course = course_rows[int(index)]
        course_vector = course_vectors[int(index)]
        recommendations.append(
    {
        "course_id": course["id"],
        "title": course["title"],
        "category": course["category"],
        "similarity_score": round(float(scores[index]), 4),
        "explanation": _explain_match(
            skill_names, skill_vectors, course_vector
        ),
    }
)
    return recommendations


def recommend_for_skills(
    skill_names: list[str], top_n: int = 3, database_url: str = DATABASE_URL
) -> dict:
    """Rank database courses for skills supplied outside a stored user profile."""
    if top_n < 1:
        raise ValueError("`top_n` must be at least 1.")

    cleaned_skills = [skill.strip() for skill in skill_names if skill.strip()]
    if not cleaned_skills:
        return {
            "skills": [],
            "recommendations": [],
            "message": "No skills could be identified from the input.",
        }

    create_schema(database_url)
    skill_vectors = embed_texts(cleaned_skills)
    with get_engine(database_url).begin() as connection:
        recommendations = _rank_courses(
            connection, cleaned_skills, skill_vectors, top_n
        )

    return {
        "skills": cleaned_skills,
        "recommendations": recommendations,
        "message": None if recommendations else "No courses are stored in the database.",
    }


def recommend_for_user(
    user_id: int, top_n: int = 3, database_url: str = DATABASE_URL
) -> dict:
    if top_n < 1:
        raise ValueError("`top_n` must be at least 1.")

    create_schema(database_url)
    engine = get_engine(database_url)

    with engine.begin() as connection:
        user_name = connection.scalar(
            select(users.c.name).where(users.c.id == user_id)
        )
        if user_name is None:
            raise ValueError(f"User with id {user_id} does not exist.")

        skill_rows = connection.execute(
            select(skills.c.id, skills.c.name)
            .join(user_skills, skills.c.id == user_skills.c.skill_id)
            .where(user_skills.c.user_id == user_id)
            .order_by(skills.c.name)
        ).mappings().all()

        if not skill_rows:
            return {
                "user_id": user_id,
                "user_name": user_name,
                "skills": [],
                "recommendations": [],
                "message": "No skills are stored for this user.",
            }

        skill_texts = {row["id"]: row["name"] for row in skill_rows}
        skill_names = list(skill_texts.values())
        skill_vectors_by_id = _ensure_embeddings(connection, "skill", skill_texts)
        skill_vectors = np.vstack(
            [skill_vectors_by_id[skill_id] for skill_id in skill_texts]
        )
        recommendations = _rank_courses(
            connection, skill_names, skill_vectors, top_n
        )

    return {
        "user_id": user_id,
        "user_name": user_name,
        "skills": skill_names,
        "recommendations": recommendations,
        "message": None if recommendations else "No courses are stored in the database.",
    }


if __name__ == "__main__":
    print(json.dumps(recommend_for_user(user_id=1), indent=2))
