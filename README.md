# Gauss Code

Gauss Code is an AI-powered coding assistant that lives in your terminal, understands your codebase, and helps you code faster by executing routine tasks, explaining complex code.

## Features

- 🤖 **AI-Powered**: Built with DeepSeek API for intelligent code assistance
- 💬 **Session Management**: Create, load, and manage multiple conversation sessions
- 🛠️ **Tool Support**: Execute bash commands and extend with custom tools
- 📝 **Streaming Output**: Real-time response streaming for better user experience
- 💾 **Persistent Storage**: Sessions saved to `~/.gauss-code/sessions`

## Installation

1. Ensure Python 3.11+ is installed on your system
2. Clone this repository
3. Navigate to the project directory
4. Install dependencies:

```bash
uv sync
```

5. Configure environment variables:

```bash
cp .env.example .env
# Edit .env and add your LLM API key
```

Available environment variables:
- `LLM_API_KEY`: LLM API 密钥（必需）
- `LLM_BASE_URL`: LLM API 基础 URL（可选，默认为 DeepSeek）
- `LLM_MODEL`: 使用的模型名称（可选，默认为 deepseek-chat）

## Usage

### Start the Agent

```bash
python src/main.py
```

### Session Commands

- `/new` - Create a new session
- `/sessions` - List all sessions
- `/load <id>` - Load a specific session
- `/delete <id>` - Delete a session
- `exit` - Quit the program

### Example Session

```
[2026-03-18-1] You: List all files in current directory
[2026-03-18-1] GaussAgent: [executes bash command and displays results]
```

## Project Structure

```
gauss-code/
├── src/
│   ├── __init__.py
│   ├── agent.py       # Agent core logic and command handling
│   ├── session.py     # Session management and storage
│   └── main.py       # Main entry point
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── .env.example      # Environment variables template
├── .gitignore
├── AGENTS.md         # Technical stack documentation
├── pyproject.toml    # Project configuration
└── README.md         # This file
```

## Session Storage

Sessions are automatically saved to `~/.gauss-code/sessions` in JSON format with the naming convention `YYYY-MM-DD-N.json`. This works on both Linux and Windows systems.

## Development

### Running Tests

```bash
python -m pytest
```

### Adding New Tools

To add a new tool, register it in `main.py`:

```python
from agent import Tool

def my_tool(param: str) -> str:
    return f"Result: {param}"

my_tool_obj = Tool(
    name="my_tool",
    description="Description of what the tool does",
    function=my_tool
)

agent.register_tool(my_tool_obj)
```

## Reference

- [Claude Code](https://github.com/anthropics/claude-code)
- [Qwen Code](https://github.com/QwenLM/qwen-code)
