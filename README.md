# ⚔️ DeepSeek AI 智能辩论系统 (AI Debate Agent)

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/ppyc12/-deepseek-autogen-/main/app.py)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-AutoGen-green.svg)](https://microsoft.github.io/autogen/)
[![LLM](https://img.shields.io/badge/Model-DeepSeek%20V3-purple.svg)](https://www.deepseek.com/)

> 🎓 **大三“创新实践”课程项目**：探索基于 Large Language Model (LLM) 的多智能体对抗与协作机制。

## 📖 项目简介

**DeepSeek AI Debate Agent** 是一个可视化的多智能体辩论系统。本项目基于 **Microsoft AutoGen** 框架开发，利用 **DeepSeek-V3** 大模型的强大逻辑推理能力，实现了两个 AI 辩手（正方与反方）围绕用户给定议题进行自动化的、多轮次的逻辑对抗。

通过本项目，旨在展示 **Multi-Agent System (MAS)** 在处理复杂逻辑任务、观点生成及自动化交互方面的潜力。

## ✨ 主要功能

* **🎭 沉浸式辩论体验**：自动构建“正方”、“反方”与“主持人”三个智能体角色。
* **🧠 深度逻辑对抗**：由 DeepSeek-V3 驱动，AI 辩手能够针对对方观点进行实时反驳与论证。
* **⚡ 简洁交互界面**：基于 Streamlit 构建 Web UI，支持自定义辩论轮数与辩题。
* **🚀 灵活配置**：
    * **快速模式**：直接在网页侧边栏输入 API Key 即可使用，无需配置环境变量。
    * **安全模式**：支持 Streamlit Secrets 云端配置，实现无感登录。

## 📸 系统演示

![系统运行截图](https://via.placeholder.com/800x450?text=Please+Upload+App+Screenshot+Here)

## 🛠️ 技术栈

| 组件 | 说明 |
| :--- | :--- |
| **Frontend** | [Streamlit](https://streamlit.io/) (Web 交互界面) |
| **Agent Framework** | [PyAutoGen](https://microsoft.github.io/autogen/) (多智能体编排) |
| **LLM Kernel** | [DeepSeek API](https://www.deepseek.com/) (核心推理引擎) |
| **Environment** | Python 3.11 |

## 🚀 快速开始 (本地运行)

如果你想在本地机器上运行此项目，请按照以下步骤操作：

### 1. 克隆仓库
```bash
git clone [https://github.com/ppyc12/-DeepSeek-AutoGen-.git](https://github.com/ppyc12/-DeepSeek-AutoGen-.git)
cd -DeepSeek-AutoGen-
2. 创建环境
Bash

# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
3. 安装依赖
Bash

pip install -r requirements.txt
4. 启动应用
Bash

streamlit run app.py
⚙️ API Key 配置说明
本项目支持两种配置方式，任选其一：

方式 A：网页端直接输入 (推荐首次测试)

运行应用后，在网页侧边栏或主界面的输入框中直接粘贴你的 DeepSeek API Key。

Key 仅在当前会话有效，刷新页面后需重新输入，不会保存在服务器。

方式 B：云端配置 (推荐部署后使用) 如果你部署在 Streamlit Community Cloud：

进入 App Settings -> Secrets。

添加以下内容：

Ini, TOML

DEEPSEEK_API_KEY = "sk-你的密钥xxxxxxxxxxxxxxxx"
保存后，应用将自动读取 Key，无需手动输入。

📂 项目结构
Plaintext

-DeepSeek-AutoGen-/
├── app.py                # 核心代码：Streamlit 界面与 AutoGen 逻辑
├── requirements.txt      # 依赖包列表 (streamlit, pyautogen, etc.)
├── README.md             # 项目说明文档
└── .gitignore            # Git 忽略配置
🤝 致谢与引用
感谢 DeepSeek 提供的高性价比大模型 API。

感谢 Microsoft AutoGen 团队提供的优秀的 Agent 框架。

Created by [你的名字] | 计算机科学与技术专业 | 2025