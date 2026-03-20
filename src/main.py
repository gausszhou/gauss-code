from agent import SimpleAgent


def main():
    try:
        agent = SimpleAgent("Agent", model="deepseek-chat")
        
        print(f"🤖 {agent.name} is ready!")
        print(f"Model: {agent.model}")
        print("\n💡 Commands:")
        print("  /new       - Create a new session")
        print("  /sessions  - List all sessions")
        print("  /load <id> - Load a specific session")
        print("  /delete <id> - Delete a session")
        print("  exit       - Quit the program")
        print("\n💡 Press Ctrl+C to interrupt generation")
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
                try:
                    for chunk in agent.generate_response_stream(user_input):
                        print(chunk, end="", flush=True)
                        full_response += chunk
                except KeyboardInterrupt:
                    agent.stop_generation()
                    print("\n\n[Generation interrupted]")
                    print()
                    continue
                
                stats = agent.get_usage_stats()
                if stats:
                    print(f"\n\n📊 Tokens: {stats['completion_tokens']} | First Token: {stats['first_token_time']}s | Speed: {stats['tokens_per_second']} tokens/s | Time: {stats['generation_time']}s")
                
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
