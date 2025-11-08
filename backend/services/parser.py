from pypdf import PdfReader
from docx import Document
from typing import Optional


class ResumeParser:
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """PDF에서 텍스트 추출"""
        text = ""
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
        return text

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """DOCX에서 텍스트 추출"""
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        """TXT에서 텍스트 추출"""
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    def parse_resume(self, file_path: str) -> Optional[str]:
        """파일 확장자에 따라 자동 파싱"""
        if file_path.endswith(".pdf"):
            return self.extract_text_from_pdf(file_path)
        elif file_path.endswith(".docx"):
            return self.extract_text_from_docx(file_path)
        elif file_path.endswith(".txt"):
            return self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
