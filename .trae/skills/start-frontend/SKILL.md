---
name: "start-frontend"
description: "启动专利数据展示前端。使用 serve.py 脚本，端口 8082。不要使用 Vite/npm/Vite 或任何 5173 端口。"
---

# 启动前端

本项目的前端位于 `frontend/` 目录，使用原生 HTML/JS/CSS 实现。

## 正确的启动方式

使用 `serve.py` 脚本启动前端服务：

```bash
cd tip
python serve.py
```

访问地址：**http://localhost:8082/frontend/index.html**

## 重要注意事项

1. **不要使用 Vite/npm dev**：前端不是 React/Vite 项目
2. **不要使用 5173 端口**：5173 是 Vite 默认端口，本项目不使用
3. **正确端口是 8082**：由 serve.py 配置

## 服务地址

- 基础地址：http://localhost:8082
- 前端入口：/frontend/index.html
- 数据接口：/output/patent_report_latest.json