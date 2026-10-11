# 数据库配置

from utils.filepath import get_file_path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

database_path=get_file_path("rag.db").as_posix()
test_database_path=get_file_path("test_rag.db").as_posix()

# 数据库连接配置
DATABASE_URL = f"sqlite:///{database_path}"
TEST_DATABASE_URL = f"sqlite:///{test_database_path}"

# 创建数据库引擎
engine = create_engine(DATABASE_URL,
                       connect_args={"check_same_thread": False})
test_engine = create_engine(TEST_DATABASE_URL,
                       connect_args={"check_same_thread": False})


# 创建数据库会话工厂
SessionLocal = sessionmaker(
    bind=engine, # 绑定数据库引擎，确保所有会话都使用相同的引擎，后面的会话都是基于这个引擎创建和管理
    autoflush=False, # 禁用自动刷新，避免未提交的变更影响其他会话
    autocommit=False, # 禁用自动提交，确保每个操作都是独立的
)
# 创建测试数据库会话工厂
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)   # ← 加这个


# 依赖注入

def get_db():
  db=SessionLocal()
  try:
    yield db
  finally:
    db.close()

# 测试的依赖注入
def get_test_db():
  db=TestSessionLocal()
  try:
    yield db
  finally:
    db.close()
