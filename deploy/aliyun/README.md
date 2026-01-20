# 阿里云服务器部署指南

## 快速部署

SSH 登录服务器后执行：

```bash
curl -fsSL https://raw.githubusercontent.com/quchenchen/novelzzhw/main/deploy/aliyun/deploy.sh -o deploy.sh
chmod +x deploy.sh
./deploy.sh
```

## 或手动执行

```bash
# 1. 克隆代码
cd /zjdata/dk_project
git clone https://github.com/quchenchen/novelzzhw.git novel
cd novel

# 2. 构建镜像（约10-20分钟）
docker build -t mumuainovel:latest -f Dockerfile .

# 3. 启动服务
docker compose up -d
```

## 配置说明

### 默认登录
- 地址：http://8.130.91.8:8000
- 用户名：`admin`
- 密码：查看 `.passwords` 文件

### AI 配置（设置页面）
- API 提供商：选择「火山引擎 ARK」
- API Key：已预填 `085dd906-0999-4910-a205-474a3d37fbf1`
- API Base URL：`https://ark.cn-beijing.volces.com/api/v3`
- 模型：选择「【自定义推理端点】DeepSeek3.2」
- 端点 ID：`ep-20251209114631-vzqqw`

### 宝塔面板 Nginx 反向代理
1. 网站 → 添加站点
2. 域名：`8.130.91.8`
3. 设置 → 反向代理 → 目标 URL: `http://127.0.0.1:8000`

## 常用命令

```bash
# 查看日志
docker compose logs -f

# 重启服务
docker compose restart

# 更新代码
git pull && docker compose up -d --build

# 查看密码
cat .passwords
```
