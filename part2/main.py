"""
Part 2 API: AI Tutor Engine
Provides personalized study reports, student management, and conversational AI tutoring.
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import requests

load_dotenv()

# Add parent directory to path for backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from backend.unit_search import search_unit, UnitSearcher

from .conversation_manager import StudentConversationManager


# Configuration

PART1_API_URL = os.getenv("PART1_API_URL", "http://127.0.0.1:8000")
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")
USE_LM_STUDIO = os.getenv("USE_LM_STUDIO", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


# Enums and Models

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ResourceType(str, Enum):
    VIDEO = "video"
    ARTICLE = "article"
    TUTORIAL = "tutorial"


class KeyConcept(BaseModel):
    concept: str
    explain: str


class WeeklyTask(BaseModel):
    week: int = Field(..., ge=1, le=4)
    tasks: List[str] = Field(..., min_length=3, max_length=6)


class Quiz(BaseModel):
    q: str
    a: str
    difficulty: DifficultyLevel


class PublicResource(BaseModel):
    title: str
    url: str
    type: ResourceType
    why: str


class TutorReportMeta(BaseModel):
    source: str = "DegreePath Tutor"
    generated_at: str


class TutorReport(BaseModel):
    unit_code: str
    summary: str
    difficulty: DifficultyLevel
    core_skills: List[str]
    key_concepts: List[KeyConcept]
    study_plan: List[WeeklyTask]
    quizzes: List[Quiz]
    public_resources: List[PublicResource]
    student_specific_notes: str
    meta: TutorReportMeta


class StudentProfile(BaseModel):
    student_id: str
    name: str
    degree: str
    major: Optional[str] = None
    completed_units: List[str]
    enrolled_units: List[str]


class TutorRequest(BaseModel):
    unit_code: str
    student_id: Optional[str] = None
    completed_units: Optional[List[str]] = Field(default_factory=list)
    degree: Optional[str] = None
    major: Optional[str] = None


class ChatRequest(BaseModel):
    student_id: str
    message: str


class ChatResponse(BaseModel):
    student_id: str
    message: str
    response: str
    timestamp: str


class ChatHistory(BaseModel):
    student_id: str
    messages: List[dict]
    total_messages: int


# Student Management

class StudentManager:
    """In-memory student management."""
    
    STUDENTS_DB = {
        "demo001": StudentProfile(
            student_id="demo001",
            name="Alex Chen",
            degree="Bachelor of Information Technology",
            major="Software Development",
            completed_units=["COMP1000"],
            enrolled_units=["COMP1010", "COMP1350"]
        ),
        "demo002": StudentProfile(
            student_id="demo002",
            name="Sarah Johnson",
            degree="Bachelor of Information Technology",
            major="Cyber Security",
            completed_units=["COMP1000", "COMP1010", "COMP1300"],
            enrolled_units=["COMP2300", "COMP2310"]
        )
    }
    
    @classmethod
    def get_student(cls, student_id: str) -> Optional[StudentProfile]:
        return cls.STUDENTS_DB.get(student_id)
    
    @classmethod
    def list_students(cls) -> List[StudentProfile]:
        return list(cls.STUDENTS_DB.values())
    
    @classmethod
    def create_student(cls, profile: StudentProfile) -> StudentProfile:
        cls.STUDENTS_DB[profile.student_id] = profile
        return profile


# LM Studio Client

class LMStudioClient:
    """Client for LM Studio API with fallback support."""
    
    def __init__(self):
        self.base_url = LM_STUDIO_URL
        self.model_name = LM_STUDIO_MODEL
        self.enabled = USE_LM_STUDIO
        self.available = False
        
    def test_connection(self) -> bool:
        """Test if LM Studio is available."""
        if not self.enabled:
            return False
        
        try:
            response = requests.get(f"{self.base_url}/models", timeout=5)
            if response.status_code == 200:
                self.available = True
                return True
        except requests.exceptions.RequestException:
            pass
        
        return False
    
    def generate_text(self, prompt: str, max_tokens: int = 250) -> Optional[str]:
        """Generate text using LM Studio API."""
        if not self.available or not self.enabled:
            return None
        
        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful academic advisor."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        
        return None


# Resource Generator

class ResourceGenerator:
    """Generate learning resources for units."""
    
    @staticmethod
    def get_resources(unit_code: str, max_results: int = 6) -> List[Dict[str, str]]:
        """Generate learning resources for a unit."""
        resources = [
            {
                'title': f'{unit_code} - Official Unit Guide',
                'url': f'https://unitguides.mq.edu.au/unit_offerings/units/show/{unit_code}',
                'type': ResourceType.ARTICLE.value,
                'why': 'Official Macquarie University unit guide'
            }
        ]
        
        code_prefix = unit_code[:4].upper()
        
        topic_resources = {
            'COMP': [
                ('GeeksforGeeks', 'https://www.geeksforgeeks.org/', 'CS tutorials and practice'),
                ('Stack Overflow', 'https://stackoverflow.com/', 'Community Q&A'),
                ('MIT OpenCourseWare', 'https://ocw.mit.edu/courses/electrical-engineering-and-computer-science/', 'Free courses'),
            ],
            'MATH': [
                ('Khan Academy', 'https://www.khanacademy.org/math', 'Free math tutorials'),
                ('Wolfram Alpha', 'https://www.wolframalpha.com/', 'Computational math'),
            ],
            'STAT': [
                ('Khan Academy Statistics', 'https://www.khanacademy.org/math/statistics-probability', 'Statistics tutorials'),
            ],
        }
        
        topic_list = topic_resources.get(code_prefix, topic_resources['COMP'])
        
        for title, url, why in topic_list:
            resources.append({
                'title': title,
                'url': url,
                'type': ResourceType.TUTORIAL.value,
                'why': why
            })
        
        resources.append({
            'title': f'{unit_code} Tutorials - YouTube',
            'url': f'https://www.youtube.com/results?search_query={unit_code}+tutorial',
            'type': ResourceType.VIDEO.value,
            'why': 'Video tutorials'
        })
        
        return resources[:max_results]


# Part 1 API Client

class Part1APIClient:
    """Client for Part 1 API with fallback to direct web search."""
    
    @staticmethod
    def fetch_unit_details(unit_code: str) -> Dict[str, Any]:
        """Fetch unit details from Part 1 or fallback to web search."""
        try:
            response = requests.get(f"{PART1_API_URL}/unit/{unit_code}", timeout=10)
            response.raise_for_status()
            data = response.json()
            details = data.get("details", {})
            
            if details.get("title") or details.get("prerequisites"):
                return details
            
            raise requests.exceptions.RequestException("Empty response")
            
        except requests.exceptions.RequestException:
            try:
                web_data = search_unit(unit_code)
                if web_data and web_data.get("unit_code"):
                    return {
                        "title": web_data.get("title", "Unknown Unit"),
                        "year_level": int(unit_code[4]) if len(unit_code) > 4 and unit_code[4].isdigit() else 1,
                        "prerequisites": web_data.get("prerequisites", []),
                        "corequisites": web_data.get("corequisites", []),
                        "learning_outcomes": web_data.get("learning_outcomes", []),
                        "description": web_data.get("description", ""),
                        "credit_points": web_data.get("credit_points", 10),
                    }
            except Exception:
                pass
            
            return {
                "title": f"{unit_code} - Details Unavailable",
                "year_level": int(unit_code[4]) if len(unit_code) > 4 and unit_code[4].isdigit() else 1,
                "prerequisites": [],
                "learning_outcomes": [],
                "description": "Unit details temporarily unavailable.",
            }


# Report Generator

class TutorReportGenerator:
    """Generate study reports with AI or rule-based fallback."""
    
    def __init__(self, lm_client: LMStudioClient):
        self.lm_client = lm_client
        self.api_client = Part1APIClient()
    
    def generate_report(self, request: TutorRequest) -> TutorReport:
        """Generate comprehensive tutor report."""
        unit_details = self.api_client.fetch_unit_details(request.unit_code)
        
        student_profile = None
        if request.student_id:
            student_profile = StudentManager.get_student(request.student_id)
            if student_profile:
                request.completed_units = student_profile.completed_units
                request.degree = student_profile.degree
                request.major = student_profile.major
        
        learning_outcomes = unit_details.get("learning_outcomes", [])
        prerequisites = unit_details.get("prerequisites", [])
        year_level = unit_details.get("year_level", 1)
        title = unit_details.get("title", "Unknown Unit")
        
        summary = self._generate_summary(request.unit_code, title, learning_outcomes)
        difficulty = self._estimate_difficulty(year_level, learning_outcomes, prerequisites)
        core_skills = self._extract_core_skills(learning_outcomes)
        key_concepts = self._generate_key_concepts(learning_outcomes)
        study_plan = self._create_study_plan(learning_outcomes, difficulty)
        quizzes = self._generate_quizzes(learning_outcomes, difficulty)
        resources = ResourceGenerator.get_resources(request.unit_code)
        student_notes = self._generate_student_notes(
            request.completed_units or [],
            prerequisites,
            difficulty,
            student_profile
        )
        
        return TutorReport(
            unit_code=request.unit_code,
            summary=summary,
            difficulty=difficulty,
            core_skills=core_skills,
            key_concepts=key_concepts,
            study_plan=study_plan,
            quizzes=quizzes,
            public_resources=[PublicResource(**r) for r in resources],
            student_specific_notes=student_notes,
            meta=TutorReportMeta(generated_at=datetime.utcnow().isoformat())
        )
    
    def _generate_summary(self, unit_code: str, title: str, outcomes: List[str]) -> str:
        if not outcomes:
            return f"{title} introduces foundational concepts in computer science."
        
        prompt = f"Write a 2-3 sentence summary for: {title} ({unit_code}). Key outcomes: {'; '.join(outcomes[:3])}"
        ai_summary = self.lm_client.generate_text(prompt, max_tokens=150)
        
        if ai_summary and len(ai_summary) > 50:
            return ai_summary
        
        first_outcome = outcomes[0].replace("ULO1:", "").strip()[:150]
        return f"{title} focuses on {first_outcome}. Students develop theoretical understanding and practical skills."
    
    def _estimate_difficulty(self, year_level: int, outcomes: List[str], prereqs: List[str]) -> DifficultyLevel:
        score = (year_level - 1) * 2 + len(prereqs)
        
        complexity_keywords = ["advanced", "complex", "analyze", "evaluate", "design", "implement"]
        outcome_text = " ".join(outcomes).lower()
        for keyword in complexity_keywords:
            if keyword in outcome_text:
                score += 1
        
        if score <= 3:
            return DifficultyLevel.EASY
        elif score <= 7:
            return DifficultyLevel.MEDIUM
        return DifficultyLevel.HARD
    
    def _extract_core_skills(self, outcomes: List[str]) -> List[str]:
        skills = []
        for outcome in outcomes:
            clean = outcome.replace("ULO1:", "").replace("ULO2:", "").replace("ULO3:", "").replace("ULO4:", "").replace("ULO5:", "").strip()[:80]
            if clean and clean not in skills:
                skills.append(clean)
        return skills[:7]
    
    def _generate_key_concepts(self, outcomes: List[str]) -> List[KeyConcept]:
        concepts = []
        for i, outcome in enumerate(outcomes[:5], 1):
            clean_outcome = outcome.replace(f"ULO{i}:", "").strip()
            concept_name = " ".join(clean_outcome.split()[:6])
            
            prompt = f"Explain briefly for a student: {clean_outcome}"
            explanation = self.lm_client.generate_text(prompt, max_tokens=100)
            
            if not explanation or len(explanation) < 20:
                explanation = f"This focuses on {clean_outcome[:120]}."
            
            concepts.append(KeyConcept(concept=concept_name[:60], explain=explanation[:250]))
        return concepts
    
    def _create_study_plan(self, outcomes: List[str], difficulty: DifficultyLevel) -> List[WeeklyTask]:
        templates = [
            ["Review prerequisite materials", "Set up development environment", "Complete introductory readings"],
            ["Study core concepts", "Attend tutorials", "Start first assignment"],
            ["Practice intermediate exercises", "Join study group", "Continue assignment work"],
            ["Focus on advanced topics", "Complete assignments", "Prepare for assessments"]
        ]
        
        plan = []
        for week in range(1, 5):
            tasks = templates[week - 1].copy()
            outcomes_per_week = max(1, len(outcomes) // 4)
            start = (week - 1) * outcomes_per_week
            
            for outcome in outcomes[start:start + outcomes_per_week]:
                clean = outcome.replace("ULO1:", "").replace("ULO2:", "").replace("ULO3:", "").replace("ULO4:", "").replace("ULO5:", "").strip()
                tasks.append(f"Master: {clean[:65]}")
            
            plan.append(WeeklyTask(week=week, tasks=tasks[:6]))
        return plan
    
    def _generate_quizzes(self, outcomes: List[str], difficulty: DifficultyLevel) -> List[Quiz]:
        quizzes = []
        for i, outcome in enumerate(outcomes[:5]):
            clean = outcome.replace(f"ULO{i+1}:", "").strip()
            
            prompt = f"Create a quiz question and answer for: {clean}\nFormat: Question: [question]\nAnswer: [answer]"
            ai_quiz = self.lm_client.generate_text(prompt, max_tokens=200)
            
            if ai_quiz and "Answer:" in ai_quiz:
                parts = ai_quiz.split("Answer:")
                question = parts[0].replace("Question:", "").strip()
                answer = parts[1].strip()
            else:
                question = f"Describe how you would {clean[:90]}?"
                answer = f"To achieve this, understand {clean[:120]} and apply concepts from lectures."
            
            quiz_difficulty = difficulty if i < 2 else DifficultyLevel.MEDIUM
            quizzes.append(Quiz(q=question[:250], a=answer[:400], difficulty=quiz_difficulty))
        return quizzes
    
    def _generate_student_notes(
        self,
        completed_units: List[str],
        prerequisites: List[str],
        difficulty: DifficultyLevel,
        student_profile: Optional[StudentProfile] = None
    ) -> str:
        notes = []
        
        if student_profile:
            notes.append(f"Hi {student_profile.name.split()[0]}! ")
        
        missing_prereqs = [p for p in prerequisites if p not in completed_units]
        
        if missing_prereqs:
            notes.append(f"Missing prerequisites: {', '.join(missing_prereqs)}. Review these first.")
        else:
            notes.append("All prerequisites completed! You're ready to start.")
        
        if difficulty == DifficultyLevel.HARD:
            notes.append(" Plan for 12-15 hours/week.")
        elif difficulty == DifficultyLevel.MEDIUM:
            notes.append(" Plan for 8-10 hours/week.")
        else:
            notes.append(" Plan for 6-8 hours/week.")
        
        notes.append(" Start assignments early!")
        return "".join(notes)


# FastAPI Application

lm_studio_client = LMStudioClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    lm_studio_client.test_connection()
    yield


app = FastAPI(
    title="DegreePath Tutor - Part 2",
    description="AI-powered tutor with study reports and conversational AI",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

report_generator = TutorReportGenerator(lm_studio_client)

conversation_manager = StudentConversationManager(
    lm_studio_url=LM_STUDIO_URL,
    model_name=LM_STUDIO_MODEL,
    enabled=USE_LM_STUDIO
)


# Endpoints

@app.get("/")
def read_root():
    return {
        "service": "DegreePath Tutor - Part 2",
        "version": "1.0.0",
        "ai_enabled": lm_studio_client.available,
        "ai_backend": "LM Studio" if lm_studio_client.available else "rule-based"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "part1_api": PART1_API_URL,
        "lm_studio": lm_studio_client.available,
        "lm_studio_url": LM_STUDIO_URL,
        "search_ready": True
    }


@app.get("/students", response_model=List[StudentProfile])
def list_students():
    return StudentManager.list_students()


@app.get("/students/{student_id}", response_model=StudentProfile)
def get_student(student_id: str):
    student = StudentManager.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.post("/students", response_model=StudentProfile)
def create_student(profile: StudentProfile):
    return StudentManager.create_student(profile)


@app.post("/tutor-report", response_model=TutorReport)
async def generate_tutor_report(request: TutorRequest):
    try:
        return report_generator.generate_report(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.get("/tutor-report/{unit_code}", response_model=TutorReport)
async def get_tutor_report_simple(unit_code: str, student_id: Optional[str] = None):
    request = TutorRequest(unit_code=unit_code.upper(), student_id=student_id)
    return await generate_tutor_report(request)


@app.post("/chat", response_model=ChatResponse)
async def chat_with_tutor(request: ChatRequest):
    student = StudentManager.get_student(request.student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student not found: {request.student_id}")
    
    try:
        response_text = conversation_manager.chat(
            student_id=request.student_id,
            message=request.message,
            student_profile=student.dict()
        )
        
        return ChatResponse(
            student_id=request.student_id,
            message=request.message,
            response=response_text,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/chat/stream")
async def chat_with_tutor_stream(request: ChatRequest):
    student = StudentManager.get_student(request.student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student not found: {request.student_id}")
    
    async def generate_stream():
        try:
            memory = conversation_manager.get_or_create_memory(request.student_id)
            prompt = conversation_manager._build_prompt(
                request.message,
                memory.get_messages(),
                student.dict()
            )
            
            if conversation_manager.enabled:
                try:
                    response = requests.post(
                        f"{LM_STUDIO_URL}/chat/completions",
                        json={
                            "model": LM_STUDIO_MODEL,
                            "messages": [
                                {"role": "system", "content": "You are a helpful university tutor."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 500,
                            "stream": True
                        },
                        stream=True,
                        timeout=60
                    )
                    
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            line_text = line.decode('utf-8')
                            if line_text.startswith('data: '):
                                data = line_text[6:]
                                if data == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data)
                                    if 'choices' in chunk and len(chunk['choices']) > 0:
                                        content = chunk['choices'][0].get('delta', {}).get('content', '')
                                        if content:
                                            full_response += content
                                            yield f"data: {json.dumps({'content': content})}\n\n"
                                except json.JSONDecodeError:
                                    pass
                    
                    memory.add_message("student", request.message)
                    memory.add_message("tutor", full_response)
                    conversation_manager.set_student_context(request.student_id, student.dict())
                    
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    
                except Exception:
                    fallback = conversation_manager._fallback_response(request.message, student.dict())
                    memory.add_message("student", request.message)
                    memory.add_message("tutor", fallback)
                    
                    for word in fallback.split(' '):
                        yield f"data: {json.dumps({'content': word + ' '})}\n\n"
                    yield f"data: {json.dumps({'done': True})}\n\n"
            else:
                fallback = conversation_manager._fallback_response(request.message, student.dict())
                memory.add_message("student", request.message)
                memory.add_message("tutor", fallback)
                
                for word in fallback.split(' '):
                    yield f"data: {json.dumps({'content': word + ' '})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.get("/chat/{student_id}/history", response_model=ChatHistory)
async def get_conversation_history(student_id: str):
    student = StudentManager.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student not found: {student_id}")
    
    messages = conversation_manager.get_conversation_history(student_id)
    return ChatHistory(student_id=student_id, messages=messages, total_messages=len(messages))


@app.delete("/chat/{student_id}")
async def clear_conversation(student_id: str):
    student = StudentManager.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student not found: {student_id}")
    
    conversation_manager.clear_conversation(student_id)
    return {"status": "cleared", "student_id": student_id}


@app.get("/chat/stats")
async def get_chat_statistics():
    return {"status": "ok", "statistics": conversation_manager.get_statistics()}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("PART2_HOST", "127.0.0.1")
    port = int(os.getenv("PART2_PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
