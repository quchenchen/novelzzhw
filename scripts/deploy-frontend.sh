#!/bin/bash
# 前端构建部署脚本

set -e

PROJECT_DIR="/zjdata/dk_project/novel"
CONTAINER_NAME="mumuainovel"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

cd "$PROJECT_DIR/frontend"

log_info "清理 Vite 缓存..."
rm -rf .vite dist node_modules/.vite

log_info "开始构建前端..."
npm run build

log_info "清理容器内静态文件..."
docker exec "$CONTAINER_NAME" rm -rf /app/static/assets/*

log_info "复制新静态文件到容器..."
docker cp backend/static/. "$CONTAINER_NAME:/app/static/"

log_info "验证部署..."
if docker exec "$CONTAINER_NAME" ls -la /app/static/assets/ | grep -q "index-"; then
    log_info "前端部署成功！"
    log_info "请清除浏览器缓存 (Ctrl+F5) 后测试"
else
    echo "错误: 静态文件部署失败"
    exit 1
fi
