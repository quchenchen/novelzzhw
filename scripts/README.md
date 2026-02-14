# 部署脚本使用说明

## 脚本列表

| 脚本 | 用途 | 使用场景 |
|------|------|----------|
| sync-from-fork.sh | 从 Fork 同步代码 | 本地修改并 push 后，在服务器上运行 |
| deploy-backend.sh | 快速部署后端文件 | 修改 Python 文件后，无需重建镜像 |
| deploy-frontend.sh | 构建并部署前端 | 修改 TypeScript/React 文件后 |

## 使用示例

### 1. 同步代码
```bash
cd /zjdata/dk_project/novel
./scripts/sync-from-fork.sh
```

### 2. 部署后端文件
```bash
cd /zjdata/dk_project/novel
./scripts/deploy-backend.sh backend/app/api/wizard_stream.py
```

### 3. 部署前端
```bash
cd /zjdata/dk_project/novel
./scripts/deploy-frontend.sh
```

## 完整工作流

### 场景：修复 Bug
```bash
# 本地
git add .
git commit -m "fix: xxx"
git push origin main

# 服务器
ssh root@8.130.91.8
cd /zjdata/dk_project/novel
./scripts/sync-from-fork.sh

# 如果是后端修改
./scripts/deploy-backend.sh backend/app/api/xxx.py

# 如果是前端修改
./scripts/deploy-frontend.sh
```

## 注意事项

1. **前端构建前会清理缓存** - 无需手动删除 .vite
2. **后端部署会重启容器** - 等待约 5 秒后可用
3. **环境变量修改** - 编辑 `.env` 后手动 `docker restart mumuainovel`
