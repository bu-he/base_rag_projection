from pathlib import Path

def get_file_base():
     base_path=Path(__file__).parent.parent
     return base_path

def get_file_path(file_name:str):
     base_path=get_file_base()
     return base_path/file_name

if __name__ == "__main__":
     base_path=get_file_base()
     print(base_path)
     file_path=get_file_path("md5.txt")
     print(file_path)