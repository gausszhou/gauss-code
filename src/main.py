import subprocess
import os
from agent import SimpleAgent, Tool


def bash_tool(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        
        return output if output else f"Command executed successfully (exit code: {result.returncode})"
    
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def main():
    try:
        agent = SimpleAgent("GaussAgent", model="deepseek-chat")
        
        bash_tool_obj = Tool(
            name="bash",
            description="Execute bash commands in shell. Use this to run terminal commands and get their output.",
            function=bash_tool
        )
        
        agent.register_tool(bash_tool_obj)
        
        print(f"🤖 {agent.name} is ready!")
        print(f"Model: {agent.model}")
        print(f"Available tools: {', '.join(agent.tools.keys())}")
        print("\n💡 Commands:")
        print("  /new       - Create a new session")
        print("  /sessions  - List all sessions")
        print("  /load <id> - Load a specific session")
        print("  /delete <id> - Delete a session")
        print("  exit       - Quit the program")
        print()
        
        while True:
            try:
                session_info = ""
                if agent.session_manager.current_session:
                    session_info = f"[{agent.session_manager.current_session.id}] "
                
                user_input = input(f"{session_info}You: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print(f"{session_info}{agent.name}: Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                if agent.handle_command(user_input):
                    continue
                
                if not agent.session_manager.current_session:
                    print(f"{session_info}{agent.name}: No active session. Use '/new' to create one or '/sessions' to load an existing one.")
                    continue
                
                print(f"{session_info}{agent.name}: ", end="", flush=True)
                
                full_response = ""
                for chunk in agent.generate_response_stream(user_input):
                    print(chunk, end="", flush=True)
                    full_response += chunk
                
                print()
                print()
                
            except KeyboardInterrupt:
                print(f"\n{session_info}{agent.name}: Goodbye!")
                break
            except Exception as e:
                print(f"\n{session_info}{agent.name}: Error occurred: {str(e)}\n")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
