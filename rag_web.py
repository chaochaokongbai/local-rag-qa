import requests
import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
ef=OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text"
)
client=chromadb.PersistentClient(path="./chroma1_data")
collection=client.get_or_create_collection(name="knowledge",embedding_function=ef)
if collection.count()==0:
    with open("knowledge.txt",encoding="utf-8")as f:
        content=f.read()
    chunks=content.strip().split("\n")
    for i, chunk in enumerate(chunks):
        collection.add(documents=[chunk], ids=[str(i)])
    print("知识库初始化完成")
import sqlite3
def ask(question):
    results = collection.query(query_texts=[question], n_results=3)
    if results["documents"]:
        context = "\n".join(results["documents"][0])
    else:
        context = "知识库未找到相关内容"
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:7b",
            "system": "你是中文助手，请根据资料回答。",
            "prompt": f"根据资料回答：\n资料:{context}\n问题:{question}",
            "stream": False
        },
        timeout=120
    )
    reply = resp.json()["response"]
    # ===== 新增：保存聊天记录 =====
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT INTO chat_record (question, answer) VALUES (?, ?)", (question, reply))
    conn.commit()
    conn.close()
    return reply
import gradio as gr
demo=gr.Interface(
    fn=ask,                # 绑定刚才的问答函数
    inputs=gr.Textbox(label="请输入你的问题"),   # 输入框
    outputs=gr.Textbox(label="AI回答")          # 输出框
    )
demo.launch()