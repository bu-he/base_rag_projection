import logging
from logging.handlers import RotatingFileHandler
from utils.filepath import get_file_path

log_dir=get_file_path("logs")
log_dir.mkdir(parents=True,exist_ok=True)
log_file=log_dir/"ragProject.log"
def setup_logger(name="ragApp",log_file:str=log_file,level=logging.INFO):
    """
    配置日志记录器
    """
    logger=logging.getLogger(name)
    logger.setLevel(level)
    formatter=logging.Formatter("%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s")
    file_handler=RotatingFileHandler(log_file,maxBytes=1024*1024*5,backupCount=5,encoding="utf-8")
    file_handler.setFormatter(formatter)
    console_handler=logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger=setup_logger()

    
    
