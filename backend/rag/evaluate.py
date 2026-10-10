# rag/evaluate.py — 检索质量评测：Hit@K + MRR
# 用法：在 ragProject 目录下执行  python -m rag.evaluate
# 评测对象是「检索器」，不调 LLM、不花 token：
#   每条评测数据拿 query 去检索，看 hit_keywords 是否出现在前 K 条结果里
# 跑两轮做对比：
#   第一轮：混合检索（向量 + BM25 融合，重排前）  → 体现"召回"能力
#   第二轮：重排后（compression_retriever，真正喂给大模型的那份） → 体现"精度"能力

import json
import sys
import time
from pathlib import Path

# 兼容两种运行方式：python -m rag.evaluate 或 python rag/evaluate.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.retriever import RetrieverService

K_LIST = [1, 3, 5]   # 统计 Hit@1 / Hit@3 / Hit@5


def find_hit_rank(docs, keywords):
    """返回关键词首次命中的排名（从 1 开始）；前 K 条都没命中返回 None"""
    for rank, doc in enumerate(docs, start=1):
        if any(kw in doc.page_content for kw in keywords):
            return rank
    return None


def evaluate(name, invoke_fn, dataset):
    """评测一个检索器：传入检索函数，输出 Hit@K 和 MRR"""
    hits = {k: 0 for k in K_LIST}
    mrr_sum = 0.0
    ranks = []

    print(f"===== {name} =====")
    for item in dataset:
        docs = invoke_fn(item["query"])                # 检索，返回 Document 列表
        rank = find_hit_rank(docs, item["hit_keywords"])
        ranks.append(rank)

        for k in K_LIST:
            if rank is not None and rank <= k:         # 命中位置在前 K 名内
                hits[k] += 1
        if rank is not None:
            mrr_sum += 1 / rank                        # MRR：命中越靠前贡献越大

        mark = f"第 {rank} 位命中" if rank is not None else "❌ 未命中"
        print(f"  [{item['difficulty']}|{item['category']}|{item.get('query_type', '')}] {item['query']} → {mark}")
        print(f"      ↳ 标准答案出处：{item['source']}")

    total = len(dataset)
    for k in K_LIST:
        print(f"Hit@{k}: {hits[k]}/{total} = {hits[k] / total:.0%}")
    print(f"MRR:   {mrr_sum / total:.3f}")

    # 按题型分组统计 Hit@3：哪种问法容易掉分一目了然
    by_type = {}
    for item, rank in zip(dataset, ranks):
        hit3 = rank is not None and rank <= 3
        stats = by_type.setdefault(item.get("query_type", "-"), [0, 0])
        stats[1] += 1
        if hit3:
            stats[0] += 1
    print("按题型 Hit@3：", "  ".join(f"{t} {h}/{n}" for t, (h, n) in sorted(by_type.items())))
    print()


def main():
    with open(Path(__file__).parent / "eval_dataset.json", encoding="utf-8") as f:
        dataset = json.load(f)
    print(f"加载评测集：{len(dataset)} 条\n")

    print("初始化检索器（embedding + 重排模型，约 20 秒）...")
    t0 = time.perf_counter()
    rs = RetrieverService()
    print(f"初始化完成，耗时 {time.perf_counter() - t0:.1f} 秒\n")

    # 四轮消融对比：逐个组件叠加，看每个组件的贡献
    evaluate("① 纯向量检索（语义）", lambda q: rs.vector_retriever.invoke(q), dataset)
    evaluate("② 纯 BM25 检索（关键词）", lambda q: rs.bm25_retriever.invoke(q), dataset)
    evaluate("③ 混合检索（向量+BM25 融合）", lambda q: rs._ensemble_retriever.invoke(q), dataset)
    evaluate("④ 混合+重排（最终给大模型的结果）", lambda q: rs.compression_retriever.invoke(q), dataset)


if __name__ == "__main__":
    main()
