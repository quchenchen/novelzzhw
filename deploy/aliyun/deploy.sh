#!/bin/bash
# ==========================================
# 阿里云服务器一键部署脚本
# 适用于阿里云轻量应用服务器
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
SERVER_IP="8.130.91.8"

# 生成随机密码
generate_password() {
    openssl rand -base64 24 | tr -dc 'A-Za-z0-9!@#$%^&*' | head -c 24
}

DB_PASSWORD=$(generate_password)
ADMIN_PASSWORD=$(generate_password)

# ==========================================
# 主流程
# ==========================================

log_step "========================================="
log_step "  MuMuAINovel 阿里云部署脚本"
log_step "========================================="
log_info "仓库: $REPO_URL"
log_info "目录: $CLONE_DIR"
log_info "服务器IP: $SERVER_IP"
log_step "========================================="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安装"
    log_info "安装命令: curl -fsSL https://get.docker.com | sh"
    exit 1
fi
log_info "Docker 版本: $(docker --version | cut -d' ' -f3)"

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

# 创建必要目录
mkdir -p logs embedding

# 检查是否已有 .env 文件，保留现有密码
if [ -f ".env" ]; then
    log_warn "检测到现有 .env 文件，保留当前配置"
    # 从现有 .env 读取密码
    if grep -q "POSTGRES_PASSWORD=" .env; then
        EXISTING_DB_PASSWORD=$(grep "POSTGRES_PASSWORD=" .env | cut -d'=' -f2)
        DB_PASSWORD=$EXISTING_DB_PASSWORD
        log_info "使用现有数据库密码"
    fi
    if grep -q "LOCAL_AUTH_PASSWORD=" .env; then
        EXISTING_ADMIN_PASSWORD=$(grep "LOCAL_AUTH_PASSWORD=" .env | cut -d'=' -f2)
        ADMIN_PASSWORD=$EXISTING_ADMIN_PASSWORD
        log_info "使用现有管理员密码"
    fi
else
    log_info "首次部署，生成新密码..."
fi

# 构建镜像
log_step "开始构建 Docker 镜像（约 10-20 分钟）..."
docker build -t $IMAGE_NAME:latest -f Dockerfile .

# 创建 .env 文件
log_step "创建环境配置文件..."
cat > .env << EOF
# ==========================================
# MuMuAINovel 生产环境配置
# ==========================================

# 应用配置
APP_NAME=MuMuAINovel
APP_VERSION=1.3.0
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
TZ=Asia/Shanghai

# PostgreSQL 数据库配置
POSTGRES_DB=mumu_novel
POSTGRES_USER=mumu
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_PORT=5432

# AI 服务配置（必须配置至少一个）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 火山引擎 ARK 配置（推荐）
ARK_API_KEY=085dd906-0999-4910-a205-474a3d37fbf1
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# 默认 AI 配置
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
LINUXDO_REDIRECT_URI=http://$SERVER_IP:8000/api/auth/linuxdo/callback
FRONTEND_URL=http://$SERVER_IP:8000

# 日志配置
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=logs/app.log
EOF

# 创建 docker-compose.yml
log_step "创建 Docker Compose 配置..."
cat > docker-compose.yml << EOFYAML
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
      - ./embedding:/app/embedding
      - ./.env:/app/.env:ro
    environment:
      - DATABASE_URL=postgresql+asyncpg://mumu:$DB_PASSWORD@postgres:5432/mumu_novel
      - DB_HOST=postgres
      - DB_PORT=5432
      - POSTGRES_PASSWORD=$DB_PASSWORD
      - TZ=Asia/Shanghai
      - HF_ENDPOINT=https://hf-mirror.com
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
EOFYAML

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
log_info "访问地址: http://$SERVER_IP:8000"
log_info ""
log_warn "========================================="
log_warn "  重要信息，请妥善保存！"
log_warn "========================================="
log_info "数据库密码: $DB_PASSWORD"
log_info "管理员密码: $ADMIN_PASSWORD"
log_info ""
log_warn "  密码仅在终端显示，未保存到文件"
log_warn "  请立即复制保存上述密码！"
log_warn "========================================="
log_info ""
log_warn "后续操作："
log_warn "1. 设置页面配置 AI Key（已预填火山引擎）"
log_warn "2. 宝塔面板 → 网站 → 添加站点"
log_warn "3. 设置反向代理: http://127.0.0.1:8000"
log_warn "4. 申请 SSL 证书"
log_info ""
log_info "常用命令:"
log_info "  查看日志: docker compose logs -f"
log_info "  重启服务: docker compose restart"
log_info "  更新代码: git pull && docker compose up -d --build"
log_info "  完全清理: docker compose down -v && rm -f .env"
log_step "========================================="
