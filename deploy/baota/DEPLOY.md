# 宝塔面板部署指南

本指南适用于使用宝塔面板的服务器，通过 Docker 管理器部署 MuMuAINovel。

## 前置准备

### 1. 服务器要求
- 操作系统：CentOS/Ubuntu/Debian
- 内存：至少 2GB（推荐 4GB+）
- 磁盘：至少 20GB 可用空间
- 已安装宝塔面板

### 2. 安装 Docker 插件

1. 登录宝塔面板
2. 进入「软件商店」
3. 搜索「Docker」
4. 安装「Docker 管理器」或「Docker 服务」

## 部署步骤

### 第一步：推送镜像到阿里云 ACR

在本地执行：

```bash
# 1. 修改 deploy/aliyun/build-push.sh 中的配置
# - ACR_REGISTRY: 阿里云镜像仓库地址
# - ACR_NAMESPACE: 命名空间
# - ACR_USERNAME: 用户名
# - ACR_PASSWORD: 密码

# 2. 构建并推送镜像
cd deploy/aliyun
chmod +x build-push.sh
ACR_USERNAME=your_username ACR_PASSWORD=your_password ./build-push.sh
```

### 第二步：在宝塔面板部署

#### 方法一：使用 Docker Compose（推荐）

1. **上传文件到服务器**

   在宝塔面板中：
   - 进入「文件」管理
   - 创建目录 `/www/wwwroot/mumuainovel`
   - 创建 `logs` 子目录

2. **创建 .env 文件**

   在 `/www/wwwroot/mumuainovel` 目录下创建 `.env` 文件：

   ```bash
   # 应用配置
   APP_NAME=MuMuAINovel
   APP_HOST=0.0.0.0
   APP_PORT=8000
   DEBUG=false
   TZ=Asia/Shanghai

   # PostgreSQL 配置
   POSTGRES_DB=mumu_novel
   POSTGRES_USER=mumu
   POSTGRES_PASSWORD=your_secure_password_here
   POSTGRES_PORT=5432

   # AI 服务配置（必须配置）
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1

   DEFAULT_AI_PROVIDER=openai
   DEFAULT_MODEL=gpt-4o-mini
   DEFAULT_TEMPERATURE=0.7

   # 本地登录配置
   LOCAL_AUTH_ENABLED=true
   LOCAL_AUTH_USERNAME=admin
   LOCAL_AUTH_PASSWORD=admin123
   LOCAL_AUTH_DISPLAY_NAME=管理员

   # 会话配置
   SESSION_EXPIRE_MINUTES=120

   # LinuxDO OAuth（可选）
   LINUXDO_CLIENT_ID=your_client_id
   LINUXDO_CLIENT_SECRET=your_client_secret
   LINUXDO_REDIRECT_URI=https://your-domain.com/api/auth/linuxdo/callback
   FRONTEND_URL=https://your-domain.com
   ```

3. **修改 docker-compose.yml**

   修改 `deploy/baota/docker-compose.yml` 中的：
   - 镜像地址：`registry.cn-hangzhou.aliyuncs.com/your-namespace/mumuainovel:latest`
   - 数据库密码：与 `.env` 中保持一致

   上传到服务器 `/www/wwwroot/mumuainovel/` 目录

4. **启动容器**

   在宝塔面板「Docker」管理器中：
   - 进入「Docker Compose」标签
   - 选择项目目录：`/www/wwwroot/mumuainovel`
   - 点击「启动」

   或在 SSH 终端执行：

   ```bash
   cd /www/wwwroot/mumuainovel
   docker compose up -d
   ```

#### 方法二：使用宝塔 Docker 管理器界面

1. **获取镜像**

   在宝塔面板「Docker」→「镜像仓库」：
   - 点击「获取镜像」
   - 输入：`registry.cn-hangzhou.aliyuncs.com/your-namespace/mumuainovel:latest`
   - 点击「拉取」

2. **创建 PostgreSQL 容器**

   在「容器器」→「添加容器」：

   | 配置项 | 值 |
   |--------|-----|
   | 镜像 | postgres:18-alpine |
   | 容器名称 | mumu-postgres |
   | 端口映射 | 5432:5432 |
   | 环境变量 | 见下方 |

   环境变量：
   ```
   POSTGRES_DB=mumu_novel
   POSTGRES_USER=mumu
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_INITDB_ARGS=--encoding=UTF8 --locale=C
   TZ=Asia/Shanghai
   ```

   目录映射（可选）：
   ```
   /www/wwwroot/mumuainovel/postgres_data:/var/lib/postgresql/data
   ```

3. **创建应用容器**

   在「容器器」→「添加容器」：

   | 配置项 | 值 |
   |--------|-----|
   | 镜像 | registry.cn-hangzhou.aliyuncs.com/your-namespace/mumuainovel:latest |
   | 容器名称 | mumuainovel |
   | 端口映射 | 8000:8000 |
   | 环境变量 | 见下方 |

   环境变量：
   ```
   DATABASE_URL=postgresql+asyncpg://mumu:your_password@mumu-postgres:5432/mumu_novel
   DB_HOST=mumu-postgres
   DB_PORT=5432
   POSTGRES_PASSWORD=your_password
   TZ=Asia/Shanghai
   OPENAI_API_KEY=your_openai_key
   DEFAULT_AI_PROVIDER=openai
   DEFAULT_MODEL=gpt-4o-mini
   LOCAL_AUTH_ENABLED=true
   LOCAL_AUTH_USERNAME=admin
   LOCAL_AUTH_PASSWORD=admin123
   ```

   目录映射：
   ```
   /www/wwwroot/mumuainovel/logs:/app/logs
   ```

### 第三步：配置 Nginx 反向代理

在宝塔面板「网站」→「添加站点」：

1. **创建站点**

   - 域名：`your-domain.com`
   - 根目录：`/www/wwwroot/mumuainovel`
   - PHP 版本：纯静态

2. **设置反向代理**

   进入站点设置 →「反向代理」→「添加反向代理」：

   | 配置项 | 值 |
   |--------|-----|
   | 代理名称 | mumuainovel |
   | 目标URL | http://127.0.0.1:8000 |
   | 发送域名 | \$host |

3. **自定义配置（可选，用于 WebSocket 支持）**

   点击配置文件，添加以下内容：

   ```nginx
   location / {
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header Host \$host;
       proxy_set_header X-Real-IP \$remote_addr;
       proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto \$scheme;
       proxy_http_version 1.1;
       proxy_set_header Upgrade \$http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```

### 第四步：配置 SSL 证书（推荐）

在站点设置 →「SSL」→「Let's Encrypt」：

1. 选择「文件验证」
2. 输入邮箱
3. 点击「申请」

或上传已有证书。

## 常用操作

### 查看/重启容器

在宝塔「Docker」管理器：
- 查看容器日志
- 重启容器
- 停止/启动容器

### 更新应用

```bash
# SSH 执行
cd /www/wwwroot/mumuainovel

# 拉取新镜像
docker compose pull

# 重启容器
docker compose up -d

# 清理旧镜像
docker image prune -f
```

### 备份数据

```bash
# 备份数据库
docker exec mumu-postgres pg_dump -U mumu mumu_novel > backup.sql

# 备份配置
tar -czf mumu_backup_$(date +%Y%m%d).tar.gz .env logs/
```

## 故障排查

### 容器无法启动

1. 检查日志：宝塔 Docker → 容器 → 查看日志
2. 检查端口是否被占用：`netstat -tlnp | grep 8000`
3. 检查 `.env` 文件配置

### 数据库连接失败

1. 确认 PostgreSQL 容器正在运行
2. 检查数据库密码是否正确
3. 确认两个容器在同一网络中

### 页面无法访问

1. 确认容器正在运行
2. 检查安全组/防火墙是否开放 8000 端口
3. 检查 Nginx 反向代理配置

## 安全建议

1. 修改默认密码
2. 关闭不必要的端口
3. 配置防火墙规则
4. 定期备份数据
5. 使用 SSL 证书
