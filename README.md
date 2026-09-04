# 本地知识库问答系统（RAG）

基于本地大模型（Ollama）和向量数据库（ChromaDB）的 RAG 问答应用，无需联网，无需 API Key，完全本地运行。

## 功能
- 📄 基于本地文档的智能问答（检索增强生成）
- 🔍 ChromaDB 向量检索，理解语义
- 🌐 Gradio 网页界面
- 💬 对话记录自动保存到 SQLite

## 技术栈
- Python
- Ollama（qwen2.5:7b + nomic-embed-text）
- ChromaDB
- Gradio
- SQLite

## 运行方法
1. 安装 Ollama 并拉取模型：
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
2. 安装依赖：
pip install chromadb gradio requests
3. 准备知识库文件 `knowledge.txt`
4. 运行：python rag_web.py
5. 浏览器访问 `http://127.0.0.1:7860`

## 项目结构
├── rag_web.py          # 主程序
├── knowledge.txt       # 知识库源文件
└── chroma1_data/       # 向量数据库（自动生成）