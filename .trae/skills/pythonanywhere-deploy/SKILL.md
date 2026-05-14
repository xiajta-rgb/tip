---
name: "pythonanywhere-deploy"
description: "Deploys the tip project to PythonAnywhere. Invoke when user asks to deploy, deploy to cloud, or push updates to PythonAnywhere servers."
---

# PythonAnywhere 一键部署

## 功能说明

本skill用于将tip项目一键部署到PythonAnywhere云平台。支持：
- 自动备份原始WSGI配置
- 通过Git拉取最新代码
- 自动重载Web应用
- 多账号部署支持

## 部署架构

### 目标平台
- **平台**: PythonAnywhere (https://www.pythonanywhere.com)
- **主账号**: tip (tip.pythonanywhere.com)
- **项目路径**: /home/tip/tip
- **WSGI文件**: /var/www/tip_pythonanywhere_com_wsgi.py
- **GitHub仓库**: git@github.com:xiajta-rgb/tip.git

### 技术栈
- **后端**: FastAPI + SQLAlchemy
- **数据库**: SQLite (app_data.db)
- **WSGI适配器**: 自定义ASGI到WSGI转换
- **部署方式**: Git clone + Web App reload

## 部署前检查清单

### 1. 代码提交确认
```bash
git status
git add -A
git commit -m "部署前提交"
git push origin main
```

### 2. 环境变量配置
确认PythonAnywhere上的环境变量已设置：
- `ADMIN_USERNAME` - 管理员用户名
- `ADMIN_PASSWORD` - 管理员密码
- `GITHUB_TOKEN` - GitHub API令牌
- `ZHIPU_API_KEY` - 智谱AI密钥（如需AI功能）
- `DEV_MODE` - 开发模式开关

### 3. 依赖安装
在PythonAnywhere的Bash控制台执行：
```bash
cd /home/tip/tip
pip install -r requirements.txt --user
```

## 部署流程

### 方式一：使用deploy_trend.py脚本（推荐）

```bash
cd /path/to/project
python deploy_trend.py
```

该脚本会自动：
1. 备份原始WSGI文件到 `/home/tip/original_wsgi_backup.txt`
2. 上传临时WSGI文件触发Git clone
3. 重载Web应用执行部署
4. 等待30秒后再次重载应用新代码

### 方式二：手动部署

#### Step 1: 在PythonAnywhere Bash控制台执行
```bash
cd /home/tip/
rm -rf tip
git clone git@github.com:xiajta-rgb/tip.git
cd tip
pip install -r requirements.txt --user
```

#### Step 2: 重载Web应用
通过PythonAnywhere API：
```bash
curl -X POST \
  -H "Authorization: Token 62a3a6f8f5bb36ef29ab10bd610ec254e0041649" \
  https://www.pythonanywhere.com/api/v0/user/tip/webapps/tip.pythonanywhere.com/reload/
```

或在PythonAnywhere网页界面点击"Reload"按钮。

## 部署验证

### 1. 检查部署日志
```bash
cat /home/tip/deploy_log.txt  # 成功日志
cat /home/tip/deploy_error.txt  # 错误日志
```

### 2. 验证网站访问
```bash
curl -I https://tip.pythonanywhere.com
# 应返回 200 OK
```

### 3. 测试API端点
```bash
curl https://tip.pythonanywhere.com/api/auth/status
# 应返回认证状态JSON
```

### 4. 检查数据库
```bash
cd /home/tip/tip
ls -la app_data.db  # 确认数据库文件存在
```

## 常见问题排查

### 问题1: 500 Internal Server Error
**原因**: WSGI初始化失败或依赖缺失

**解决**:
```bash
# 1. 检查WSGI日志（PythonAnywhere Web标签页）
# 2. 确认依赖已安装
cd /home/tip/tip
pip install -r requirements.txt --user
# 3. 检查main.py是否存在
ls -la main.py
```

### 问题2: 数据库权限错误
**原因**: SQLite数据库文件权限问题

**解决**:
```bash
cd /home/tip/tip
touch app_data.db
chmod 666 app_data.db
```

### 问题3: 环境变量未生效
**原因**: PythonAnywhere环境变量配置位置错误

**解决**:
1. 登录PythonAnywhere网页
2. 进入Web标签页
3. 在"Environment variables"部分添加变量
4. 点击Reload重载应用

### 问题4: Git clone失败
**原因**: SSH密钥未配置或网络问题

**解决**:
```bash
# 方式1: 使用HTTPS（需输入凭证）
git clone https://github.com/xiajta-rgb/tip.git

# 方式2: 配置SSH密钥
ssh-keygen -t rsa -b 4096
cat ~/.ssh/id_rsa.pub  # 添加到GitHub SSH keys
```

## 多账号部署

项目支持多个PythonAnywhere账号同时部署。配置方式：

### 环境变量方式
在GitHub Actions Secrets或本地.env文件中添加：
```
PYTHONANYWHERE_USERNAME1=tip
PYTHONANYWHERE_PASSWORD1=xxx
PYTHONANYWHERE_USERNAME2=other
PYTHONANYWHERE_PASSWORD2=xxx
```

### 执行续期脚本
```bash
python pythonanywhere_extend.py
```

## 部署后操作

### 1. 管理员登录
访问 https://tip.pythonanywhere.com
点击右上角"管理员登录"
- 用户名: admin（或自定义）
- 密码: 环境变量中配置的ADMIN_PASSWORD

### 2. 数据初始化
首次部署后，系统会自动：
- 创建数据库表结构
- 初始化导航分类数据
- 创建默认管理员账户（如配置）

### 3. 功能测试
- [ ] 首页趋势数据展示
- [ ] 管理员登录/登出
- [ ] JS代码管理器（增删改查）
- [ ] 导航工具管理
- [ ] 论文爬取功能
- [ ] GitHub Token配置

## 回滚方案

如果部署后出现问题，可以快速回滚：

```bash
# 1. 恢复备份的WSGI文件
cp /home/tip/original_wsgi_backup.txt /var/www/tip_pythonanywhere_com_wsgi.py

# 2. 或使用Git回退到指定版本
cd /home/tip/tip
git reset --hard <commit-hash>

# 3. 重载Web应用
# 通过PythonAnywhere网页或API
```

## 性能优化建议

### 1. 数据库优化
```python
# 在config.py中配置连接池
DATABASE_URL=sqlite:///app_data.db?check_same_thread=False
```

### 2. 缓存策略
- 统计数据使用内存缓存（已实现）
- 趋势数据定期更新
- 静态文件使用CDN（可选）

### 3. PythonAnywhere限制
- 免费账号每月需续期
- CPU时间有限制
- 无法使用cron job（免费账号）
- 建议使用GitHub Actions定时触发更新

## 监控和维护

### 日常检查
```bash
# 检查网站响应时间
curl -w "@curl-format.txt" -o /dev/null -s https://tip.pythonanywhere.com

# 检查磁盘空间
df -h /home/tip/

# 检查进程状态
ps aux | grep python
```

### 日志查看
- PythonAnywhere Web标签页 -> Error log
- PythonAnywhere Web标签页 -> Server log
- /home/tip/tip/ 目录下的日志文件

## 安全注意事项

1. **不要提交.env文件到Git**
2. **定期更换ADMIN_PASSWORD**
3. **使用HTTPS访问**
4. **限制API访问频率**
5. **定期备份数据库**

```bash
# 数据库备份
cp /home/tip/tip/app_data.db /home/tip/app_data_backup_$(date +%Y%m%d).db
```
