import yaml
from utils.filepath import get_file_path

def load_prompt_config(config_path:str=get_file_path("config/prompt.yaml")):
       with open(config_path,"r",encoding="utf-8") as f:
             return yaml.load(f,Loader=yaml.FullLoader)
       
    
            
prompt_config=load_prompt_config()




if __name__=="__main__":
       result=prompt_config["rag_summarize_path"]
       print(result)

