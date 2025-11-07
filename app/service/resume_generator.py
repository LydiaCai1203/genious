import json
from typing import List, Optional
from loguru import logger

from app.schema.generation import (
    GenerateResumeRequest, GenerateResumeResponse,
    GenerateProjectRequest, ProjectGenerationResponse
)
from app.schema.resume import ProjectDetail, ResumeInfo
from app.service.search import search_by_resume_requirements
from config import config


class ResumeGenerator:
    """简历生成器（使用 LLM）"""
    
    def __init__(self):
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        """初始化 LLM 客户端"""
        # 根据配置选择 LLM 服务
        llm_type = getattr(config, "llm_type", "deepseek")
        
        if llm_type == "deepseek":
            return DeepSeekClient()
        elif llm_type == "openai":
            return OpenAIClient()
        else:
            logger.warning(f"未知的 LLM 类型: {llm_type}，使用 DeepSeek")
            return DeepSeekClient()
    
    def generate_resume(self, request: GenerateResumeRequest) -> GenerateResumeResponse:
        """
        生成完整简历
        
        Args:
            request: 简历生成请求
        
        Returns:
            GenerateResumeResponse
        """
        try:
            # 1. 搜索相关的招聘要求和开源项目
            search_results = search_by_resume_requirements(
                job_title=request.target_job_title,
                city=request.target_city,
                salary=request.target_salary,
                industry=request.target_industry,
                tech_stack=", ".join(request.old_resume.tech_stack) if request.old_resume.tech_stack else None
            )
            
            # 2. 生成新的项目经验
            project_request = GenerateProjectRequest(
                job_requirements=search_results["job_requirements"],
                open_source_projects=search_results["open_source_projects"],
                existing_projects=request.old_resume.projects
            )
            
            project_response = self.generate_project_experience(project_request)
            if not project_response.success:
                return GenerateResumeResponse(
                    success=False,
                    error=project_response.error
                )
            
            # 3. 合成完整简历
            resume_content = self._synthesize_resume(
                old_resume=request.old_resume,
                new_projects=project_response.projects,
                job_requirements=search_results["job_requirements"][:3],  # 取前3个作为参考
                template_id=request.template_id
            )
            
            # 4. 生成 PDF（如果需要）
            pdf_path = None
            if getattr(config, "generate_pdf", True):
                pdf_path = self._generate_pdf(resume_content, request.old_resume.name or "resume")
            
            return GenerateResumeResponse(
                success=True,
                resume_content=resume_content,
                resume_pdf_path=pdf_path,
                new_projects=project_response.projects
            )
        
        except Exception as e:
            logger.error(f"生成简历失败: {e}")
            return GenerateResumeResponse(
                success=False,
                error=str(e)
            )
    
    def generate_project_experience(
        self, 
        request: GenerateProjectRequest
    ) -> ProjectGenerationResponse:
        """
        生成项目经验
        
        Args:
            request: 项目生成请求
        
        Returns:
            ProjectGenerationResponse
        """
        try:
            # 构建提示词
            prompt = self._build_project_prompt(
                job_requirements=request.job_requirements,
                open_source_projects=request.open_source_projects,
                existing_projects=request.existing_projects
            )
            
            # 调用 LLM 生成
            response_text = self.llm_client.generate(prompt)
            
            # 解析响应
            projects = self._parse_project_response(response_text)
            
            return ProjectGenerationResponse(
                success=True,
                projects=projects
            )
        
        except Exception as e:
            logger.error(f"生成项目经验失败: {e}")
            return ProjectGenerationResponse(
                success=False,
                error=str(e),
                projects=[]
            )
    
    def _build_project_prompt(
        self,
        job_requirements: List[dict],
        open_source_projects: List[dict],
        existing_projects: Optional[List[ProjectDetail]] = None
    ) -> str:
        """构建项目生成提示词"""
        prompt = """你是一个专业的简历生成助手。根据招聘要求和开源项目信息，生成或增强项目经验。

## 招聘要求（参考）：
"""
        for i, jr in enumerate(job_requirements[:3], 1):
            prompt += f"""
{i}. 岗位：{jr.get('job_title', '')}
   公司：{jr.get('company_name', '')}
   行业：{jr.get('company_industry', '')}
   要求：{jr.get('job_detail', '')}
"""
        
        prompt += "\n## 开源项目（参考）：\n"
        for i, project in enumerate(open_source_projects[:3], 1):
            prompt += f"""
{i}. 项目名称：{project.get('project_name', '')}
   技术栈：{project.get('tech_stack', '')}
   描述：{project.get('description', '')[:200]}
"""
        
        if existing_projects:
            prompt += "\n## 现有项目经验（可在此基础上增强）：\n"
            for i, project in enumerate(existing_projects[:2], 1):
                prompt += f"""
{i}. {project.name}
   技术栈：{', '.join(project.tech_stack)}
   描述：{project.description}
"""
            prompt += "\n请基于现有项目，添加新的功能点，使其更符合招聘要求。\n"
        else:
            prompt += "\n请根据招聘要求和开源项目，生成2-3个新的项目经验。\n"
        
        prompt += """
## 要求：
1. 项目名称要专业、具体
2. 技术栈要匹配招聘要求
3. 项目描述要详细，包含核心功能和技术难点
4. 职责描述要具体，体现技术深度
5. 如果是增强现有项目，要自然融合新功能

请以 JSON 格式返回，格式如下：
[
  {
    "name": "项目名称",
    "description": "项目描述（200-500字）",
    "tech_stack": ["技术1", "技术2", ...],
    "responsibilities": ["职责1", "职责2", ...],
    "duration": "项目时长（可选）"
  }
]
"""
        return prompt
    
    def _parse_project_response(self, response_text: str) -> List[ProjectDetail]:
        """解析 LLM 返回的项目经验"""
        projects = []
        
        try:
            # 尝试提取 JSON
            # 移除可能的 markdown 代码块标记
            text = response_text.strip()
            if text.startswith("```"):
                # 移除代码块标记
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            
            # 尝试解析 JSON
            data = json.loads(text)
            
            if isinstance(data, list):
                for item in data:
                    project = ProjectDetail(
                        name=item.get("name", "未命名项目"),
                        description=item.get("description", ""),
                        tech_stack=item.get("tech_stack", []),
                        responsibilities=item.get("responsibilities", []),
                        duration=item.get("duration")
                    )
                    projects.append(project)
            elif isinstance(data, dict):
                # 单个项目
                project = ProjectDetail(
                    name=data.get("name", "未命名项目"),
                    description=data.get("description", ""),
                    tech_stack=data.get("tech_stack", []),
                    responsibilities=data.get("responsibilities", []),
                    duration=data.get("duration")
                )
                projects.append(project)
        
        except json.JSONDecodeError:
            # 如果 JSON 解析失败，尝试用正则表达式提取
            logger.warning("JSON 解析失败，尝试正则提取")
            projects = self._extract_projects_from_text(response_text)
        
        return projects[:5]  # 最多返回5个项目
    
    def _extract_projects_from_text(self, text: str) -> List[ProjectDetail]:
        """从文本中提取项目信息（备用方法）"""
        projects = []
        # 简单的文本解析逻辑
        # 这里可以实现更复杂的解析
        return projects
    
    def _synthesize_resume(
        self,
        old_resume: ResumeInfo,
        new_projects: List[ProjectDetail],
        job_requirements: List[dict],
        template_id: Optional[str] = None
    ) -> str:
        """合成完整简历"""
        prompt = f"""根据以下信息生成一份完整的简历（Markdown 格式）：

## 个人信息
- 姓名：{old_resume.name or '待填写'}
- 年龄：{old_resume.age or '待填写'}

## 技术栈
{', '.join(old_resume.tech_stack) if old_resume.tech_stack else '待补充'}

## 项目经验
"""
        for i, project in enumerate(new_projects, 1):
            prompt += f"""
### {i}. {project.name}
**技术栈：** {', '.join(project.tech_stack)}
**项目描述：** {project.description}
**主要职责：**
"""
            for resp in project.responsibilities:
                prompt += f"- {resp}\n"
        
        if old_resume.education:
            prompt += f"\n## 教育经历\n{old_resume.education}\n"
        
        if old_resume.work_experience:
            prompt += f"\n## 工作经历\n{old_resume.work_experience}\n"
        
        prompt += "\n请生成格式良好的 Markdown 简历，包含所有必要部分。"
        
        # 调用 LLM 生成简历
        resume_content = self.llm_client.generate(prompt)
        return resume_content
    
    def _generate_pdf(self, content: str, filename: str) -> Optional[str]:
        """生成 PDF 文件"""
        try:
            # 这里可以使用 markdown2pdf 或 weasyprint
            # 暂时返回 None，后续实现
            logger.info(f"PDF 生成功能待实现: {filename}")
            return None
        except Exception as e:
            logger.error(f"生成 PDF 失败: {e}")
            return None


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self):
        self.api_key = getattr(config, "deepseek_api_key", "")
        self.base_url = getattr(config, "deepseek_base_url", "https://api.deepseek.com/v1/chat/completions")
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """调用 DeepSeek API 生成文本"""
        import requests
        
        if not self.api_key:
            logger.warning("DeepSeek API Key 未配置，返回示例文本")
            return self._get_fallback_response()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": getattr(config, "deepseek_model", "deepseek-chat"),
                "messages": [
                    {"role": "system", "content": "你是一个专业的简历生成助手。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.base_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> str:
        """返回备用响应"""
        return """[
  {
    "name": "示例项目",
    "description": "这是一个示例项目描述",
    "tech_stack": ["Python", "FastAPI"],
    "responsibilities": ["负责后端开发", "实现 API 接口"]
  }
]"""


class OpenAIClient:
    """OpenAI API 客户端（备用）"""
    
    def __init__(self):
        self.api_key = getattr(config, "openai_api_key", "")
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """调用 OpenAI API"""
        import requests
        
        if not self.api_key:
            raise ValueError("OpenAI API Key 未配置")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "你是一个专业的简历生成助手。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        
        response = requests.post(self.base_url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


# 创建全局实例
resume_generator = ResumeGenerator()

