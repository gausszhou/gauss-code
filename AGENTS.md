# Gauss Code - 技术栈

## 包管理器
- **uv** - 现代化的 Python 包管理器

## 环境变量配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

- `LLM_API_KEY`: LLM API 密钥（必需）
- `LLM_BASE_URL`: LLM API 基础 URL（可选，默认为 DeepSeek）
- `LLM_MODEL`: 使用的模型名称（可选，默认为 deepseek-chat）
