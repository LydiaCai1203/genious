from pydantic import BaseModel
from typing import Optional, List
from app.schema.resume import ResumeInfo, ProjectDetail


class GenerateResumeRequest(BaseModel):
    """简历生成请求"""
    old_resume: ResumeInfo  # 旧简历信息
    target_job_title: str  # 目标岗位
    target_city: str  # 期望城市
    target_salary: Optional[str] = None  # 期望薪资
    target_industry: Optional[str] = None  # 目标行业
    template_id: Optional[str] = None  # 简历模板ID


class GenerateProjectRequest(BaseModel):
    """生成项目经验请求"""
    job_requirements: List[dict]  # 招聘要求列表
    open_source_projects: List[dict]  # 开源项目列表
    existing_projects: Optional[List[ProjectDetail]] = None  # 现有项目（可选）


class GenerateResumeResponse(BaseModel):
    """简历生成响应"""
    success: bool
    resume_content: Optional[str] = None  # 生成的简历内容（Markdown 或 HTML）
    resume_pdf_path: Optional[str] = None  # 生成的 PDF 文件路径
    new_projects: Optional[List[ProjectDetail]] = None  # 新生成的项目经验
    error: Optional[str] = None


class ProjectGenerationResponse(BaseModel):
    """项目经验生成响应"""
    success: bool
    projects: List[ProjectDetail]
    error: Optional[str] = None

