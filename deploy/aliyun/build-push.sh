#!/bin/bash
# ==========================================
# 阿里云 ACR 镜像构建与推送脚本
# ==========================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ==========================================
# 配置区域 - 请根据实际情况修改
# ==========================================

# 阿里云 ACR 配置
# 格式: registry.{region}.aliyuncs.com
# region: cn-hangzhou, cn-beijing, cn-shenzhen, cn-hongkong 等
ACR_REGISTRY="registry.cn-hangzhou.aliyuncs.com"

# 命名空间名称
ACR_NAMESPACE="your-namespace"

# 镜像名称
IMAGE_NAME="mumuainovel"

# 镜像标签 (默认使用时间戳 + git commit hash)
VERSION=${VERSION:-$(date +%Y%m%d-%H%M%S)-$(git rev-parse --short HEAD 2>/dev/null || echo "latest")}

# 完整镜像地址
FULL_IMAGE_TAG="${ACR_REGISTRY}/${ACR_NAMESPACE}/${IMAGE_NAME}:${VERSION}"
LATEST_IMAGE_TAG="${ACR_REGISTRY}/${ACR_NAMESPACE}/${IMAGE_NAME}:latest"

# ==========================================
# 函数定义
# ==========================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 登录 ACR
login_acr() {
    log_info "登录阿里云容器镜像服务..."

    # 检查是否已登录
    if docker info | grep -q "Username: ${ACR_USERNAME}"; then
        log_warn "已经登录到 ACR"
        return
    fi

    if [ -z "$ACR_USERNAME" ] || [ -z "$ACR_PASSWORD" ]; then
        log_error "请设置 ACR_USERNAME 和 ACR_PASSWORD 环境变量"
        echo ""
        echo "使用方法:"
        echo "  export ACR_USERNAME=your_username"
        echo "  export ACR_PASSWORD=your_password"
        echo "  $0"
        exit 1
    fi

    echo "$ACR_PASSWORD" | docker login --username="$ACR_USERNAME" --password-stdin $ACR_REGISTRY
    log_info "登录成功"
}

# 构建镜像
build_image() {
    log_info "开始构建 Docker 镜像..."
    log_info "镜像标签: $FULL_IMAGE_TAG"

    docker build -t $FULL_IMAGE_TAG -t $LATEST_IMAGE_TAG -f Dockerfile .

    log_info "镜像构建完成"
}

# 推送镜像
push_image() {
    log_info "开始推送镜像到 ACR..."

    docker push $FULL_IMAGE_TAG
    docker push $LATEST_IMAGE_TAG

    log_info "镜像推送完成"
    log_info "镜像地址: $FULL_IMAGE_TAG"
}

# ==========================================
# 主流程
# ==========================================

main() {
    log_info "========================================="
    log_info "阿里云 ACR 镜像构建与推送"
    log_info "========================================="
    log_info "ACR 地址: $ACR_REGISTRY"
    log_info "命名空间: $ACR_NAMESPACE"
    log_info "镜像名称: $IMAGE_NAME"
    log_info "版本标签: $VERSION"
    log_info "========================================="

    # 检查必要命令
    check_command docker
    check_command git

    # 检查配置
    if [ "$ACR_NAMESPACE" = "your-namespace" ]; then
        log_error "请先修改脚本中的 ACR_NAMESPACE 配置"
        exit 1
    fi

    # 登录 ACR
    login_acr

    # 构建镜像
    build_image

    # 推送镜像
    push_image

    log_info "========================================="
    log_info "构建与推送完成！"
    log_info "========================================="
    echo ""
    log_info "在服务器上使用以下命令部署:"
    echo ""
    echo "  export IMAGE_TAG=$VERSION"
    echo "  bash deploy.sh"
    echo ""
}

# 执行主流程
main "$@"
