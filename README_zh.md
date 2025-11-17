<div align="center">
  <h1>🤖 AutoToolDPO</h1>
  <p><em>企业级 Agent 工具调用 DPO 数据集自动构建系统</em></p>
  <p>自动生成高质量的工具调用训练数据，支持 LLaMA-Factory DPO 微调</p>
  <span>中文 | <a href="./README.md">English</a></span>
</div>

## ⚡ 项目简介

AutoToolDPO 是一个**自动化生成 Agent 工具调用 DPO 数据集**的系统。通过 LLM 自动生成 chosen（正确调用）和 rejected（错误调用）对比数据，将数周的人工标注工作缩短到几小时。


https://github.com/user-attachments/assets/90078b8c-c9ba-47e5-bb8a-7d824caddf3c


### 核心特性

- 🎯 **自动化生成**：输入工具定义，自动生成 DPO 训练数据
- 🚀 **高效并发**：异步并发处理，支持并发
- 📊 **实时监控**：WebSocket 实时显示生成进度和统计
- 🎨 **Web 界面**：现代化的前端控制台，一键生成
- 🔧 **高度可配置**：支持单轮/多轮对话、工具数量、质量控制
- 🔌 **多模型支持**：兼容 DeepSeek、Qwen、GPT 等 OpenAI API

### 数据格式

生成的数据符合 LLaMA-Factory DPO 训练格式：

```jsonl
{
  "system": "你是一个智能AI助手...",
  "tools": "[{\"name\":\"get_weather@v1\",...}]",
  "messages": [{"role":"user","content":"北京天气如何？"}],
  "chosen": "<function_call>{\"name\":\"get_weather@v1\",\"arguments\":{\"city\":\"北京\"}}</function_call>",
  "rejected": "<function_call>{\"name\":\"get_time@v1\",...}</function_call>"
}
```




## 🚀 使用指南

### 环境要求

- Python 3.12+
- Node.js 18+
- API Key（DeepSeek / Qwen / OpenAI）

### 一键启动

**Linux/macOS 系统**：

```bash
cd AutoToolDPO
chmod +x scripts/*.sh
./scripts/setup.sh        # 首次运行，安装依赖
./scripts/start_all.sh    # 一键启动前后端（后台运行）
```

**Windows 系统**：

```bash
cd AutoToolDPO
scripts\setup.bat          # 首次运行，安装依赖
scripts\start_all.bat      # 一键启动前后端
```

服务启动后访问：
- 🌐 **前端界面**：http://localhost:3000
- 📚 **API 文档**：http://localhost:8000/docs



## 🏗️ 项目结构

```
AutoToolDPO/
├── backend/                    # Python 后端引擎
│   ├── configs/               # 配置文件（工具定义）
│   ├── core/           
│   │   ├── concurrent_engine.py    # 并发引擎
│   │   ├── data_synthesizer.py     # 数据合成器
│   │   ├── exporter.py            # 数据导出器
│   │   ├── task_generator.py      # 任务生成器
│   │   └── validator.py           # 数据验证器
│   ├── api/                   # FastAPI 服务器
│   ├── services/              # LLM 客户端、任务管理
│   └── main.py                # 命令行入口
├── frontend/                   # React 前端控制台
│   ├── src/
│   │   ├── components/        # UI 组件
│   │   ├── hooks/             # 自定义 Hooks
│   │   └── App.tsx            # 主应用
├── data/                       # 数据输出目录
├── logs/                       # 日志目录
└── scripts/                    # 启动脚本
└── QUICK_START.md              # 快速开始指南
└── ARCHITECTURE.md             # 完整架构文档
```

## 🤝 贡献

欢迎提交 Issue 与 Pull Request 帮助改进项目（功能增强、Bug 修复、文档优化等）。

## 😎 技术交流
探索我们的技术社区 👉 [大模型技术社区丨赋范空间](https://kq4b3vgg5b.feishu.cn/wiki/JuJSwfbwmiwvbqkiQ7LcN1N1nhd)

扫描添加小可爱，加入技术交流群，与其他小伙伴一起交流学习。
<div align="center">
<img src="assets\交流群.jpg" width="200" alt="技术交流群二维码">
<div>
