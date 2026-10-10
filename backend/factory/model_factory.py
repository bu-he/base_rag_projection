from langchain_openai import ChatOpenAI
from config.rag import Settings
from config.logger import logger
from langchain_openai import OpenAIEmbeddings



setting=Settings()

model={
      "dashscope":{
            "model_name":setting.dashscope_model_name,
            "api_key":setting.dashscope_api_key,
            "base_url":setting.dashscope_base_url,
      },
      
      "deepseek":{
            "model_name":setting.deepseek_model_name,
            "api_key":setting.deepseek_api_key,
            "base_url":setting.deepseek_base_url,
      }
}

def get_model(
            provider:str|None=None,
            max_tokens:int|None=None,
            temperature:float|None=None,
           ):
      provider=provider or setting.llm_provider
      max_tokens=max_tokens or setting.max_tokens
      temperature=temperature or setting.temperature
      


      if provider not in model:
            raise ValueError(f"不支持的模型提供者：{provider}")
      
      provider_config=model[provider]
      logger.info(f"模型提供商：{provider},使用模型：{provider_config['model_name']}")

      return ChatOpenAI(
            model=model[provider]["model_name"],
            api_key=model[provider]["api_key"],
            base_url=model[provider]["base_url"],
            max_tokens=max_tokens,
            temperature=temperature,
            # 控制“是否输出思考过程”
            extra_body = {"enable_thinking": False}
      )


def embed_model():
      return OpenAIEmbeddings(
            model=setting.embedding_model_name,
            api_key=setting.dashscope_api_key,
            base_url=setting.dashscope_base_url,
            check_embedding_ctx_length=setting.check_embedding_ctx_length,
            chunk_size=setting.embedding_batch_size,
      )
