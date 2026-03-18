from modelscope import snapshot_download
from sentence_transformers import SentenceTransformer

# 下载模型（国内源）
model_dir = snapshot_download("BAAI/bge-small-zh")

print("模型路径：", model_dir)

model = SentenceTransformer(model_dir)

emb = model.encode(["测试一下RAG系统"])
print("成功！向量维度：", len(emb[0]))
