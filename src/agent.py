import os
import time
from typing import Generator, Dict
from openai import OpenAI
from dotenv import load_dotenv
from session import SessionManager
from stream_buffer import StreamBuffer

load_dotenv()


def estimate_tokens(text: str) -> int:
    tokens = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符
            tokens += 0.6
        else:  # 其他字符（数字、符号等）
            tokens += 0.3
    return int(tokens)


class SimpleAgent:
    def __init__(self, name: str = "SimpleAgent", model: str = None):
        self.name = name
        self.model = os.getenv("LLM_MODEL", "deepseek-chat")
        self.session_manager = SessionManager()
        self._stop_generation = False
        self._last_generation_time: float = 0.0
        self._last_completion_tokens: int = 0
        self._last_first_token_time: float = 0.0
        self._stream_buffer = StreamBuffer(mode="char")
        
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        print(f"LLM_MODEL: {self.model}")
        print(f"LLM_BASE_URL: {base_url}")
        if not api_key:
            raise ValueError("LLM_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def stop_generation(self):
        self._stop_generation = True
        self._stream_buffer.stop()

    def reset_stop_flag(self):
        self._stop_generation = False
        self._stream_buffer.reset()

    def add_message(self, role: str, content: str):
        self.session_manager.add_message_to_current_session(role, content)

    def generate_response_stream(self, user_input: str) -> Generator[str, None, None]:
        self.add_message("user", user_input)
        
        messages_for_api = [
            {"role": msg.role, "content": msg.content}
            for msg in self.session_manager.current_session.messages
        ]
        
        if self._stop_generation:
            yield "\n\n[Generation stopped by user]"
            self.reset_stop_flag()
            return
        
        start_time = time.time()
        completion_tokens = 0
        first_token_received = False
        first_token_time = 0.0
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages_for_api,
                stream=True
            )
        except Exception as e:
            error_msg = f"Error creating completion: {str(e)}"
            self.add_message("system", error_msg)
            yield f"\n[Error: {error_msg}]"
            return
        
        full_content = ""
        
        try:
            for chunk in stream:
                if self._stop_generation:
                    yield "\n\n[Generation stopped by user]"
                    self.reset_stop_flag()
                    return
                
                if not chunk or not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                if delta is None:
                    continue
                
                if delta.content:
                    content = delta.content
                    if content:
                        if not first_token_received:
                            first_token_received = True
                            first_token_time = time.time()
                        
                        full_content += content
                        completion_tokens += estimate_tokens(content)
                        
                        for char in self._stream_buffer.process(content):
                            yield char
        except Exception as e:
            error_msg = f"Error processing stream: {str(e)}"
            self.add_message("system", error_msg)
            yield f"\n[Error: {error_msg}]"
            return
        
        for char in self._stream_buffer.flush():
            yield char
        
        end_time = time.time()
        self._last_generation_time = end_time - start_time
        self._last_completion_tokens = completion_tokens
        self._last_first_token_time = first_token_time - start_time if first_token_received else 0.0
        
        if full_content:
            self.add_message("assistant", full_content)

    def generate_response(self, user_input: str) -> str:
        full_response = ""
        for chunk in self.generate_response_stream(user_input):
            full_response += chunk
        return full_response

    def get_usage_stats(self) -> Dict[str, any]:
        if self._last_generation_time == 0:
            return {}
        
        completion_tokens = self._last_completion_tokens
        first_token_time = self._last_first_token_time
        actual_generation_time = self._last_generation_time - first_token_time if self._last_generation_time > first_token_time else self._last_generation_time
        tokens_per_second = completion_tokens / actual_generation_time if actual_generation_time > 0 else 0
        
        return {
            'completion_tokens': completion_tokens,
            'first_token_time': round(first_token_time, 2),
            'generation_time': round(self._last_generation_time, 2),
            'actual_generation_time': round(actual_generation_time, 2),
            'tokens_per_second': round(tokens_per_second, 2)
        }

    def handle_command(self, user_input: str) -> bool:
        if user_input.startswith("/"):
            command = user_input[1:].strip().lower()
            
            if command == "new":
                session = self.session_manager.create_session()
                self.session_manager.set_current_session(session)
                print(f"✅ Created new session: {session.id} - {session.name}")
                return True
            
            elif command == "sessions":
                sessions = self.session_manager.list_sessions()
                if not sessions:
                    print("📋 No sessions found")
                else:
                    print("📋 Available sessions:")
                    for i, session in enumerate(sessions, 1):
                        current_marker = "👉 " if self.session_manager.current_session and session["id"] == self.session_manager.current_session.id else "   "
                        print(f"{current_marker}{i}. {session['id']} - {session['name']}")
                        print(f"      Messages: {session['message_count']}, Updated: {session['updated_at'][:19]}")
                return True
            
            elif command.startswith("load "):
                session_id = command[5:].strip()
                session = self.session_manager.load_session(session_id)
                if session:
                    self.session_manager.set_current_session(session)
                    print(f"✅ Loaded session: {session.id} - {session.name}")
                else:
                    print(f"❌ Session not found: {session_id}")
                return True
            
            elif command.startswith("delete "):
                session_id = command[7:].strip()
                if self.session_manager.delete_session(session_id):
                    print(f"✅ Deleted session: {session_id}")
                    if self.session_manager.current_session and self.session_manager.current_session.id == session_id:
                        self.session_manager.current_session = None
                else:
                    print(f"❌ Session not found: {session_id}")
                return True
            
            else:
                print(f"❓ Unknown command: /{command}")
                print("Available commands: /new, /sessions, /load <id>, /delete <id>")
                return True
        
        return False
