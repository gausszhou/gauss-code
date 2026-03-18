import subprocess
import json
import os
import sys
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass, field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Tool:
    name: str
    description: str
    function: callable


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ToolCall:
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None


class SimpleAgent:
    def __init__(self, name: str = "SimpleAgent", model: str = "deepseek-chat"):
        self.name = name
        self.model = model
        self.messages: List[Message] = []
        self.tools: Dict[str, Tool] = {}
        self.max_iterations = 10
        
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def add_message(self, role: str, content: str):
        self.messages.append(Message(role=role, content=content))

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "The command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
            for tool in self.tools.values()
        ]

    def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found"
        
        try:
            result = self.tools[tool_name].function(**arguments)
            return str(result)
        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def generate_response_stream(self, user_input: str) -> Generator[str, None, None]:
        self.add_message("user", user_input)
        
        messages_for_api = [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages_for_api,
                tools=self.get_openai_tools(),
                tool_choice="auto",
                stream=True
            )
            
            full_content = ""
            tool_calls_buffer = {}
            
            for chunk in stream:
                delta = chunk.choices[0].delta
                
                if delta.content:
                    content = delta.content
                    full_content += content
                    yield content
                
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        call_id = tool_call.id
                        if call_id not in tool_calls_buffer:
                            tool_calls_buffer[call_id] = {
                                "id": call_id,
                                "type": tool_call.type,
                                "function": {
                                    "name": tool_call.function.name if tool_call.function.name else "",
                                    "arguments": tool_call.function.arguments if tool_call.function.arguments else ""
                                }
                            }
                        else:
                            if tool_call.function.name:
                                tool_calls_buffer[call_id]["function"]["name"] = tool_call.function.name
                            if tool_call.function.arguments:
                                tool_calls_buffer[call_id]["function"]["arguments"] += tool_call.function.arguments
            
            if tool_calls_buffer:
                tool_calls_list = list(tool_calls_buffer.values())
                tool_results = []
                
                for tool_call_data in tool_calls_list:
                    tool_name = tool_call_data["function"]["name"]
                    try:
                        arguments = json.loads(tool_call_data["function"]["arguments"])
                    except json.JSONDecodeError:
                        arguments = {"command": tool_call_data["function"]["arguments"]}
                    
                    result = self.execute_tool_call(tool_name, arguments)
                    tool_results.append({
                        "tool_call_id": tool_call_data["id"],
                        "role": "tool",
                        "name": tool_name,
                        "content": result
                    })
                    
                    self.add_message("system", f"Tool '{tool_name}' executed. Result: {result}")
                
                messages_for_api.append({
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": tool_calls_list
                })
                
                messages_for_api.extend(tool_results)
                continue
            
            if full_content:
                self.add_message("assistant", full_content)
                return
            
            break

    def generate_response(self, user_input: str) -> str:
        full_response = ""
        for chunk in self.generate_response_stream(user_input):
            full_response += chunk
        return full_response

    def run(self):
        print(f"🤖 {self.name} is ready!")
        print(f"Model: {self.model}")
        print(f"Available tools: {', '.join(self.tools.keys())}")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print(f"{self.name}: Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print(f"{self.name}: ", end="", flush=True)
                
                full_response = ""
                for chunk in self.generate_response_stream(user_input):
                    print(chunk, end="", flush=True)
                    full_response += chunk
                
                print()
                print()
                
            except KeyboardInterrupt:
                print(f"\n{self.name}: Goodbye!")
                break
            except Exception as e:
                print(f"\n{self.name}: Error occurred: {str(e)}\n")


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
            description="Execute bash commands in the shell. Use this to run terminal commands and get their output.",
            function=bash_tool
        )
        
        agent.register_tool(bash_tool_obj)
        
        agent.run()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please make sure DEEPSEEK_API_KEY is set in your .env file")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
