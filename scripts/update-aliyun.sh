#!/bin/bash
# ==========================================
# 阿里云服务器更新脚本
# ==========================================

SERVER="root@8.130.91.8"
DEPLOY_DIR="/zjdata/dk_project/novel"
IMAGE_NAME="mumuainovel"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================="
echo "  阿里云服务器更新"
echo -e "=========================================${NC}"
echo "服务器: $SERVER"
echo "目录: $DEPLOY_DIR"
echo -e "${GREEN}=========================================${NC}"
echo ""

# 远程执行更新命令
ssh $SERVER << EOF
set -e

echo "进入部署目录..."
cd $DEPLOY_DIR

echo "拉取最新代码..."
git fetch --all
git reset --hard origin/main
git pull

echo "停止当前服务..."
docker compose down

echo "构建 Docker 镜像（约 10-20 分钟）..."
docker build -t $IMAGE_NAME:latest -f Dockerfile .

echo "启动服务..."
docker compose up -d

echo ""
echo "等待服务启动..."
sleep 15

echo "检查服务状态..."
docker compose ps

echo ""
echo "查看最新日志..."
docker compose logs --tail=30
EOF

echo ""
echo -e "${GREEN}========================================="
echo "  更新完成！"
echo -e "=========================================${NC}"
echo "访问地址: http://8.130.91.8:8000"
echo ""
