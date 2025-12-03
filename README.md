# 🎯 说人话 AI 助手

一个基于阿里云通义千问的智能分析工具，包含**简历优化器**和**合同分析器**两大功能，帮助用户用"人话"理解复杂的简历和合同内容。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 核心功能

### 📄 简历分析器
- **智能优化建议**：AI 分析简历内容，提供专业的优化建议
- **HR 视角评估**：从招聘者角度评估简历质量
- **多格式支持**：支持 PDF、Word、图片、文本格式
- **OCR 文字识别**：自动识别图片中的文字内容

### 📋 合同分析器
- **风险识别**：自动识别合同中的风险条款和不公平条件
- **通俗解释**：用大白话解释复杂的法律条款
- **实用建议**：提供具体的应对策略和谈判建议
- **多类型支持**：租房合同、服务协议、劳动合同等

## 🚀 快速开始

### 前置要求

- Python 3.8+
- 阿里云 DashScope API Key（[获取地址](https://dashscope.aliyun.com/)）
- （可选）百度/阿里云/腾讯云 OCR API Key

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/ai-assistant.git
cd ai-assistant
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
# 至少需要配置 DASHSCOPE_API_KEY
```

4. **启动服务**
```bash
python main.py
```

5. **访问应用**
- 简历分析器：http://localhost:8000
- 合同分析器：http://localhost:8000/contract

## 🔧 环境变量配置

在 `.env` 文件中配置以下变量：

### 必需配置
```bash
# AI 分析服务（必需）
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here
```

### 可选配置（OCR服务，至少配置一个）
```bash
# 百度 OCR（推荐，每天500次免费）
BAIDU_OCR_API_KEY=your-baidu-api-key-here
BAIDU_OCR_SECRET_KEY=your-baidu-secret-key-here

# 阿里云 OCR
ALIYUN_ACCESS_KEY_ID=your-aliyun-access-key-id-here
ALIYUN_ACCESS_KEY_SECRET=your-aliyun-access-key-secret-here

# 腾讯云 OCR（每月1000次免费）
TENCENT_SECRET_ID=your-tencent-secret-id-here
TENCENT_SECRET_KEY=your-tencent-secret-key-here
```

## 📦 Docker 部署

```bash
# 构建镜像
docker build -t ai-assistant .

# 运行容器
docker run -d -p 8000:8000 \
  -e DASHSCOPE_API_KEY=your-api-key \
  ai-assistant
```

## 🌐 云平台部署

支持一键部署到以下平台：

- **Railway**：连接 GitHub 仓库自动部署
- **Render**：支持 Dockerfile 自动构建
- **Fly.io**：全球边缘网络部署
- **阿里云/腾讯云**：容器服务或云服务器部署

详细部署说明请查看 [部署说明.md](部署说明.md)

## 🎨 技术栈

### 后端
- **FastAPI**：高性能 Web 框架
- **SQLAlchemy**：数据库 ORM
- **阿里云通义千问**：AI 分析引擎
- **多云 OCR**：百度/阿里云/腾讯云 OCR 服务

### 前端
- **TailwindCSS**：现代化 UI 框架
- **Lucide Icons**：精美图标库
- **原生 JavaScript**：无框架依赖

## 📂 项目结构

```
.
├── main.py                 # FastAPI 主应用
├── services/               # 业务逻辑层
│   ├── resume_analyzer.py  # 简历分析服务
│   ├── contract_analyzer.py # 合同分析服务
│   ├── cloud_ocr.py        # 云端 OCR 服务
│   └── image_parser.py     # 本地 OCR 服务
├── static/                 # 静态文件
│   ├── index.html          # 简历分析器页面
│   └── contract.html       # 合同分析器页面
├── database/               # 数据库相关
├── .env                    # 环境变量配置（不提交）
├── .env.example            # 环境变量示例
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 配置
└── README.md               # 项目说明
```

## 🔒 安全说明

- ✅ API Key 采用环境变量管理，不在代码中硬编码
- ✅ 前端支持加密存储 API Key（AES-256）
- ✅ 上传的文件仅用于分析，不会永久保存
- ✅ 支持会话级、持久化、内存三种安全模式
- ✅ 启用 CSP 防护，防止恶意攻击

## 📝 使用说明

### 简历分析器
1. 配置 DashScope API Key
2. 上传简历文件（PDF/Word/图片/文本）
3. 填写目标职位（可选）
4. 点击"开始优化简历"
5. 查看 AI 生成的优化建议

### 合同分析器
1. 配置 DashScope API Key
2. 选择合同类型（租房/服务/劳动/其他）
3. 上传合同文件
4. 填写补充说明（可选）
5. 点击"开始分析合同"
6. 查看风险分析和通俗解释

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 开源协议

本项目采用 MIT 协议开源 - 查看 [LICENSE](LICENSE) 文件了解详情

## ⚠️ 免责声明

- 本工具提供的分析结果仅供参考，不构成专业建议
- 重要的简历优化和合同签署请咨询专业人士
- 使用本工具产生的任何后果由用户自行承担

## 🙏 致谢

- [阿里云通义千问](https://dashscope.aliyun.com/) - AI 分析引擎
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [TailwindCSS](https://tailwindcss.com/) - UI 框架
- [Lucide](https://lucide.dev/) - 图标库

## 📧 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 [Issue](https://github.com/your-username/ai-assistant/issues)
- 发送邮件至：your-email@example.com

---

⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！
