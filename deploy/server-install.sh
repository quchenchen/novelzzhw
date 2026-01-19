#!/bin/bash
# ==========================================
# 服务器一键部署脚本
# 在阿里云轻量应用服务器上运行
# ==========================================

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# 配置
REPO_URL="https://github.com/quchenchen/novelzzhw.git"
CLONE_DIR="/zjdata/dk_project/novel"
IMAGE_NAME="mumuainovel"
DB_PASSWORD="MuMu@2024"  # 默认数据库密码，请修改
ADMIN_PASSWORD="MuMu@2024"  # 默认管理员密码，请修改

# ==========================================
# 主流程
# ==========================================

log_step "========================================="
log_step "  MuMuAINovel 服务器部署脚本"
log_step "========================================="
log_info "仓库: $REPO_URL"
log_info "目录: $CLONE_DIR"
log_step "========================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安装，请先安装 Docker"
    log_info "安装命令: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
log_info "Docker 版本: $(docker --version | cut -d' ' -f3)"

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    log_error "Docker Compose 未安装"
    exit 1
fi
log_info "Docker Compose 版本: $(docker compose version | cut -d' ' -f4)"

# 克隆代码
log_step "克隆代码仓库..."
if [ -d "$CLONE_DIR" ]; then
    log_warn "目录已存在，正在更新..."
    cd "$CLONE_DIR"
    git fetch --all
    git reset --hard origin/main
    git pull
else
    mkdir -p "$(dirname "$CLONE_DIR")"
    git clone "$REPO_URL" "$CLONE_DIR"
    cd "$CLONE_DIR"
fi

# 构建镜像
log_step "开始构建 Docker 镜像（可能需要 10-20 分钟）..."
docker build -t $IMAGE_NAME:latest -f Dockerfile .

# 创建 logs 目录
mkdir -p logs

# 创建 .env 文件
log_step "创建环境配置文件..."
cat > .env << EOF
# 应用配置
APP_NAME=MuMuAINovel
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
TZ=Asia/Shanghai

# PostgreSQL 配置
POSTGRES_DB=mumu_novel
POSTGRES_USER=mumu
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_PORT=5432

# AI 服务配置（必须配置）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

DEFAULT_AI_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=32000

# 本地账户登录配置
LOCAL_AUTH_ENABLED=true
LOCAL_AUTH_USERNAME=admin
LOCAL_AUTH_PASSWORD=$ADMIN_PASSWORD
LOCAL_AUTH_DISPLAY_NAME=管理员

# 会话配置
SESSION_EXPIRE_MINUTES=120
SESSION_REFRESH_THRESHOLD_MINUTES=30

# LinuxDO OAuth（可选）
LINUXDO_CLIENT_ID=your_client_id
LINUXDO_CLIENT_SECRET=your_client_secret
LINUXDO_REDIRECT_URI=https://your-domain.com/api/auth/linuxdo/callback
FRONTEND_URL=https://your-domain.com

# 日志配置
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=logs/app.log
EOF
log_warn ".env 文件已创建，请修改 OPENAI_API_KEY 后重启服务"

# 创建 docker-compose.yml
log_step "创建 Docker Compose 配置..."
cat > docker-compose.yml << EOF
services:
  postgres:
    image: postgres:18-alpine
    container_name: mumu-postgres
    environment:
      POSTGRES_DB: mumu_novel
      POSTGRES_USER: mumu
      POSTGRES_PASSWORD: $DB_PASSWORD
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
      TZ: Asia/Shanghai
    volumes:
      - mumu_postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - mumu-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mumu -d mumu_novel"]
      interval: 10s
      timeout: 5s
      retries: 5

  mumuainovel:
    image: $IMAGE_NAME:latest
    container_name: mumuainovel
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./.env:/app/.env:ro
    environment:
      - DATABASE_URL=postgresql+asyncpg://mumu:$DB_PASSWORD@postgres:5432/mumu_novel
      - DB_HOST=postgres
      - DB_PORT=5432
      - POSTGRES_PASSWORD=$DB_PASSWORD
      - TZ=Asia/Shanghai
    restart: unless-stopped
    networks:
      - mumu-network
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  mumu_postgres_data:
    driver: local

networks:
  mumu-network:
    driver: bridge
EOF

# 启动服务
log_step "启动服务..."
docker compose up -d

# 等待服务启动
log_info "等待服务启动（约 30 秒）..."
sleep 30

# 检查服务状态
log_step "检查服务状态..."
docker compose ps

log_step "========================================="
log_info "  部署完成！"
log_step "========================================="
log_info "访问地址: http://$(hostname -I | awk '{print $1}'):8000"
log_info ""
log_warn "请执行以下操作："
log_warn "1. 修改 .env 中的 OPENAI_API_KEY"
log_warn "2. 修改数据库密码和管理员密码"
log_warn "3. 配置宝塔面板 Nginx 反向代理"
log_warn "4. 申请 SSL 证书"
log_info ""
log_info "修改配置后重启服务:"
log_info "  docker compose restart mumuainovel"
log_info ""
log_info "查看日志:"
log_info "  docker compose logs -f"
log_step "========================================="
