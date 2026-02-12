"""文本提取服务 - 从文件和URL中提取纯文本"""
import os
import logging
import tempfile
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from fastapi import UploadFile

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 支持的文件扩展名
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}


class ExtractorService:
    """文本提取服务"""

    def _validate_extension(self, filename: str) -> str:
        """校验并返回文件扩展名"""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}")
        return ext

    async def extract_from_file(self, file: UploadFile) -> str:
        """从上传文件中提取文本"""
        ext = self._validate_extension(file.filename)
        content = await file.read()

        if len(content) > settings.max_file_size:
            raise ValueError(f"文件大小超过限制（最大 {settings.max_file_size // 1024 // 1024}MB）")

        # 写入临时文件后解析
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if ext == ".pdf":
                return self._extract_pdf(tmp_path)
            elif ext == ".docx":
                return self._extract_docx(tmp_path)
            elif ext == ".md":
                return self._extract_text_file(tmp_path)
            elif ext == ".txt":
                return self._extract_text_file(tmp_path)
            else:
                raise ValueError(f"不支持的文件格式: {ext}")
        finally:
            os.unlink(tmp_path)

    def _extract_pdf(self, file_path: str) -> str:
        """解析 PDF 文件"""
        import fitz  # pymupdf

        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
        text = "\n".join(text_parts).strip()
        if not text:
            raise ValueError("PDF 文件内容为空或无法提取文本")
        return text

    def _extract_docx(self, file_path: str) -> str:
        """解析 Word 文档"""
        from docx import Document

        doc = Document(file_path)
        text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
        text = "\n".join(text_parts).strip()
        if not text:
            raise ValueError("Word 文档内容为空")
        return text

    def _extract_text_file(self, file_path: str) -> str:
        """读取纯文本/Markdown 文件"""
        for encoding in ["utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    text = f.read().strip()
                if text:
                    return text
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise ValueError("无法读取文件内容，编码不支持")

    async def extract_from_url(self, url: str) -> str:
        """从 URL 抓取网页正文"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text

        soup = BeautifulSoup(html, "lxml")

        # 移除脚本、样式等无关标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()

        # 优先取 article 或 main 标签内容
        main_content = soup.find("article") or soup.find("main") or soup.find("body")
        if main_content is None:
            raise ValueError("无法从该 URL 提取有效内容")

        text = main_content.get_text(separator="\n", strip=True)
        if not text:
            raise ValueError("网页内容为空")
        return text


# 单例
extractor_service = ExtractorService()
