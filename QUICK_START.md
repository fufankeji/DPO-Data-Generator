# 🚀 AutoToolDPO 快速开始指南

## 📁 项目结构概览

```
AutoToolDPO/
├── backend/                    # Python后端引擎
│   ├── configs/               # 配置文件（工具定义）
│   ├── core/                  # 7大核心模块
│   ├── api/                   # FastAPI服务器
│   └── main.py                # 命令行入口
├── frontend/                   # React前端控制台
│   ├── src/
│   │   ├── api/               # API客户端
│   │   ├── components/        # UI组件
│   │   └── hooks/             # 自定义Hooks
│   └── vite.config.ts
├── data/                       # 数据输出目录
├── logs/                       # 日志目录
└── scripts/                    # 启动脚本
```

---

## ⚡ 快速启动

### 方式1: 一键启动（推荐）

```bash
cd AutoToolDPO
chmod +x scripts/*.sh
./scripts/setup.sh        # 首次运行需要安装依赖
./scripts/start_all.sh    # 一键启动前后端（后台运行）
```

服务会在后台运行，访问：
- 前端界面：http://localhost:3000
- API文档：http://localhost:8000/docs

### 方式2: 分别启动

**终端1 - 启动后端：**
```bash
./scripts/start_backend.sh
```

**终端2 - 启动前端：**
```bash
./scripts/start_frontend.sh
```

### 🛑 停止服务

```bash
# 停止所有服务
./scripts/stop_all.sh

# 或分别停止
./scripts/stop_backend.sh   # 只停止后端
./scripts/stop_frontend.sh  # 只停止前端
```

### 📋 查看日志

```bash
# 查看后端日志
tail -f logs/backend.log

# 查看前端日志
tail -f logs/frontend.log
```

---

## 🎮 使用Web界面

### 配置参数

1. **数据生成参数**
   - **样本数量**：1000（建议范围：100-100000）
   - **并发级别**：10（建议范围：5-50）
   - **多轮对话比例**：30%（0-100%滑块调整）
   - **工具数配置**：单值模式=4 或 范围模式=2-5

2. **模型配置**
   - 点击**模型预设**按钮快速选择：
     - ✅ **DeepSeek Chat**（推荐，性价比高）
     - ✅ **Qwen Turbo/Plus/Max**（阿里通义千问）
     - GPT-4 Turbo / GPT-3.5
   - 或手动输入模型名称和API地址
   - 输入**API Key**

3. **路径配置**
   - **工具列表路径**：`configs/tools_registry.json`（相对于backend目录）
   - 点击右侧蓝色 **预览** 按钮查看工具配置内容
   - **输出目录**：`data/processed`
   - ⚠️ **路径说明**：使用相对路径时，相对于 `backend/` 目录
     - ✅ 正确：`configs/tools_registry.json`
     - ❌ 错误：`backend/configs/tools_registry.json`
   - 💡 详细路径说明请查看 [PATH_GUIDE.md](PATH_GUIDE.md)

### 开始生成

1. 点击**开始生成**按钮
2. 实时查看：
   - 📊 生成进度（进度条）
   - 📈 生成速率（样本/秒）
   - 📉 对话类型分布（单轮/多轮）
   - ✅ 验证成功率
   - 📝 实时日志
3. 完成后点击**下载数据集（JSONL）**

---

## 💻 使用命令行（可选）

### 基础用法

```bash
cd AutoToolDPO
python backend/main.py \
  --num_samples 1000 \
  --multi_ratio 0.3 \
  --tool_count 4 \
  --concurrency 20 \
  --base_model deepseek-chat \
  --model_api_url https://api.deepseek.com \
  --api_key YOUR_API_KEY \
  --output_dir data/processed
```

### 高级用法

```bash
# 使用工具数范围模式
python backend/main.py \
  --num_samples 5000 \
  --multi_ratio 0.25 \
  --tool_count_mode range \
  --tool_count_min 2 \
  --tool_count_max 5 \
  --concurrency 30 \
  --base_model qwen-plus \
  --model_api_url https://dashscope.aliyuncs.com/compatible-mode/v1 \
  --api_key YOUR_QWEN_API_KEY
```

### 查看帮助

```bash
python backend/main.py --help
```

---

## 🔧 配置工具库

### 编辑工具定义

编辑 `backend/configs/tools_registry.json`：

```json
{
  "tools": [
    {
      "name": "get_weather",
      "version": "v1",
      "description": "查询城市天气",
      "category": "weather",
      "parameters": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "城市名称"
          }
        },
        "required": ["city"]
      }
    }
  ]
}
```

### 在Web界面预览

1. 确保路径为 `configs/tools_registry.json`
2. 点击工具列表路径旁的 **👁️** 按钮
3. 弹窗显示完整JSON配置

---

## 📦 输出数据

### 文件位置

- 主数据：`data/processed/data_dpo.jsonl`（或分片文件）
- 元信息：`data/processed/dataset_info.json`
- 统计：`data/processed/generation_stats.json`
- 无效样本：`data/processed/invalid_samples.jsonl`（调试用）

### 数据格式（LLaMA-Factory兼容）

```jsonl
{
  "system": "你是一个智能AI助手...",
  "tools": "[{\"name\":\"get_weather@v1\",...}]",
  "messages": [{"role":"user","content":"北京天气如何？"}],
  "chosen": "<function_call>{\"name\":\"get_weather@v1\",\"arguments\":{\"city\":\"北京\"}}</function_call>",
  "rejected": "<function_call>{\"name\":\"get_time@v1\",...}</function_call>"
}
```

---

## 🎯 推荐配置

### 快速测试（100样本）

- 样本数量：100
- 并发：10
- 模型：deepseek-chat
- 预计时间：~1分钟

### 小规模生产（1000样本）

- 样本数量：1000
- 并发：20
- 多轮比例：30%
- 工具数：3-5
- 模型：qwen-turbo / deepseek-chat
- 预计时间：~3-5分钟

### 大规模生产（10000样本）

- 样本数量：10000
- 并发：30-50
- 多轮比例：25%
- 工具数范围：2-6
- 模型：qwen-plus / deepseek-chat
- 预计时间：~30-45分钟

---

## 🔑 获取API密钥

### DeepSeek（推荐）

1. 访问：https://platform.deepseek.com/
2. 注册并充值（新用户送免费额度）
3. 创建API Key
4. 在Web界面选择"DeepSeek Chat"预设
5. 粘贴API Key

### 通义千问（Qwen）

1. 访问：https://dashscope.console.aliyun.com/
2. 开通服务（新用户有免费额度）
3. 创建API Key
4. 在Web界面选择"Qwen Turbo/Plus/Max"预设
5. 粘贴API Key

### OpenAI

1. 访问：https://platform.openai.com/
2. 创建API Key
3. 在Web界面选择"GPT-4 Turbo"或"GPT-3.5"预设
4. 粘贴API Key

---

## ❓ 常见问题

### Q: 前端无法连接后端？

A: 确保：
1. 后端已启动（`./scripts/start_backend.sh`）
2. 端口8000未被占用
3. 检查浏览器控制台错误

### Q: 生成速度很慢？

A:
1. 提高并发数（建议10-30）
2. 选择更快的模型（deepseek-chat / qwen-turbo）
3. 检查网络连接和API限流

### Q: 数据质量不理想？

A:
1. 使用更强的模型（qwen-plus / gpt-4）
2. 调整工具定义，使其更清晰
3. 检查生成的invalid_samples.jsonl找问题

### Q: 如何修改默认工具？

A: 编辑 `backend/configs/tools_registry.json`，然后在Web界面点击预览按钮验证

---

## 📚 进阶用法

### 集成到LLaMA-Factory

1. 将生成的 `data_dpo.jsonl` 和 `dataset_info.json` 复制到LLaMA-Factory数据目录
2. 在LLaMA-Factory中引用数据集名称
3. 开始DPO训练

### 自定义工具类别

在工具定义中添加 `category` 字段，用于任务生成时的分类：

```json
{
  "name": "my_tool",
  "category": "custom",
  ...
}
```

### 批量生产

编写脚本循环调用生成命令，每次1000-5000样本

---

## 🎉 开始使用

现在您已经准备好了！打开 http://localhost:3000 开始生成高质量的DPO数据集！

有问题？查看完整文档：[README.md](README.md) 或 [readme.md](readme.md)（设计文档）
