from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

from app.schema import GerneralResponse
from app.schema.resume import ResumeParseRequest, ResumeParseResponse
from app.schema.generation import GenerateResumeRequest, GenerateResumeResponse
from app.service.resume_parser import resume_parser
from app.service.resume_generator import resume_generator
from loguru import logger

router = APIRouter()


@router.post("/parse")
async def parse_resume(
    file: UploadFile = File(...),
    file_type: str = Form("pdf")
) -> GerneralResponse:
    """
    解析简历文件
    
    Args:
        file: 上传的简历文件
        file_type: 文件类型 (pdf, txt, docx, md)
    
    Returns:
        解析后的简历信息
    """
    response = GerneralResponse()
    
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 解析简历
        parse_response = resume_parser.parse(
            file_content=file_content,
            file_type=file_type
        )
        
        if not parse_response.success:
            response.code = 400
            response.message = parse_response.error or "解析失败"
            return response
        
        response.data = parse_response.resume_info.dict()
        return response
    
    except Exception as e:
        logger.error(f"解析简历失败: {e}")
        response.code = 500
        response.message = str(e)
        return response


@router.post("/generate")
async def generate_resume(
    request: GenerateResumeRequest
) -> GerneralResponse:
    """
    生成新简历
    
    Args:
        request: 简历生成请求
    
    Returns:
        生成的简历内容（Markdown 格式）
    """
    response = GerneralResponse()
    
    try:
        # 生成简历
        generate_response = resume_generator.generate_resume(request)
        
        if not generate_response.success:
            response.code = 400
            response.message = generate_response.error or "生成失败"
            return response
        
        response.data = {
            "resume_content": generate_response.resume_content,
            "resume_pdf_path": generate_response.resume_pdf_path,
            "new_projects": [
                project.dict() for project in generate_response.new_projects or []
            ]
        }
        return response
    
    except Exception as e:
        logger.error(f"生成简历失败: {e}")
        response.code = 500
        response.message = str(e)
        return response


@router.post("/generate-projects")
async def generate_projects(
    job_requirements: list,
    open_source_projects: list,
    existing_projects: Optional[list] = None
) -> GerneralResponse:
    """
    仅生成项目经验（不生成完整简历）
    
    Args:
        job_requirements: 招聘要求列表
        open_source_projects: 开源项目列表
        existing_projects: 现有项目列表（可选）
    
    Returns:
        生成的项目经验列表
    """
    response = GerneralResponse()
    
    try:
        from app.schema.generation import GenerateProjectRequest
        from app.schema.resume import ProjectDetail
        
        # 转换现有项目
        existing = None
        if existing_projects:
            existing = [
                ProjectDetail(**p) if isinstance(p, dict) else p
                for p in existing_projects
            ]
        
        project_request = GenerateProjectRequest(
            job_requirements=job_requirements,
            open_source_projects=open_source_projects,
            existing_projects=existing
        )
        
        project_response = resume_generator.generate_project_experience(project_request)
        
        if not project_response.success:
            response.code = 400
            response.message = project_response.error or "生成失败"
            return response
        
        response.data = {
            "projects": [
                project.dict() for project in project_response.projects
            ]
        }
        return response
    
    except Exception as e:
        logger.error(f"生成项目经验失败: {e}")
        response.code = 500
        response.message = str(e)
        return response

