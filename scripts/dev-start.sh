#!/bin/bash
# ==========================================
# 本地开发环境启动脚本
# ==========================================

set -e

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 项目根目录
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# ==========================================
# 后端启动
# ==========================================

start_backend() {
    log_info "========================================="
    log_info "  启动后端服务"
    log_info "========================================="

    cd "$PROJECT_ROOT/backend"

    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        log_warn "虚拟环境不存在，正在创建..."
        python3 -m venv venv
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 安装依赖
    if [ ! -f "venv/.installed" ]; then
        log_warn "安装 Python 依赖..."
        pip install -r requirements.txt
        touch venv/.installed
    fi

    # 检查 .env 文件
    if [ ! -f ".env" ]; then
        log_warn "创建 .env 文件..."
        cp .env.example .env
        log_warn "请修改 .env 中的配置"
    fi

    # 启动后端
    log_info "启动 FastAPI 服务 (端口 8000)..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# ==========================================
# 前端启动
# ==========================================

start_frontend() {
    log_info "========================================="
    log_info "  启动前端服务"
    log_info "========================================="

    cd "$PROJECT_ROOT/frontend"

    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        log_warn "安装前端依赖..."
        npm install
    fi

    # 启动前端
    log_info "启动 Vite 开发服务器 (端口 5173)..."
    npm run dev
}

# ==========================================
# 全部启动
# ==========================================

start_all() {
    log_info "========================================="
    log_info "  启动完整开发环境"
    log_info "========================================="

    # 后端（后台运行）
    cd "$PROJECT_ROOT/backend"

    if [ ! -d "venv" ]; then
        log_warn "创建虚拟环境..."
        python3 -m venv venv
    fi

    source venv/bin/activate

    if [ ! -f "venv/.installed" ]; then
        log_warn "安装 Python 依赖..."
        pip install -r requirements.txt > /dev/null 2>&1
        touch venv/.installed
    fi

    if [ ! -f ".env" ]; then
        cp .env.example .env
    fi

    log_info "启动后端 (端口 8000)..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../logs/backend.pid
    log_info "后端 PID: $BACKEND_PID"

    # 前端
    cd "$PROJECT_ROOT/frontend"

    if [ ! -d "node_modules" ]; then
        log_warn "安装前端依赖..."
        npm install
    fi

    log_info "启动前端 (端口 5173)..."
    npm run dev
}

# ==========================================
# 停止服务
# ==========================================

stop_services() {
    log_info "停止开发服务..."

    if [ -f "logs/backend.pid" ]; then
        PID=$(cat logs/backend.pid)
        kill $PID 2>/dev/null || true
        rm logs/backend.pid
        log_info "后端已停止 (PID: $PID)"
    fi

    # 查找并杀死 uvicorn 进程
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
}

# ==========================================
# 主流程
# ==========================================

case "${1:-all}" in
    backend)
        mkdir -p logs
        start_backend
        ;;
    frontend)
        start_frontend
        ;;
    all)
        mkdir -p logs
        start_all
        ;;
    stop)
        stop_services
        ;;
    *)
        echo "用法: $0 [backend|frontend|all|stop]"
        echo ""
        echo "  backend   - 只启动后端"
        echo "  frontend  - 只启动前端"
        echo "  all       - 启动前后端（默认）"
        echo "  stop      - 停止服务"
        exit 1
        ;;
esac
