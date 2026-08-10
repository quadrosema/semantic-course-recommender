from sqlalchemy import insert, select

from day1.courses_data import courses as course_catalog
from day2.database import (
    DATABASE_URL,
    courses,
    create_schema,
    get_engine,
    skills,
    user_skills,
    users,
)


SAMPLE_USERS = [
    {
        "name": "Amina Khalil",
        "email": "amina.khalil@example.com",
        "skills": ["Python", "data analysis", "machine learning"],
    },
    {
        "name": "Omar Nasser",
        "email": "omar.nasser@example.com",
        "skills": ["backend development", "Node.js", "API design"],
    },
    {
        "name": "Lina Haddad",
        "email": "lina.haddad@example.com",
        "skills": ["cloud computing", "cybersecurity", "DevOps"],
    },
]


def seed_database(database_url: str = DATABASE_URL) -> dict[str, int]:
    create_schema(database_url)
    engine = get_engine(database_url)

    summary = {"courses": 0, "skills": 0, "users": 0, "user_skills": 0}

    with engine.begin() as connection:
        existing_course_ids = set(connection.scalars(select(courses.c.id)))
        new_courses = [
            course for course in course_catalog if course["id"] not in existing_course_ids
        ]
        if new_courses:
            connection.execute(insert(courses), new_courses)
            summary["courses"] = len(new_courses)

        skill_names = sorted(
            {skill for user in SAMPLE_USERS for skill in user["skills"]}
        )
        existing_skill_names = set(connection.scalars(select(skills.c.name)))
        new_skills = [
            {"name": skill} for skill in skill_names if skill not in existing_skill_names
        ]
        if new_skills:
            connection.execute(insert(skills), new_skills)
            summary["skills"] = len(new_skills)

        for sample_user in SAMPLE_USERS:
            user_id = connection.scalar(
                select(users.c.id).where(users.c.email == sample_user["email"])
            )
            if user_id is None:
                result = connection.execute(
                    insert(users).values(
                        name=sample_user["name"], email=sample_user["email"]
                    )
                )
                user_id = result.inserted_primary_key[0]
                summary["users"] += 1

            for skill_name in sample_user["skills"]:
                skill_id = connection.scalar(
                    select(skills.c.id).where(skills.c.name == skill_name)
                )
                relationship_exists = connection.scalar(
                    select(user_skills.c.user_id).where(
                        user_skills.c.user_id == user_id,
                        user_skills.c.skill_id == skill_id,
                    )
                )
                if relationship_exists is None:
                    connection.execute(
                        insert(user_skills).values(user_id=user_id, skill_id=skill_id)
                    )
                    summary["user_skills"] += 1

    return summary


if __name__ == "__main__":
    result = seed_database()
    print(
        "Seed complete: "
        f"{result['courses']} courses, "
        f"{result['skills']} skills, "
        f"{result['users']} users, and "
        f"{result['user_skills']} user-skill links added."
    )
