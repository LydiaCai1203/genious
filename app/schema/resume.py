from pydantic import BaseModel
from typing import Optional, List


class ProjectDetail(BaseModel):
    """项目详情"""
    name: str
    description: str
    tech_stack: List[str]
    responsibilities: List[str]
    duration: Optional[str] = None


class ResumeInfo(BaseModel):
    """简历解析结果"""
    name: Optional[str] = None
    age: Optional[int] = None
    avatar_path: Optional[str] = None  # 头像文件路径
    tech_stack: List[str] = []
    projects: List[ProjectDetail] = []
    education: Optional[str] = None
    work_experience: Optional[str] = None
    raw_text: Optional[str] = None  # 原始文本内容


class ResumeParseRequest(BaseModel):
    """简历解析请求"""
    file_path: Optional[str] = None  # 文件路径
    file_content: Optional[bytes] = None  # 文件内容（base64 或 bytes）
    file_type: str  # "pdf", "txt", "docx", "md"


class ResumeParseResponse(BaseModel):
    """简历解析响应"""
    success: bool
    resume_info: Optional[ResumeInfo] = None
    error: Optional[str] = None

