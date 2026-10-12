from langchain.tools import tool
import random
from rag.retriever import RetrieverService
from config.logger import logger


@tool(description="检索扫地机器人产品知识库，返回带来源的资料。产品使用、故障、维护、价格规格等问题调用；打招呼、闲聊、无关常识不调用,如果返回没有上传任何文件，请先上传文件，那就提醒用户上传")
def search_knowledge_base(query:str):
    from rag.retriever import get_retriever_service
    retriever_service=get_retriever_service()
    if retriever_service._ensemble_retriever is None:
        return "没有上传任何文件，请先上传文件"
    docs=retriever_service.compression_retriever.invoke(query)
    if not docs:
        logger.info(f"未检索到相关内容，查询：{query}")
        return "未检索到相关内容"
    parts=[]
    for i,doc in enumerate(docs,start=1):
        source=doc.metadata.get("file_name","未知")
        parts.append(f"[参考资料{i}]{source}:{doc.page_content}")
    logger.info(f"检索到{len(parts)}条相关内容，查询：{query}")
    return "\n".join(parts)

import re

@tool(description="计算数学表达式的值。用户提出算术计算问题（加减乘除、百分比等）时调用。"
                  "expression 传标准数学表达式（如 '35*12+8'），不要传自然语言句子。"
                  "产品知识问题不要用这个工具。")
def calculator(expression: str) -> str:
    if not re.fullmatch(r"[0-9+\-*/().% ]+", expression):
        return "表达式含非法字符，拒绝计算"
    
    return str(eval(expression))


if __name__=="__main__":
    # print(get_weather("北京"))
    res=search_knowledge_base("扫拖一体机器人可以只扫地不拖地吗？")

    print(res)

    res1=search_knowledge_base("首次使用扫地机器人需要做什么？")
    print(res1)

    res2=search_knowledge_base("扫拖一体机器人可以只扫地不拖地吗？")
    print(res2)
