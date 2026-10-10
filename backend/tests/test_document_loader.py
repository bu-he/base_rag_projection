# tests/test_document_loader.py — DocumentService 单元测试（不碰 HTTP、不碰数据库）
# 和 test_message.py 那种「走接口的集成测试」相对：这里直接调类的方法，测纯逻辑，
# 所以跑起来毫秒级，也不需要 client / auth_client 夹具。

from langchain_core.documents import Document

from rag.document_loader import DocumentService


def test_process_empty_file_rejected(tmp_path):
    """空文件应被优雅拒绝：返回 (None, None) 而不是抛异常

    tmp_path 是 pytest 内置夹具：给本次测试一个专属临时目录，跑完自动删。
    对应真实场景：用户上传了一个空文件，入库流程应记录错误并跳过它。
    """
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("", encoding="utf-8")

    loader = DocumentService()
    chunks, md5 = loader.process_document(empty_file)

    # 无论死在「加载为空」还是「分割为空」哪个分支，契约都是 (None, None)
    assert chunks is None
    assert md5 is None


def test_add_metadata_sets_chunk_id(tmp_path):
    """add_metadata 应给每个 chunk 打上文件名 / md5 / chunk_id 等元数据

    chunk_id 格式为 "文件名_序号"（0 起），是以后做 Ground Truth
    chunk 级评测的定位依据。（原名 chunk_index，改名后测试同步跟进）
    """
    loader = DocumentService()
    file_path = tmp_path / "faq.txt"
    file_path.write_text("占位内容", encoding="utf-8")

    # 手工构造两个 chunk（不用真的分割文件，这里只测打元数据的逻辑）
    docs = [Document(page_content="第一块"), Document(page_content="第二块")]

    loader.add_metadata(file_path, docs, md5="abc123")

    assert docs[0].metadata["file_name"] == "faq.txt"
    assert docs[0].metadata["md5"] == "abc123"
    assert docs[0].metadata["chunk_id"] == "faq.txt_0"
    assert docs[1].metadata["chunk_id"] == "faq.txt_1"
