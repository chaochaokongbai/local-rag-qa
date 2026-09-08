"""本地 RAG 知识库问答系统

基于 Ollama（本地大模型 + Embedding）与 ChromaDB 的检索增强生成（RAG）应用：
把本地文档切片存入向量库，提问时先检索最相关的片段，再交给大模型生成回答。
全程本地运行：无需联网、无需 API Key。

运行前请先:
    ollama pull qwen2.5:7b
    ollama pull nomic-embed-text
    pip install -r requirements.txt

然后:
    python rag_web.py
浏览器打开 http://127.0.0.1:7860 即可使用。
"""

import os
import sqlite3
from pathlib import Path

import chromadb
import gradio as gr
import requests
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

# ---------- 配置（可用环境变量覆盖） ----------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:7b")
TOP_K = int(os.getenv("TOP_K", "3"))                 # 检索返回的片段数

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_FILE = BASE_DIR / "knowledge.txt"          # 知识库源文件（每行一段）
CHROMA_DIR = BASE_DIR / "chroma1_data"               # 向量数据库目录（自动生成）
DB_FILE = BASE_DIR / "chat_history.db"               # 对话记录 SQLite

SYSTEM_PROMPT = "你是中文助手，请只根据给出的资料回答问题；资料中没有的内容请如实说明。"


def load_or_build_collection():
    """加载向量库；首次运行时读取 knowledge.txt 并入库。"""
    ef = OllamaEmbeddingFunction(
        url=f"{OLLAMA_URL}/api/embeddings",
        model_name=EMBED_MODEL,
    )
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(name="knowledge", embedding_function=ef)

    if collection.count() == 0:
        text = KNOWLEDGE_FILE.read_text(encoding="utf-8")
        chunks = [line.strip() for line in text.splitlines() if line.strip()]
        collection.add(documents=chunks, ids=[str(i) for i in range(len(chunks))])
        print(f"知识库初始化完成：共 {len(chunks)} 个片段")
    return collection


COLLECTION = load_or_build_collection()


def save_chat_record(question: str, answer: str) -> None:
    """把一次问答写入 SQLite，便于回顾。"""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS chat_record (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   question TEXT,
                   answer TEXT,
                   time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )"""
        )
        conn.execute(
            "INSERT INTO chat_record (question, answer) VALUES (?, ?)",
            (question, answer),
        )


def retrieve(question: str) -> str:
    """从向量库检索最相关的片段，拼成上下文。"""
    try:
        results = COLLECTION.query(query_texts=[question], n_results=TOP_K)
        documents = (results.get("documents") or [[]])[0]
    except Exception as exc:  # 常见：Ollama 未启动 / Embedding 模型未拉取
        raise RuntimeError(f"向量检索失败（请确认 Ollama 已启动并拉取了 {EMBED_MODEL}）：{exc}") from exc

    if not documents:
        return "（知识库中未找到相关内容）"
    return "\n".join(documents)


def ask(question: str) -> str:
    """检索 + 生成：RAG 主流程。"""
    question = (question or "").strip()
    if not question:
        return "请输入你的问题～"

    try:
        context = retrieve(question)
    except RuntimeError as exc:
        return str(exc)

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": CHAT_MODEL,
                "system": SYSTEM_PROMPT,
                "prompt": f"资料：\n{context}\n\n问题：{question}",
                "stream": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        reply = resp.json()["response"]
    except Exception as exc:
        return f"生成失败（请确认已拉取模型 {CHAT_MODEL}）：{exc}"

    try:
        save_chat_record(question, reply)
    except sqlite3.Error:
        pass  # 记录失败不影响主流程
    return reply


def main() -> None:
    demo = gr.Interface(
        fn=ask,
        inputs=gr.Textbox(label="请输入你的问题", placeholder="例如：事假需要提前几天申请？"),
        outputs=gr.Textbox(label="AI 回答", lines=6),
        title="本地知识库问答（RAG）",
        description="Ollama + ChromaDB + Gradio · 全程本地运行，无需 API Key",
        examples=["事假需要提前几天申请？", "病假需要什么证明材料？", "调休的最小申请单位是？"],
    )
    demo.launch(server_name="127.0.0.1")


if __name__ == "__main__":
    main()
