<div align="center">
  <h1>🤖 AutoToolDPO</h1>
  <p><em>Enterprise-grade automatic builder for Agent tool-calling DPO datasets</em></p>
  <p>Automatically generates high-quality tool-calling training data, ready for LLaMA-Factory DPO fine-tuning</p>
  <span>English | <a href="./README_zh.md">中文</a></span>
</div>

## ⚡ Overview

AutoToolDPO is an automated system for generating Agent tool-calling DPO datasets. By using LLMs to automatically create pairs of chosen (correct calls) and rejected (incorrect calls), it compresses weeks of manual labeling into just hours.

### Key Features

- 🎯 **Automated synthesis**: Provide tool definitions and automatically generate DPO training data
- 🚀 **High concurrency**: Asynchronous processing with configurable concurrency of 10–50
- 📊 **Real-time monitoring**: WebSocket-based real-time progress and stats
- 🎨 **Web console**: Modern frontend dashboard, one-click generation
- 🔧 **Highly configurable**: Supports single-turn/multi-turn, tool count, and quality controls
- 🔌 **Multi-model support**: Compatible with DeepSeek, Qwen, GPT and other OpenAI API providers

### Data Format

Generated data follows the LLaMA-Factory DPO training format:

```jsonl
{
  "system": "You are an intelligent AI assistant...",
  "tools": "[{\"name\":\"get_weather@v1\",...}]",
  "messages": [{"role":"user","content":"What's the weather in Beijing?"}],
  "chosen": "<function_call>{\"name\":\"get_weather@v1\",\"arguments\":{\"city\":\"Beijing\"}}</function_call>",
  "rejected": "<function_call>{\"name\":\"get_time@v1\",...}</function_call>"
}
```

## 🚀 Getting Started

### Requirements

- Python 3.12+
- Node.js 18+
- API Key (DeepSeek / Qwen / OpenAI)

### One-Click Start

**Linux/macOS**:

```bash
cd AutoToolDPO
chmod +x scripts/*.sh
./scripts/setup.sh        # First run: install dependencies
./scripts/start_all.sh    # Start backend and frontend (background)
```

**Windows**:

```bash
cd AutoToolDPO
scripts\setup.bat          # First run: install dependencies
scripts\start_all.bat      # Start backend and frontend
```

After services start, visit:
- 🌐 **Frontend**: http://localhost:3000
- 📚 **API Docs**: http://localhost:8000/docs

## 🏗️ Project Structure

```
AutoToolDPO/
├── backend/                    # Python backend engine
│   ├── configs/                # Configuration files (tool definitions)
│   ├── core/
│   │   ├── concurrent_engine.py    # Concurrency engine
│   │   ├── data_synthesizer.py     # Data synthesizer
│   │   ├── exporter.py             # Data exporter
│   │   ├── task_generator.py       # Task generator
│   │   └── validator.py            # Data validator
│   ├── api/                    # FastAPI server
│   ├── services/               # LLM clients and task management
│   └── main.py                 # CLI entry
├── frontend/                   # React frontend console
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── hooks/              # Custom hooks
│   │   └── App.tsx             # Main app
├── data/                       # Data output directory
├── logs/                       # Logs directory
└── scripts/                    # Startup scripts
```

## 🤝 Contributing

Issues and Pull Requests are welcome to improve the project (feature enhancements, bug fixes, docs, etc.).

## 😎 Community

Explore our tech community 👉 [Large-Model Tech Community | Fufan Space](https://kq4b3vgg5b.feishu.cn/wiki/JuJSwfbwmiwvbqkiQ7LcN1N1nhd)

Scan to join the group and discuss with other members.
<div align="center">
<img src="assets/交流群.jpg" width="200" alt="Community QR code">
<div>