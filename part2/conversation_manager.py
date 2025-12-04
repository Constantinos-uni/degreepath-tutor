"""
Conversation Manager for Student-Tutor Interactions
Uses simple in-memory storage for conversation history
Integrates with RAG and Web Search for accurate information
Enhanced context tracking for better personalization
"""

import os
import sys
import re
import json
from typing import Dict, Optional, List, Set
import requests
from datetime import datetime
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Part 1 API URL
PART1_API_URL = os.getenv("PART1_API_URL", "http://127.0.0.1:8000")

# Persistence directory
PERSISTENCE_DIR = Path(__file__).parent / "data" / "conversations"


class ConversationMemory:
    """Enhanced conversation memory with topic tracking"""
    
    def __init__(self, student_id: str = None):
        self.student_id = student_id
        self.messages: List[dict] = []
        self.discussed_units: Set[str] = set()  # Track units discussed
        self.discussed_topics: Set[str] = set()  # Track general topics
        self.session_start = datetime.utcnow().isoformat()
        self.last_activity = datetime.utcnow().isoformat()
    
    def add_message(self, role: str, content: str):
        """Add a message to history and extract topics"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_activity = datetime.utcnow().isoformat()
        
        # Extract and track unit codes mentioned
        unit_codes = re.findall(r'[A-Z]{4}\d{4}', content.upper())
        self.discussed_units.update(unit_codes)
        
        # Track general topics
        topic_keywords = {
            "prerequisites": ["prerequisite", "prereq", "require", "need to take"],
            "enrollment": ["enroll", "register", "sign up"],
            "study_tips": ["study", "prepare", "learn", "tips"],
            "assignments": ["assignment", "project", "homework", "task"],
            "difficulty": ["hard", "difficult", "struggle", "confused"],
            "career": ["career", "job", "work", "industry"],
            "schedule": ["schedule", "time", "plan", "week"],
        }
        
        content_lower = content.lower()
        for topic, keywords in topic_keywords.items():
            if any(kw in content_lower for kw in keywords):
                self.discussed_topics.add(topic)
    
    def get_messages(self) -> List[dict]:
        """Get all messages"""
        return self.messages
    
    def get_recent_messages(self, n: int = 10) -> List[dict]:
        """Get last n messages"""
        return self.messages[-n:] if len(self.messages) > n else self.messages
    
    def get_context_summary(self) -> dict:
        """Get a summary of conversation context"""
        return {
            "total_messages": len(self.messages),
            "discussed_units": list(self.discussed_units),
            "discussed_topics": list(self.discussed_topics),
            "session_start": self.session_start,
            "last_activity": self.last_activity
        }
    
    def clear(self):
        """Clear all messages but keep topic history"""
        self.messages = []
        # Keep discussed_units and discussed_topics for continuity
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for persistence"""
        return {
            "student_id": self.student_id,
            "messages": self.messages,
            "discussed_units": list(self.discussed_units),
            "discussed_topics": list(self.discussed_topics),
            "session_start": self.session_start,
            "last_activity": self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConversationMemory':
        """Deserialize from dictionary"""
        memory = cls(student_id=data.get("student_id"))
        memory.messages = data.get("messages", [])
        memory.discussed_units = set(data.get("discussed_units", []))
        memory.discussed_topics = set(data.get("discussed_topics", []))
        memory.session_start = data.get("session_start", datetime.utcnow().isoformat())
        memory.last_activity = data.get("last_activity", datetime.utcnow().isoformat())
        return memory


class StudentConversationManager:
    """Manages conversation context and memory for each student with persistence"""
    
    def __init__(self, lm_studio_url: str, model_name: str, enabled: bool = True):
        """
        Initialize conversation manager
        
        Args:
            lm_studio_url: Base URL for LM Studio API
            model_name: Name of the model to use
            enabled: Whether LM Studio is enabled (fallback if False)
        """
        self.lm_studio_url = lm_studio_url
        self.model_name = model_name
        self.enabled = enabled
        
        # Store conversation memory per student
        self.conversations: Dict[str, ConversationMemory] = {}
        
        # Store student contexts (profile info)
        self.student_contexts: Dict[str, dict] = {}
        
        # Ensure persistence directory exists
        PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing conversations from disk
        self._load_conversations()
    
    def _load_conversations(self):
        """Load saved conversations from disk"""
        try:
            for file_path in PERSISTENCE_DIR.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                        student_id = data.get("student_id")
                        if student_id:
                            self.conversations[student_id] = ConversationMemory.from_dict(data.get("memory", {}))
                            if data.get("context"):
                                self.student_contexts[student_id] = data["context"]
                            print(f"[LOADED] Conversation for {student_id}")
                except Exception as e:
                    print(f"[WARN] Failed to load {file_path}: {e}")
        except Exception as e:
            print(f"[WARN] Failed to load conversations: {e}")
    
    def _save_conversation(self, student_id: str):
        """Save conversation to disk"""
        try:
            file_path = PERSISTENCE_DIR / f"{student_id}.json"
            data = {
                "student_id": student_id,
                "memory": self.conversations[student_id].to_dict() if student_id in self.conversations else {},
                "context": self.student_contexts.get(student_id, {}),
                "saved_at": datetime.utcnow().isoformat()
            }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[WARN] Failed to save conversation for {student_id}: {e}")
    
    def get_or_create_memory(self, student_id: str) -> ConversationMemory:
        """Get or create conversation memory for a student"""
        if student_id not in self.conversations:
            self.conversations[student_id] = ConversationMemory(student_id=student_id)
        return self.conversations[student_id]
    
    def set_student_context(self, student_id: str, context: dict):
        """Store student context for future reference"""
        self.student_contexts[student_id] = {
            **context,
            "context_set_at": datetime.utcnow().isoformat()
        }
        # Persist changes
        self._save_conversation(student_id)
    
    def get_student_context(self, student_id: str) -> Optional[dict]:
        """Get stored student context"""
        return self.student_contexts.get(student_id)
    
    def chat(
        self, 
        student_id: str, 
        message: str, 
        student_profile: Optional[dict] = None
    ) -> str:
        """
        Have a conversation with context and memory.
        Integrates RAG + Web Search for accurate information.
        
        Args:
            student_id: Student identifier
            message: Student's message/question
            student_profile: Optional student profile for context
            
        Returns:
            AI tutor's response
        """
        memory = self.get_or_create_memory(student_id)
        
        # Update student context if provided
        if student_profile:
            self.set_student_context(student_id, student_profile)
        
        # Fetch RAG context and live unit data for mentioned units
        rag_context = self._fetch_rag_context(message)
        live_unit_context = self._fetch_live_unit_context(message)
        
        # Also check for units from previous conversation
        if memory.discussed_units:
            for code in list(memory.discussed_units)[:2]:  # Add context for up to 2 previously discussed units
                if code not in live_unit_context:
                    try:
                        response = requests.get(f"{PART1_API_URL}/unit/{code}", timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            details = data.get("details", {})
                            live_unit_context[code] = {
                                "title": details.get("title", "Unknown"),
                                "prerequisites": details.get("prerequisites", []),
                                "credit_points": details.get("credit_points", 10),
                                "learning_outcomes": details.get("learning_outcomes", [])[:3]
                            }
                    except:
                        pass
        
        # Build context-aware prompt with RAG + Live data + Memory
        prompt = self._build_prompt(
            message, 
            memory.get_messages(), 
            student_profile,
            rag_context=rag_context,
            live_unit_context=live_unit_context,
            memory=memory
        )
        
        # Get response from LM Studio or fallback
        print(f"[DEBUG] Chat enabled={self.enabled}, URL={self.lm_studio_url}")
        
        if self.enabled:
            print("[DEBUG] Attempting LM Studio call...")
            answer = self._call_lm_studio(prompt)
            if not answer:  # If LM Studio failed
                print("[WARN] LM Studio returned no answer, using fallback")
                answer = self._fallback_response(message, student_profile, live_unit_context)
        else:
            print("[DEBUG] LM Studio disabled, using fallback")
            answer = self._fallback_response(message, student_profile, live_unit_context)
        
        # Save to memory (includes topic tracking)
        memory.add_message("student", message)
        memory.add_message("tutor", answer)
        
        # Persist conversation to disk
        self._save_conversation(student_id)
        
        return answer
    
    def _fetch_rag_context(self, message: str) -> str:
        """Fetch relevant context from RAG system via Part 1 API"""
        try:
            response = requests.post(
                f"{PART1_API_URL}/rag/query",
                json={
                    "query": message,
                    "k": 3,
                    "include_live": False  # We'll fetch live data separately
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    context_parts = ["=== Relevant Information from Knowledge Base ==="]
                    for r in results[:3]:
                        context_parts.append(f"- {r['content'][:300]}...")
                    print(f"[RAG] Retrieved {len(results)} relevant documents")
                    return "\n".join(context_parts)
        except Exception as e:
            print(f"[WARN] RAG query failed: {e}")
        
        return ""
    
    def _fetch_live_unit_context(self, message: str) -> dict:
        """Fetch live unit data for any unit codes mentioned in the message"""
        # Extract unit codes from message (e.g., COMP1010, MATH2000)
        unit_codes = re.findall(r'[A-Z]{4}\d{4}', message.upper())
        
        if not unit_codes:
            return {}
        
        live_data = {}
        for code in unit_codes[:3]:  # Max 3 units
            try:
                response = requests.get(
                    f"{PART1_API_URL}/unit/{code}",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    details = data.get("details", {})
                    live_data[code] = {
                        "title": details.get("title", "Unknown"),
                        "prerequisites": details.get("prerequisites", []),
                        "credit_points": details.get("credit_points", 10),
                        "learning_outcomes": details.get("learning_outcomes", [])[:3]
                    }
                    print(f"[LIVE] Fetched data for {code}: {details.get('title')}")
            except Exception as e:
                print(f"[WARN] Failed to fetch {code}: {e}")
        
        return live_data
    
    def _build_prompt(
        self, 
        message: str, 
        messages: List[dict], 
        profile: Optional[dict] = None,
        rag_context: str = "",
        live_unit_context: dict = None,
        memory: ConversationMemory = None
    ) -> str:
        """Build context-aware prompt with student info, RAG context, live unit data, and conversation history"""
        parts = []
        
        # Add live unit context FIRST (most accurate data)
        if live_unit_context:
            parts.append("=== Live Unit Information (Accurate & Current) ===")
            for code, info in live_unit_context.items():
                parts.append(f"Unit: {code} - {info['title']}")
                if info['prerequisites']:
                    parts.append(f"  Prerequisites: {', '.join(info['prerequisites'])}")
                else:
                    parts.append(f"  Prerequisites: None")
                parts.append(f"  Credit Points: {info['credit_points']}")
                if info['learning_outcomes']:
                    parts.append(f"  Key Topics: {'; '.join(info['learning_outcomes'][:2])}")
            parts.append("")
        
        # Add RAG context
        if rag_context:
            parts.append(rag_context)
            parts.append("")
        
        # Add student context
        if profile:
            parts.append("=== Student Profile ===")
            parts.append(f"Name: {profile.get('name', 'Student')}")
            parts.append(f"Degree: {profile.get('degree', 'Unknown')}")
            
            if profile.get('major'):
                parts.append(f"Major: {profile['major']}")
            
            completed = profile.get('completed_units', [])
            if completed:
                parts.append(f"Completed Units: {', '.join(completed)}")
            
            enrolled = profile.get('enrolled_units', [])
            if enrolled:
                parts.append(f"Currently Enrolled: {', '.join(enrolled)}")
            
            parts.append("")
        
        # Add conversation context (previously discussed topics/units)
        if memory:
            context_summary = memory.get_context_summary()
            if context_summary.get("discussed_units"):
                parts.append("=== Previously Discussed Units ===")
                parts.append(f"Units mentioned in this conversation: {', '.join(context_summary['discussed_units'])}")
                parts.append("")
            
            if context_summary.get("discussed_topics"):
                parts.append("=== Topics of Interest ===")
                parts.append(f"Student has asked about: {', '.join(context_summary['discussed_topics'])}")
                parts.append("")
        
        # Add recent conversation history (last 5 exchanges = 10 messages for better context)
        if messages:
            parts.append("=== Recent Conversation ===")
            recent = messages[-10:] if len(messages) > 10 else messages
            for msg in recent:
                role = "Student" if msg["role"] == "student" else "Tutor"
                # Truncate long messages in history
                content = msg['content'][:300] + "..." if len(msg['content']) > 300 else msg['content']
                parts.append(f"{role}: {content}")
            parts.append("")
        
        # Add current question
        parts.append("=== Current Question ===")
        parts.append(f"Student: {message}")
        parts.append("")
        parts.append("Please provide a helpful, accurate response based on the information above. Reference previous discussion if relevant.")
        
        return "\n".join(parts)
    
    def _call_lm_studio(self, prompt: str) -> Optional[str]:
        """Call LM Studio API for response"""
        try:
            print(f"[DEBUG] Calling {self.lm_studio_url}/chat/completions")
            print(f"[DEBUG] Model: {self.model_name}")
            print(f"[DEBUG] Prompt length: {len(prompt)} chars")
            
            response = requests.post(
                f"{self.lm_studio_url}/chat/completions",
                json={
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a helpful and knowledgeable university tutor. "
                                "You help students understand course material, plan their studies, "
                                "and answer questions about their units. "
                                "Use the student's profile and conversation history to provide "
                                "personalized, contextual advice. "
                                "Be encouraging, clear, and educational."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500,
                    "stream": False
                },
                timeout=30
            )
            
            print(f"[DEBUG] LM Studio response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    answer = result["choices"][0]["message"]["content"].strip()
                    print(f"[OK] Got LM Studio response ({len(answer)} chars)")
                    return answer
            
            # Fallback if API call fails
            print(f"[WARN] LM Studio returned status {response.status_code}")
            return None
            
        except Exception as e:
            print(f"[WARN] LM Studio call failed: {e}")
            return None
    
    def _fallback_response(
        self, 
        message: str, 
        profile: Optional[dict] = None,
        live_unit_context: dict = None
    ) -> str:
        """Generate rule-based response when LM Studio unavailable, using live data"""
        message_lower = message.lower()
        
        # If we have live unit data, use it for accurate responses
        if live_unit_context:
            unit_codes = list(live_unit_context.keys())
            if unit_codes:
                parts = []
                for code in unit_codes:
                    info = live_unit_context[code]
                    parts.append(f"**{code} - {info['title']}**")
                    if info['prerequisites']:
                        parts.append(f"Prerequisites: {', '.join(info['prerequisites'])}")
                    else:
                        parts.append("Prerequisites: None (you can enroll directly)")
                    parts.append(f"Credit Points: {info['credit_points']}")
                    if info['learning_outcomes']:
                        parts.append(f"Key Topics: {info['learning_outcomes'][0][:100]}...")
                    parts.append("")
                
                # Add relevant advice based on query type
                if any(word in message_lower for word in ["prerequisite", "prereq", "eligible", "enroll"]):
                    if profile and profile.get('completed_units'):
                        completed = set(profile['completed_units'])
                        for code in unit_codes:
                            prereqs = set(live_unit_context[code]['prerequisites'])
                            missing = prereqs - completed
                            if missing:
                                parts.append(f"To enroll in {code}, you still need: {', '.join(missing)}")
                            else:
                                parts.append(f"You meet all prerequisites for {code}!")
                
                return "\n".join(parts)
        
        # Study plan queries
        if any(word in message_lower for word in ["study", "learn", "prepare", "plan"]):
            return (
                "For effective study, I recommend: "
                "1) Review lecture notes within 24 hours of class. "
                "2) Practice problems regularly, not just before exams. "
                "3) Join study groups to discuss concepts. "
                "4) Use office hours when you're stuck. "
                "5) Start assignments early to allow time for help."
            )
        
        # Prerequisites queries
        if any(word in message_lower for word in ["prerequisite", "prereq", "before", "first"]):
            if profile and profile.get('completed_units'):
                completed = ", ".join(profile['completed_units'])
                return (
                    f"You've completed: {completed}. "
                    "Check the unit handbook for prerequisite requirements. "
                    "Generally, you need to pass all prerequisites before enrolling in advanced units."
                )
            return (
                "Prerequisites are units you must complete before taking another unit. "
                "Check your unit handbook or use the eligibility checker to verify requirements."
            )
        
        # Assignment help
        if any(word in message_lower for word in ["assignment", "homework", "project", "task"]):
            return (
                "For assignment help: "
                "1) Read the specification carefully multiple times. "
                "2) Break it into smaller tasks. "
                "3) Start with what you know. "
                "4) Use consultation hours for specific questions. "
                "5) Don't leave it until the last minute!"
            )
        
        # Concept explanation
        if any(word in message_lower for word in ["explain", "what is", "how does", "understand"]):
            return (
                "I'd be happy to explain! For complex concepts: "
                "1) Start with the basics and build up. "
                "2) Look for examples and practice problems. "
                "3) Try explaining it to someone else. "
                "4) Use multiple resources (textbook, videos, tutorials). "
                "Could you be more specific about what you'd like to understand?"
            )
        
        # Time management
        if any(word in message_lower for word in ["time", "week", "schedule", "manage"]):
            return (
                "Good time management is key! "
                "For a typical unit, allocate 8-10 hours per week: "
                "- 3 hours for lectures/tutorials "
                "- 2-3 hours reviewing notes "
                "- 3-4 hours on assignments and practice. "
                "Use a calendar and set specific study times."
            )
        
        # Difficulty/struggling
        if any(word in message_lower for word in ["difficult", "hard", "struggle", "confused", "help"]):
            return (
                "Don't worry, many students find some topics challenging! "
                "Here's what to do: "
                "1) Identify exactly what you don't understand. "
                "2) Review the basics first. "
                "3) Attend consultation hours or ask in tutorials. "
                "4) Form a study group. "
                "5) Use online resources for different explanations. "
                "What specific topic are you struggling with?"
            )
        
        # General response
        name = profile.get('name', 'there') if profile else 'there'
        return (
            f"Hi {name.split()[0]}! I'm here to help with your studies. "
            "You can ask me about: study strategies, unit content, prerequisites, "
            "time management, or specific topics. What would you like to know?"
        )
    
    def get_conversation_history(self, student_id: str) -> List[dict]:
        """Get conversation history for a student"""
        memory = self.get_or_create_memory(student_id)
        return memory.get_messages()
    
    def get_conversation_context(self, student_id: str) -> dict:
        """Get full conversation context including topics and units discussed"""
        memory = self.get_or_create_memory(student_id)
        return {
            "messages": memory.get_messages(),
            "context_summary": memory.get_context_summary(),
            "student_context": self.student_contexts.get(student_id, {})
        }
    
    def clear_conversation(self, student_id: str):
        """Clear conversation history for a student (keeps profile)"""
        if student_id in self.conversations:
            self.conversations[student_id].clear()
            self._save_conversation(student_id)
    
    def delete_student_data(self, student_id: str):
        """Completely remove student data including files"""
        if student_id in self.conversations:
            del self.conversations[student_id]
        
        if student_id in self.student_contexts:
            del self.student_contexts[student_id]
        
        # Delete persistence file
        try:
            file_path = PERSISTENCE_DIR / f"{student_id}.json"
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"[WARN] Failed to delete file for {student_id}: {e}")
    
    def get_statistics(self) -> dict:
        """Get detailed statistics about conversations"""
        all_discussed_units = set()
        all_discussed_topics = set()
        
        for mem in self.conversations.values():
            all_discussed_units.update(mem.discussed_units)
            all_discussed_topics.update(mem.discussed_topics)
        
        return {
            "total_students": len(self.conversations),
            "total_messages": sum(
                len(mem.get_messages())
                for mem in self.conversations.values()
            ),
            "students_with_context": len(self.student_contexts),
            "all_discussed_units": list(all_discussed_units),
            "all_discussed_topics": list(all_discussed_topics),
            "persistence_enabled": True,
            "persistence_dir": str(PERSISTENCE_DIR)
        }
