# Skills Utilization Platform & Course Recommendation Engine

An AI-powered course recommendation system that extracts skills from natural-language user input and recommends relevant courses using transformer embeddings, semantic similarity, SQLAlchemy, LangChain, LangGraph, and Flask.

## Overview

The system takes either:

* A registered user's ID and retrieves their stored skills from the database.
* Free-form text describing what the user wants to learn.

It then generates semantic embeddings for skills and courses, builds a user-interest representation, calculates cosine similarity, and returns ranked course recommendations with explanations.

The project was developed as a three-day progression from a core AI recommendation engine into a database-backed API and finally an agent/workflow-based system.

---

## Architecture

```text
                    ┌──────────────────────┐
                    │      Flask API       │
                    │   POST /api/recommend│
                    └──────────┬───────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
             user_id                    user_text
                 │                           │
                 ▼                           ▼
       Day 2 Recommendation          Day 3 LangGraph
             Pipeline                     Workflow
                 │                           │
                 │                    ┌──────┴──────┐
                 │                    │             │
                 │                    ▼             ▼
                 │              Skill Extraction  Course
                 │                 Agent       Recommendation
                 │                               Agent
                 │                    │             │
                 └────────────────────┴─────────────┘
                                      │
                                      ▼
                            Ranked Recommendations
                                      │
                                      ▼
                                JSON Response
```

---

## Project Structure

```text
Project_5/
│
├── day1/
│   ├── embeddings.py
│   ├── skill_extraction.py
│   └── ...
│
├── day2/
│   ├── api.py
│   ├── database.py
│   ├── recommendation_pipeline.py
│   ├── seed_data.py
│   └── ...
│
├── day3/
│   ├── agents.py
│   ├── workflow.py
│   └── ...
│
├── db.sqlite3
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Day 1 — Core AI Engine

Day 1 implements the core semantic recommendation engine.

### 1. Skill Extraction

Natural-language input is converted into a list of relevant skills.

Example:

```text
"I want to learn AI and backend development"
```

Produces:

```json
[
  "AI",
  "backend development"
]
```

### 2. Embedding Generation

Skills and course descriptions are converted into vector representations using a transformer-based embedding model.

### 3. User Profile Vector

When multiple skills are available, their embeddings are combined using average pooling:

```text
User Vector = mean(skill embeddings)
```

This creates a single representation of the user's interests.

### 4. Semantic Course Matching

Course vectors are compared with the user-interest vector using cosine similarity.

Higher similarity means stronger semantic relevance.

### 5. Recommendation Output

The recommendation engine returns:

* Course ID
* Course title
* Category
* Similarity score
* Explanation

Example:

```json
{
  "course_id": 4,
  "title": "Backend Development with Node.js",
  "category": "Backend",
  "similarity_score": 0.8067,
  "explanation": "Recommended because your interest in 'backend development' closely matches this course's focus."
}
```

---

# Day 2 — Backend Integration

Day 2 converts the recommendation logic into a database-backed application.

## Database

SQLAlchemy Core is used for database access.

The SQLite database contains:

### Users

Stores registered users.

### Skills

Stores available skills.

### Courses

Stores course metadata and descriptions.

### UserSkills

Many-to-many relationship between users and skills.

### Embeddings

Stores generated embeddings for skills and courses.

### Recommendation Logs

Stores recommendation decisions for users, including:

* User ID
* Course ID
* Rank
* Similarity score
* Explanation
* Timestamp

## Sample Data

The database contains sample users, skills, and courses for testing the recommendation pipeline.

The course catalog currently contains areas including:

* Data Science
* AI / Machine Learning
* Backend Development
* Cloud Computing
* DevOps
* Databases
* Frontend Development
* Cybersecurity
* NLP
* Mobile Development
* Data Engineering
* Design

---

# Recommendation Pipeline

The database-backed pipeline performs the following process:

```text
User ID
   ↓
Retrieve user skills
   ↓
Load/generate skill embeddings
   ↓
Build user profile vector
   ↓
Load/generate course embeddings
   ↓
Calculate cosine similarity
   ↓
Rank courses
   ↓
Return Top N recommendations
```

Embeddings are cached in the database so they do not need to be regenerated every time.

---

# Day 3 — Agents & Workflow Orchestration

Day 3 introduces LangChain tools and LangGraph workflow orchestration.

## LangChain Agents

Two LangChain tools are implemented:

### Skill Extraction Agent

```text
skill_extraction_agent
```

Responsible for extracting relevant skills from natural-language input.

### Course Recommendation Agent

```text
course_recommendation_agent
```

Responsible for passing extracted skills into the database-backed recommendation pipeline.

---

## LangGraph Workflow

The agents are connected using LangGraph.

Current workflow:

```text
START
  ↓
Skill Extraction
  ↓
Course Recommendation
  ↓
END
```

The workflow maintains structured state containing:

```text
user_text
top_n
skills
recommendations
message
```

Example:

```json
{
  "skills": [
    "AI",
    "backend development"
  ],
  "recommendations": [
    {
      "course_id": 4,
      "title": "Backend Development with Node.js",
      "category": "Backend",
      "similarity_score": 0.8067
    },
    {
      "course_id": 5,
      "title": "Backend Development with Django",
      "category": "Backend",
      "similarity_score": 0.8051
    }
  ],
  "message": null
}
```

---

# API

The application exposes:

```text
POST /api/recommend
```

## Request Using User ID

```json
{
  "user_id": 1,
  "top_n": 3
}
```

## Request Using Free Text

```json
{
  "user_text": "I want to learn AI and backend development",
  "top_n": 3
}
```

The API validates:

* Request body type
* `user_id`
* `user_text`
* `top_n`
* Mutually exclusive `user_id` / `user_text`
* Missing input
* Nonexistent users

---

# Example Output

```json
{
  "skills": [
    "AI",
    "backend development"
  ],
  "recommendations": [
    {
      "course_id": 4,
      "title": "Backend Development with Node.js",
      "category": "Backend",
      "similarity_score": 0.8067,
      "explanation": "Recommended because your interest in 'backend development' closely matches this course's focus."
    },
    {
      "course_id": 5,
      "title": "Backend Development with Django",
      "category": "Backend",
      "similarity_score": 0.8051,
      "explanation": "Recommended because your interest in 'backend development' closely matches this course's focus."
    },
    {
      "course_id": 9,
      "title": "Frontend Development with React",
      "category": "Frontend",
      "similarity_score": 0.743,
      "explanation": "Recommended because your interest in 'backend development' closely matches this course's focus."
    }
  ],
  "message": null
}
```

---

# Installation

## 1. Clone the repository

```bash
git clone <repository-url>
cd Project_5
```

## 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

---

# Database Setup

Create the database schema:

```powershell
python -m day2.database
```

Populate the sample data:

```powershell
python -m day2.seed_data
```

---

# Running the Components

## Test Day 1

Run the relevant Day 1 modules to verify skill extraction and embedding generation.

## Test Day 2

```powershell
python -m day2.recommendation_pipeline
```

## Test Day 3 Agents

```powershell
python -m day3.agents
```

## Test Day 3 Workflow

```powershell
python -m day3.workflow
```

Expected workflow:

```text
Skill Extraction
        ↓
Course Recommendation
        ↓
Structured Recommendation Output
```

---

# Running the API

Start Flask:

```powershell
python -m day2.api
```

The API will be available at:

```text
http://127.0.0.1:5000
```

Example PowerShell request:

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:5000/api/recommend" `
  -ContentType "application/json" `
  -Body '{"user_text":"I want to learn AI and backend development","top_n":3}'
```

---

# Technologies

* Python
* Flask
* SQLAlchemy Core
* SQLite
* NumPy
* scikit-learn
* Sentence Transformers
* LangChain
* LangGraph

---

# AI Approach

The recommendation engine combines:

1. Natural-language skill extraction
2. Transformer-based embeddings
3. Average pooling for user profiles
4. Cosine similarity
5. Vector-based ranking
6. Database-backed embedding storage
7. LangChain tools
8. LangGraph workflow orchestration

This provides a lightweight semantic recommendation architecture without requiring a dedicated vector database.

---

# Validation

The implemented system has been tested with:

* Valid user IDs
* Free-text recommendations
* Multiple extracted skills
* Empty text
* Text without recognizable skills
* Invalid `top_n`
* Missing request parameters
* Conflicting `user_id` and `user_text`
* Nonexistent users
* Direct recommendation pipeline execution
* LangChain agent execution
* LangGraph workflow execution
* Flask API execution

---

# Future Improvements

Potential extensions include:

* Better recommendation confidence thresholds
* Guardrails for weak semantic matches
* Fallback recommendations
* Recommendation logging for anonymous/free-text requests
* Explanation generation using an LLM
* User feedback and recommendation learning
* Personalized ranking based on previous interactions
* Vector database integration
* Authentication
* Frontend dashboard
* Recommendation evaluation metrics
* Automated API tests
* Docker deployment

---

# Project Goal

The goal of this project is to demonstrate how modern AI components can be combined with traditional backend engineering to build a practical recommendation system.

The architecture progresses from a basic semantic similarity engine to a database-backed service and finally to an agentic workflow using LangChain and LangGraph.
