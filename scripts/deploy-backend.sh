#!/bin/bash
# 后端快速部署脚本 - 无需重建镜像

set -e

PROJECT_DIR="/zjdata/dk_project/novel"
CONTAINER_NAME="mumuainovel"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

cd "$PROJECT_DIR"

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <文件路径>"
    echo ""
    echo "示例:"
    echo "  $0 backend/app/api/wizard_stream.py"
    echo "  $0 backend/app/services/prompt_service.py"
    exit 1
fi

FILE_PATH="$1"

# 检查文件存在
if [ ! -f "$FILE_PATH" ]; then
    echo "错误: 文件不存在: $FILE_PATH"
    exit 1
fi

# 计算容器内路径
CONTAINER_PATH="/app/${FILE_PATH#backend/}"

log_info "复制文件到容器: $FILE_PATH -> $CONTAINER_PATH"
docker cp "$FILE_PATH" "${CONTAINER_NAME}:${CONTAINER_PATH}"

log_info "重启容器..."
docker restart "$CONTAINER_NAME"

# 等待容器启动
log_info "等待容器启动..."
sleep 5

# 检查容器状态
if docker ps | grep -q "$CONTAINER_NAME"; then
    log_info "部署成功！容器运行正常"
else
    echo "错误: 容器未运行"
    docker logs "$CONTAINER_NAME" --tail 20
    exit 1
fi
