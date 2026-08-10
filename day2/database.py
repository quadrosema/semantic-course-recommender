import os
from pathlib import Path

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'db.sqlite3'}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False),
    Column("email", String(255), nullable=False, unique=True),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
)

skills = Table(
    "skills",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(100), nullable=False, unique=True),
)

courses = Table(
    "courses",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(255), nullable=False, unique=True),
    Column("description", Text, nullable=False),
    Column("category", String(100), nullable=False),
)

user_skills = Table(
    "user_skills",
    metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

embeddings = Table(
    "embeddings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("entity_type", String(20), nullable=False),
    Column("entity_id", Integer, nullable=False),
    Column("model_name", String(100), nullable=False),
    Column("vector", JSON, nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
    CheckConstraint("entity_type IN ('skill', 'course')", name="valid_embedding_entity_type"),
    UniqueConstraint(
        "entity_type", "entity_id", "model_name", name="unique_entity_embedding"
    ),
)

recommendation_logs = Table(
    "recommendation_logs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("course_id", ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
    Column("rank", Integer, nullable=False),
    Column("similarity_score", Float, nullable=False),
    Column("explanation", Text, nullable=False),
    Column("created_at", DateTime, nullable=False, server_default=func.now()),
    CheckConstraint("rank > 0", name="positive_recommendation_rank"),
)

Index("ix_embeddings_entity", embeddings.c.entity_type, embeddings.c.entity_id)
Index("ix_recommendation_logs_user", recommendation_logs.c.user_id)


def get_engine(database_url: str = DATABASE_URL):
    """Return a database engine, using SQLite by default."""
    return create_engine(database_url, future=True)


def create_schema(database_url: str = DATABASE_URL) -> None:
    metadata.create_all(get_engine(database_url))


if __name__ == "__main__":
    create_schema()
    print(f"Database schema is ready at {DATABASE_URL}")
