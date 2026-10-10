from utils.yaml_handler import prompt_config
from pathlib import Path
from utils.filepath import get_file_path
def load_prompt(prompt_path:str | Path):
    """
    加载提示词
    """
    prompt_path=prompt_config[prompt_path]
    with open(get_file_path(prompt_path),"r",encoding="utf-8") as f:
        
        return f.read()
    
if __name__=="__main__":
    
    prompt=load_prompt("rag_summarize_path")
    system_prompt=load_prompt("rag_system_prompt_path")
    
    print(prompt)
    print(system_prompt)
    