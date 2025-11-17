# 🚀 AutoToolDPO 启动脚本说明

本目录包含所有项目启动和管理脚本。

---

## 📋 脚本列表

### 🔧 安装脚本

#### `setup.sh` - 一键环境安装
安装所有依赖，首次使用时运行。

```bash
./scripts/setup.sh
```

**功能**：
- 创建目录结构（logs, data等）
- 创建Python虚拟环境并安装后端依赖
- 安装前端npm依赖
- 创建.env配置文件
- 设置脚本可执行权限

---

### ▶️ 启动脚本

#### `start_all.sh` - 一键启动（推荐）⭐
同时启动前后端服务，后台运行。

```bash
./scripts/start_all.sh
```

**特点**：
- ✅ 自动检查依赖环境
- ✅ 后台运行，关闭终端不会停止服务
- ✅ 自动等待后端就绪后再启动前端
- ✅ 提供详细的服务信息和管理命令

**输出信息**：
```
📝 服务信息:
  • 后端API:  http://localhost:8000
  • 前端界面: http://localhost:3000
  • API文档:  http://localhost:8000/docs

📋 管理命令:
  • 查看后端日志: tail -f logs/backend.log
  • 查看前端日志: tail -f logs/frontend.log
  • 停止所有服务: ./scripts/stop_all.sh
```

---

#### `start_backend.sh` - 启动后端
仅启动后端API服务器，前台运行。

```bash
./scripts/start_backend.sh
```

**适用场景**：
- 单独调试后端
- 需要查看实时日志
- 前端已经在运行

**服务地址**：
- API: http://localhost:8000
- API文档: http://localhost:8000/docs

---

#### `start_frontend.sh` - 启动前端
仅启动前端开发服务器，前台运行。

```bash
./scripts/start_frontend.sh
```

**适用场景**：
- 单独调试前端
- 后端已经在运行
- 需要查看实时编译信息

**访问地址**：http://localhost:3000

---

### ⏹️ 停止脚本

#### `stop_all.sh` - 停止所有服务（推荐）⭐
同时停止前后端服务。

```bash
./scripts/stop_all.sh
```

**功能**：
- 优雅停止所有uvicorn和npm进程
- 如果进程无响应，强制终止
- 清理所有相关进程

---

#### `stop_backend.sh` - 停止后端
仅停止后端API服务器。

```bash
./scripts/stop_backend.sh
```

**功能**：
- 查找所有uvicorn进程
- 发送SIGTERM信号优雅停止
- 等待2秒后强制kill残留进程

---

#### `stop_frontend.sh` - 停止前端
仅停止前端开发服务器。

```bash
./scripts/stop_frontend.sh
```

**功能**：
- 查找所有npm和vite进程
- 发送SIGTERM信号优雅停止
- 等待2秒后强制kill残留进程

---

## 🎯 使用场景

### 场景1: 首次使用
```bash
chmod +x scripts/*.sh    # 设置可执行权限
./scripts/setup.sh       # 安装依赖
./scripts/start_all.sh   # 启动服务
```

### 场景2: 日常开发（推荐）
```bash
# 启动
./scripts/start_all.sh

# 工作...

# 停止
./scripts/stop_all.sh
```

### 场景3: 前端开发（需要实时查看编译信息）
```bash
# 终端1: 启动后端（后台）
./scripts/start_all.sh

# 终端2: 单独启动前端（前台，可看日志）
./scripts/stop_frontend.sh       # 先停止start_all启动的前端
cd frontend
npm run dev
```

### 场景4: 后端开发（需要实时查看日志）
```bash
# 终端1: 单独启动后端（前台）
./scripts/start_backend.sh

# 终端2: 单独启动前端
./scripts/start_frontend.sh
```

### 场景5: 调试问题
```bash
# 查看后端日志
tail -f logs/backend.log

# 查看前端日志
tail -f logs/frontend.log

# 重启服务
./scripts/stop_all.sh
./scripts/start_all.sh
```

---

## ⚠️ 注意事项

### 端口占用
- **后端端口**: 8000
- **前端端口**: 3000

如果端口被占用，可以：

**1. 查找占用端口的进程**
```bash
lsof -i :8000    # 查看8000端口
lsof -i :3000    # 查看3000端口
```

**2. 停止进程**
```bash
./scripts/stop_all.sh    # 使用脚本停止
# 或
kill -9 <PID>            # 手动停止指定进程
```

### 日志文件
- 后端日志: `logs/backend.log`
- 前端日志: `logs/frontend.log`

日志会持续增长，定期清理：
```bash
rm logs/*.log    # 删除所有日志
```

### 权限问题
如果脚本无法执行：
```bash
chmod +x scripts/*.sh    # 重新设置可执行权限
```

---

## 🔍 故障排查

### 问题1: 脚本无法执行
**错误**: `Permission denied`

**解决**:
```bash
chmod +x scripts/*.sh
```

---

### 问题2: 后端启动失败
**检查**:
1. Python3是否安装: `python3 --version`
2. 虚拟环境是否创建: `ls venv/`
3. 依赖是否安装: `./scripts/setup.sh`

**查看日志**:
```bash
tail -f logs/backend.log
```

---

### 问题3: 前端启动失败
**检查**:
1. Node.js是否安装: `node --version`
2. npm是否安装: `npm --version`
3. 依赖是否安装: `cd frontend && npm install`

**查看日志**:
```bash
tail -f logs/frontend.log
```

---

### 问题4: 端口已被占用
**错误**: `Address already in use`

**解决**:
```bash
# 停止所有服务
./scripts/stop_all.sh

# 或手动查找并停止
lsof -i :8000 -i :3000
kill -9 <PID>
```

---

### 问题5: 前后端无法通信
**检查**:
1. 后端是否启动: `curl http://localhost:8000/health`
2. 前端代理配置: 查看 `frontend/vite.config.ts`
3. CORS配置: 查看 `backend/api/app.py`

---

## 📚 相关文档

- [QUICK_START.md](../QUICK_START.md) - 快速开始指南
- [PATH_GUIDE.md](../PATH_GUIDE.md) - 路径配置指南
- [README.md](../README.md) - 项目主文档

---

## 💡 提示

1. **推荐使用 `start_all.sh` 和 `stop_all.sh`** 进行日常操作
2. **后台运行的服务不会随终端关闭而停止**，记得用 `stop_all.sh` 停止
3. **日志文件会持续增长**，定期清理 `logs/` 目录
4. **开发时建议使用前台运行**（`start_backend.sh` + `start_frontend.sh`），方便查看实时日志
