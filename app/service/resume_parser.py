import re
import os
from typing import Optional
from pathlib import Path

import pdfplumber
from docx import Document

from app.schema.resume import ResumeInfo, ProjectDetail, ResumeParseResponse
from loguru import logger


class ResumeParser:
    """简历解析器"""
    
    def __init__(self):
        self.tech_keywords = [
            "Python", "Java", "Golang", "Go", "JavaScript", "TypeScript",
            "React", "Vue", "Angular", "Spring", "Django", "Flask",
            "MySQL", "PostgreSQL", "MongoDB", "Redis", "Kafka",
            "Docker", "Kubernetes", "Linux", "Git",
            "微服务", "分布式", "高并发", "大数据", "AI", "机器学习"
        ]
    
    def parse(self, file_path: Optional[str] = None, 
              file_content: Optional[bytes] = None,
              file_type: str = "pdf") -> ResumeParseResponse:
        """
        解析简历文件
        
        Args:
            file_path: 文件路径
            file_content: 文件内容（bytes）
            file_type: 文件类型 ("pdf", "txt", "docx", "md")
        
        Returns:
            ResumeParseResponse
        """
        try:
            if file_path:
                text = self._read_file(file_path, file_type)
            elif file_content:
                text = self._read_content(file_content, file_type)
            else:
                return ResumeParseResponse(
                    success=False,
                    error="必须提供 file_path 或 file_content"
                )
            
            if not text:
                return ResumeParseResponse(
                    success=False,
                    error="无法读取文件内容"
                )
            
            # 解析简历信息
            resume_info = self._parse_resume_text(text)
            resume_info.raw_text = text
            
            return ResumeParseResponse(
                success=True,
                resume_info=resume_info
            )
        
        except Exception as e:
            logger.error(f"解析简历失败: {e}")
            return ResumeParseResponse(
                success=False,
                error=str(e)
            )
    
    def _read_file(self, file_path: str, file_type: str) -> str:
        """读取文件内容"""
        if file_type.lower() == "pdf":
            return self._read_pdf(file_path)
        elif file_type.lower() == "txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        elif file_type.lower() == "docx":
            return self._read_docx(file_path)
        elif file_type.lower() == "md":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    
    def _read_content(self, content: bytes, file_type: str) -> str:
        """从 bytes 读取内容"""
        if file_type.lower() == "pdf":
            # 对于 PDF，需要先保存到临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                text = self._read_pdf(tmp_path)
            finally:
                os.unlink(tmp_path)
            return text
        elif file_type.lower() in ["txt", "md"]:
            return content.decode("utf-8")
        elif file_type.lower() == "docx":
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            try:
                text = self._read_docx(tmp_path)
            finally:
                os.unlink(tmp_path)
            return text
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")
    
    def _read_pdf(self, file_path: str) -> str:
        """读取 PDF 文件"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.error(f"读取 PDF 失败: {e}")
            raise
        return text
    
    def _read_docx(self, file_path: str) -> str:
        """读取 Word 文档"""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"读取 Word 文档失败: {e}")
            raise
    
    def _parse_resume_text(self, text: str) -> ResumeInfo:
        """解析简历文本"""
        resume_info = ResumeInfo()
        
        # 提取姓名
        resume_info.name = self._extract_name(text)
        
        # 提取年龄
        resume_info.age = self._extract_age(text)
        
        # 提取技术栈
        resume_info.tech_stack = self._extract_tech_stack(text)
        
        # 提取项目经验
        resume_info.projects = self._extract_projects(text)
        
        # 提取教育经历
        resume_info.education = self._extract_education(text)
        
        # 提取工作经历
        resume_info.work_experience = self._extract_work_experience(text)
        
        return resume_info
    
    def _extract_name(self, text: str) -> Optional[str]:
        """提取姓名"""
        # 尝试从开头提取姓名（通常在简历开头）
        lines = text.split("\n")[:5]
        for line in lines:
            line = line.strip()
            # 匹配中文姓名（2-4个字符）
            match = re.search(r"^[\u4e00-\u9fa5]{2,4}$", line)
            if match:
                return match.group()
        return None
    
    def _extract_age(self, text: str) -> Optional[int]:
        """提取年龄"""
        # 匹配年龄模式：年龄：25、25岁、age: 25 等
        patterns = [
            r"年龄[：:]\s*(\d+)",
            r"(\d+)岁",
            r"age[：:]\s*(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    age = int(match.group(1))
                    if 18 <= age <= 100:  # 合理年龄范围
                        return age
                except:
                    pass
        return None
    
    def _extract_tech_stack(self, text: str) -> list:
        """提取技术栈"""
        found_tech = []
        text_lower = text.lower()
        
        for tech in self.tech_keywords:
            # 检查技术关键词是否在文本中
            if tech.lower() in text_lower or tech in text:
                found_tech.append(tech)
        
        # 去重并保持顺序
        seen = set()
        result = []
        for tech in found_tech:
            if tech not in seen:
                seen.add(tech)
                result.append(tech)
        
        return result
    
    def _extract_projects(self, text: str) -> list:
        """提取项目经验"""
        projects = []
        
        # 查找项目相关的段落
        # 匹配模式：项目名称、项目描述等
        project_sections = re.split(
            r"(项目[名称]?[：:]\s*|项目经验|项目经历|Project)",
            text,
            flags=re.IGNORECASE
        )
        
        for i, section in enumerate(project_sections[1:], 1):
            if i % 2 == 0:  # 取项目内容部分
                project = self._parse_project_section(section)
                if project:
                    projects.append(project)
        
        # 如果没有找到明确的项目段落，尝试从整个文本中提取
        if not projects:
            # 查找包含技术栈的段落作为项目
            lines = text.split("\n")
            current_project = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 检查是否包含技术关键词
                has_tech = any(tech.lower() in line.lower() for tech in self.tech_keywords)
                
                if has_tech and len(line) > 10:
                    if current_project is None:
                        current_project = ProjectDetail(
                            name=line[:50] if len(line) > 50 else line,
                            description=line,
                            tech_stack=self._extract_tech_stack(line),
                            responsibilities=[]
                        )
                    else:
                        current_project.description += " " + line
                        current_project.tech_stack.extend(self._extract_tech_stack(line))
                
                # 如果遇到明显的分隔，保存当前项目
                if current_project and (line.startswith("项目") or len(line) < 5):
                    projects.append(current_project)
                    current_project = None
            
            if current_project:
                projects.append(current_project)
        
        return projects[:10]  # 最多返回10个项目
    
    def _parse_project_section(self, section: str) -> Optional[ProjectDetail]:
        """解析单个项目段落"""
        lines = section.split("\n")
        if not lines:
            return None
        
        # 第一行通常是项目名称
        name = lines[0].strip()[:100]
        if not name or len(name) < 3:
            return None
        
        # 提取描述
        description = " ".join(lines[1:6])[:500]  # 取前5行作为描述
        
        # 提取技术栈
        tech_stack = self._extract_tech_stack(section)
        
        # 提取职责（包含"负责"、"实现"等关键词的句子）
        responsibilities = []
        for line in lines:
            if any(keyword in line for keyword in ["负责", "实现", "开发", "设计", "优化"]):
                responsibilities.append(line.strip()[:200])
        
        return ProjectDetail(
            name=name,
            description=description if description else section[:500],
            tech_stack=tech_stack,
            responsibilities=responsibilities[:5]  # 最多5条职责
        )
    
    def _extract_education(self, text: str) -> Optional[str]:
        """提取教育经历"""
        # 查找教育相关的段落
        patterns = [
            r"教育[背景经历]?[：:]\s*([^\n]+(?:\n[^\n]+){0,3})",
            r"学历[：:]\s*([^\n]+)",
            r"毕业[院校]?[：:]\s*([^\n]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]
        
        return None
    
    def _extract_work_experience(self, text: str) -> Optional[str]:
        """提取工作经历"""
        # 查找工作经历相关的段落
        patterns = [
            r"工作[经历经验]?[：:]\s*([^\n]+(?:\n[^\n]+){0,5})",
            r"工作[经历经验][：:]\s*([^\n]+(?:\n[^\n]+){0,5})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:500]
        
        return None


# 创建全局实例
resume_parser = ResumeParser()

