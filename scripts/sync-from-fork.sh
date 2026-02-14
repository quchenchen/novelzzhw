#!/bin/bash
# 从 Fork 同步代码到服务器

set -e

PROJECT_DIR="/zjdata/dk_project/novel"
GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

cd "$PROJECT_DIR"

log_info "从 Fork 获取最新代码..."
git fetch origin

CURRENT_COMMIT=$(git rev-parse HEAD)
LATEST_COMMIT=$(git rev-parse origin/main)

if [ "$CURRENT_COMMIT" = "$LATEST_COMMIT" ]; then
    log_info "已是最新版本，无需同步"
    exit 0
fi

log_info "重置到 Fork 最新版本..."
git reset --hard origin/main

log_info "当前版本信息:"
git log --oneline -3

log_info "代码同步完成！"
log_info "后端修改请运行: ./scripts/deploy-backend.sh <file>"
log_info "前端修改请运行: ./scripts/deploy-frontend.sh"
