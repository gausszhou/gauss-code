import os
import json
import tempfile
import shutil
from datetime import datetime
from session import SessionManager, Session, Message


def test_message_creation():
    message = Message(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == "Hello"
    assert message.timestamp != ""
    assert isinstance(message.timestamp, str)


def test_session_creation():
    session = Session(
        id="2026-03-18-1",
        name="Test Session",
        created_at="2026-03-18T10:00:00",
        messages=[]
    )
    assert session.id == "2026-03-18-1"
    assert session.name == "Test Session"
    assert session.messages == []
    assert session.updated_at != ""


def test_session_to_dict():
    session = Session(
        id="2026-03-18-1",
        name="Test Session",
        created_at="2026-03-18T10:00:00",
        messages=[
            Message(role="user", content="Hello")
        ]
    )
    session_dict = session.to_dict()
    assert session_dict["id"] == "2026-03-18-1"
    assert session_dict["name"] == "Test Session"
    assert len(session_dict["messages"]) == 1
    assert session_dict["messages"][0]["role"] == "user"


def test_session_manager_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = os.path.join(tmpdir, "sessions")
        manager = SessionManager(sessions_dir)
        assert manager.sessions_dir == sessions_dir
        assert os.path.exists(sessions_dir)
        assert manager.current_session is None


def test_session_manager_create_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = os.path.join(tmpdir, "sessions")
        manager = SessionManager(sessions_dir)
        
        session = manager.create_session("Test Session")
        
        assert session.id.startswith(datetime.now().strftime("%Y-%m-%d"))
        assert session.name == "Test Session"
        assert session.messages == []
        assert session.created_at != ""
        
        file_path = os.path.join(sessions_dir, f"{session.id}.json")
        assert os.path.exists(file_path)


def test_session_manager_save_and_load_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = os.path.join(tmpdir, "sessions")
        manager = SessionManager(sessions_dir)
        
        session = manager.create_session("Test Session")
        session.messages.append(Message(role="user", content="Hello"))
        session.messages.append(Message(role="assistant", content="Hi there!"))
        
        manager.save_session(session)
        
        loaded_session = manager.load_session(session.id)
        
        assert loaded_session is not None
        assert loaded_session.id == session.id
        assert loaded_session.name == session.name
        assert len(loaded_session.messages) == 2
        assert loaded_session.messages[0].content == "Hello"
        assert loaded_session.messages[1].content == "Hi there!"


def test_session_manager_list_sessions():
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = os.path.join(tmpdir, "sessions")
        manager = SessionManager(sessions_dir)
        
        session1 = manager.create_session("Session 1")
        session2 = manager.create_session("Session 2")
        
        sessions = manager.list_sessions()
        
        assert len(sessions) == 2
        assert sessions[0]["id"] == session2.id
        assert sessions[1]["id"] == session1.id


def test_session_manager_delete_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = os.path.join(tmpdir, "sessions")
        manager = SessionManager(sessions_dir)
        
        session = manager.create_session("Test Session")
        file_path = os.path.join(sessions_dir, f"{session.id}.json")
        assert os.path.exists(file_path)
        
        result = manager.delete_session(session.id)
        assert result is True
        assert not os.path.exists(file_path)
        
        result = manager.delete_session(session.id)
        assert result is False


def test_session_manager_set_current_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = os.path.join(tmpdir, "sessions")
        manager = SessionManager(sessions_dir)
        
        session = manager.create_session("Test Session")
        manager.set_current_session(session)
        
        assert manager.current_session == session


def test_session_manager_add_message_to_current_session():
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = os.path.join(tmpdir, "sessions")
        manager = SessionManager(sessions_dir)
        
        session = manager.create_session("Test Session")
        manager.set_current_session(session)
        
        manager.add_message_to_current_session("user", "Hello")
        manager.add_message_to_current_session("assistant", "Hi!")
        
        assert len(session.messages) == 2
        assert session.messages[0].content == "Hello"
        assert session.messages[1].content == "Hi!"
        
        loaded_session = manager.load_session(session.id)
        assert len(loaded_session.messages) == 2


def test_session_manager_generate_session_id():
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = os.path.join(tmpdir, "sessions")
        manager = SessionManager(sessions_dir)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        session_id_1 = manager._generate_session_id()
        assert session_id_1 == f"{today}-1"
        
        manager.create_session("Session 1")
        
        session_id_2 = manager._generate_session_id()
        assert session_id_2 == f"{today}-2"


def test_session_manager_default_directory():
    manager = SessionManager()
    home_dir = os.path.expanduser("~")
    expected_dir = os.path.join(home_dir, ".gauss-code", "sessions")
    assert manager.sessions_dir == expected_dir
