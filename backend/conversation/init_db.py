# 数据库初始化，创建数据库表



from .database import  engine
from .models import Base
from config.logger import logger






def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("数据库初始化完成")


if __name__ == "__main__":
    init_db()
    logger.info("数据库初始化完成")