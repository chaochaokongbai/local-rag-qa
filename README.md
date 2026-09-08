# 本地知识库问答系统（RAG）

> 基于 **Ollama + ChromaDB + Gradio** 的本地检索增强生成（RAG）应用：把文档切片存入向量库，提问时先检索再生成。**无需联网、无需 API Key**。

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB) ![License](https://img.shields.io/badge/License-MIT-green)

## ✨ 功能

- 📄 基于本地文档的语义问答（检索增强生成 RAG）
- 🔍 ChromaDB 向量检索：理解语义而非关键词
- 🖥️ Gradio 网页界面，开箱即用
- 💾 对话记录自动保存到 SQLite
- 🔒 全程本地：数据不出本机

## 🧱 工作原理

```text
knowledge.txt ──切片──▶ ChromaDB 向量库
                            │  query(问题)
                            ▼
                    检索 Top-K 片段
                            │
                            ▼
   Ollama(qwen2.5:7b) ◀── 资料 + 问题 ──▶ 生成回答
```

提问时，系统先把问题转成向量在知识库中检索最相关的 3 个片段，再连同问题一起交给本地大模型生成回答——避免模型"凭空编造"，答案有据可查。

## 🚀 快速开始

### 1. 准备模型（Ollama）

```bash
# 安装 Ollama：https://ollama.com
ollama pull qwen2.5:7b        # 对话模型
ollama pull nomic-embed-text  # Embedding 模型
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 准备知识库

把想让它学习的资料放进 `knowledge.txt`，**每行一个知识点/段落**（如示例中的请假制度）。

### 4. 运行

```bash
python rag_web.py
```

浏览器打开 <http://127.0.0.1:7860> 即可提问。

首次启动会自动把 `knowledge.txt` 切片写入向量库（目录 `chroma1_data/`），之后重启秒开。**知识库更新后**，删除 `chroma1_data/` 再重启即可重建索引。

## ⚙️ 可配置项（环境变量）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `CHAT_MODEL` | `qwen2.5:7b` | 对话模型 |
| `EMBED_MODEL` | `nomic-embed-text` | Embedding 模型 |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama 服务地址 |
| `TOP_K` | `3` | 检索返回的片段数量 |

示例：`CHAT_MODEL=qwen3:8b python rag_web.py`（换任意 Ollama 支持的模型即可）。

## 📁 项目结构

```text
local-rag-qa/
├── rag_web.py          # 主程序（检索 + 生成 + Web 界面）
├── knowledge.txt       # 知识库源文件（示例：公司请假制度）
├── requirements.txt    # 依赖
├── chroma1_data/       # 向量数据库（自动生成，已 gitignore）
└── chat_history.db     # 对话记录（自动生成，已 gitignore）
```

## 🛠️ 常见问题

**Q：提示"向量检索失败"？**
A：Ollama 没启动，或没拉取 `nomic-embed-text`：先 `ollama serve`，再 `ollama pull nomic-embed-text`。

**Q：回答质量不理想？**
A：① 资料切分越清晰越好（一行一个知识点）；② 尝试更小的 `TOP_K`（更聚焦）或换成更大的对话模型。

**Q：能识别 PDF / Word 吗？**
A：当前是纯文本行切片。接入 `pypdf` / `docx` 解析后按段落入库即可支持，欢迎 PR。

## 📄 License

[MIT](LICENSE)
