"""内容预处理层 — 统一将各格式文档转换为 Markdown

使用 Microsoft MarkItDown 库，支持：
HTML / PDF / DOCX / XLSX / PPTX / CSV / JSON / XML / TXT / Markdown
"""

from io import BytesIO
from pathlib import Path
from typing import Optional

from markitdown import MarkItDown, StreamInfo

_md = MarkItDown()

# 扩展名 → (MIME 类型, 扩展名)
EXTENSION_MAP: dict[str, tuple[str, str]] = {
    ".html": ("text/html", ".html"),
    ".htm": ("text/html", ".html"),
    ".pdf": ("application/pdf", ".pdf"),
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
    ),
    ".xlsx": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    ".pptx": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
    ),
    ".csv": ("text/csv", ".csv"),
    ".json": ("application/json", ".json"),
    ".xml": ("text/xml", ".xml"),
    ".txt": ("text/plain", ".txt"),
    ".md": ("text/markdown", ".md"),
}


def _guess_format(filename: str) -> tuple[str, str]:
    """根据文件名推断 MIME 类型和扩展名"""
    ext = Path(filename).suffix.lower()
    if ext in EXTENSION_MAP:
        return EXTENSION_MAP[ext]
    return ("text/plain", ".txt")


def preprocess_bytes(content: bytes, filename: str = "document.html") -> str:
    """将原始字节内容转换为 Markdown。

    Args:
        content: 原始文件内容的字节数据
        filename: 原始文件名（用于推断格式），默认 "document.html"

    Returns:
        转换后的 Markdown 字符串
    """
    mime, ext = _guess_format(filename)
    result = _md.convert(
        BytesIO(content),
        stream_info=StreamInfo(mimetype=mime, extension=ext),
    )
    return result.text_content


def preprocess_file(filepath: str | Path) -> str:
    """将本地文件转换为 Markdown。

    Args:
        filepath: 本地文件路径

    Returns:
        转换后的 Markdown 字符串
    """
    result = _md.convert(str(filepath))
    return result.text_content


__all__ = ["preprocess_bytes", "preprocess_file"]
