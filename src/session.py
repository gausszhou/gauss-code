import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Message:
    role: str
    content: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class Session:
    id: str
    name: str
    created_at: str
    messages: List[Message]
    updated_at: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SessionManager:
    def __init__(self, sessions_dir: str = None):
        if sessions_dir is None:
            home_dir = os.path.expanduser("~")
            sessions_dir = os.path.join(home_dir, ".gauss-code", "sessions")
        
        self.sessions_dir = sessions_dir
        self.current_session: Optional[Session] = None
        self._ensure_sessions_dir()

    def _ensure_sessions_dir(self):
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)

    def _get_session_file_path(self, session_id: str) -> str:
        return os.path.join(self.sessions_dir, f"{session_id}.json")

    def _generate_session_id(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        existing_sessions = self.list_sessions()
        
        counter = 1
        while True:
            session_id = f"{today}-{counter}"
            if not any(s["id"] == session_id for s in existing_sessions):
                break
            counter += 1
        
        return session_id

    def create_session(self, name: str = "") -> Session:
        session_id = self._generate_session_id()
        session = Session(
            id=session_id,
            name=name or f"Session {session_id}",
            created_at=datetime.now().isoformat(),
            messages=[]
        )
        self.save_session(session)
        return session

    def load_session(self, session_id: str) -> Optional[Session]:
        file_path = self._get_session_file_path(session_id)
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = [Message(**msg) for msg in data.get("messages", [])]
        return Session(
            id=data["id"],
            name=data["name"],
            created_at=data["created_at"],
            messages=messages,
            updated_at=data.get("updated_at", data["created_at"])
        )

    def save_session(self, session: Session):
        session.updated_at = datetime.now().isoformat()
        file_path = self._get_session_file_path(session.id)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def list_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        if not os.path.exists(self.sessions_dir):
            return sessions
        
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.sessions_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append({
                        "id": data["id"],
                        "name": data["name"],
                        "created_at": data["created_at"],
                        "updated_at": data.get("updated_at", data["created_at"]),
                        "message_count": len(data.get("messages", []))
                    })
        
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        file_path = self._get_session_file_path(session_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def set_current_session(self, session: Session):
        self.current_session = session

    def add_message_to_current_session(self, role: str, content: str):
        if self.current_session:
            message = Message(role=role, content=content)
            self.current_session.messages.append(message)
            self.save_session(self.current_session)
