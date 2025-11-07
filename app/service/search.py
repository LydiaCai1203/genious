from typing import List, Optional
from loguru import logger
import requests

from app.repositry.milvus import query_job_requirements
from config import config


def search_job_requirements(
    query: str,
    city: Optional[str] = None,
    salary: Optional[str] = None,
    industry: Optional[str] = None,
    top_k: int = 10
) -> List[dict]:
    """
    搜索招聘要求
    
    Args:
        query: 查询文本（岗位、技术栈等）
        city: 城市过滤
        salary: 薪资过滤
        industry: 行业过滤
        top_k: 返回数量
    
    Returns:
        招聘要求列表
    """
    try:
        # 这里需要指定使用哪个 collection
        # 暂时使用配置中的 collection，后续需要根据实际需求调整
        from app.db.milvus import prepare_milvus_oper
        from pymilvus import Collection
        
        # 直接调用 repository 方法
        # 注意：这里需要确保 collection 已经加载
        results = query_job_requirements(
            collection=None,  # prepare_milvus_oper 会自动处理
            query=query,
            top_k=top_k,
            city=city,
            salary=salary,
            industry=industry
        )
        return results
    except Exception as e:
        logger.error(f"搜索招聘要求失败: {e}")
        return []


def search_open_source_projects(
    query: str,
    industry: Optional[str] = None,
    tech_stack: Optional[str] = None,
    top_k: int = 10
) -> List[dict]:
    """
    实时搜索开源项目（从 GitHub/Gitee API）
    
    Args:
        query: 查询文本（技术栈、项目描述等）
        industry: 行业过滤（暂不支持）
        tech_stack: 技术栈过滤
        top_k: 返回数量
    
    Returns:
        开源项目列表
    """
    try:
        projects = []
        
        # 构建搜索关键词
        search_keywords = tech_stack or query
        
        # 从 GitHub 搜索
        github_projects = _search_github(search_keywords, limit=top_k)
        projects.extend(github_projects)
        
        # 如果还需要更多，从 Gitee 搜索
        if len(projects) < top_k:
            gitee_projects = _search_gitee(search_keywords, limit=top_k - len(projects))
            projects.extend(gitee_projects)
        
        return projects[:top_k]
    
    except Exception as e:
        logger.error(f"搜索开源项目失败: {e}")
        return []


def _search_github(keywords: str, language: Optional[str] = None, limit: int = 10) -> List[dict]:
    """从 GitHub API 搜索项目"""
    try:
        # GitHub Search API: https://api.github.com/search/repositories
        url = "https://api.github.com/search/repositories"
        params = {
            "q": keywords,
            "sort": "stars",
            "order": "desc",
            "per_page": min(limit, 100)  # GitHub API 限制每页最多100
        }
        
        if language:
            params["q"] = f"{keywords} language:{language}"
        
        # 可以添加 token 提高速率限制
        headers = {}
        github_token = getattr(config, "github_token", None)
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        projects = []
        
        for item in data.get("items", [])[:limit]:
            # 获取 README 内容（可选，因为可能比较慢）
            readme_content = _fetch_github_readme(item["full_name"])
            
            projects.append({
                "project_name": item["name"],
                "project_url": item["html_url"],
                "tech_stack": item.get("language", "") or keywords,
                "industry": "",  # GitHub 不提供行业信息
                "description": item.get("description", "")[:500],
                "readme_content": readme_content[:2000] if readme_content else ""
            })
        
        return projects
    
    except Exception as e:
        logger.warning(f"GitHub 搜索失败: {e}")
        return []


def _fetch_github_readme(repo_full_name: str) -> Optional[str]:
    """获取 GitHub 项目的 README 内容"""
    try:
        url = f"https://api.github.com/repos/{repo_full_name}/readme"
        headers = {"Accept": "application/vnd.github.v3.raw"}
        
        github_token = getattr(config, "github_token", None)
        if github_token:
            headers["Authorization"] = f"token {github_token}"
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.text[:2000]  # 限制长度
    except:
        pass
    return None


def _search_gitee(keywords: str, limit: int = 10) -> List[dict]:
    """从 Gitee API 搜索项目"""
    try:
        # Gitee Search API: https://gitee.com/api/v5/search/repositories
        url = "https://gitee.com/api/v5/search/repositories"
        params = {
            "q": keywords,
            "sort": "stars_count",
            "order": "desc",
            "per_page": min(limit, 100),
            "page": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        projects = []
        
        for item in data.get("items", [])[:limit]:
            projects.append({
                "project_name": item.get("name", ""),
                "project_url": item.get("html_url", ""),
                "tech_stack": keywords,  # Gitee API 不直接提供语言信息
                "industry": "",
                "description": item.get("description", "")[:500],
                "readme_content": ""  # Gitee 的 README 需要单独请求，暂时不获取
            })
        
        return projects
    
    except Exception as e:
        logger.warning(f"Gitee 搜索失败: {e}")
        return []


def search_by_resume_requirements(
    job_title: str,
    city: Optional[str] = None,
    salary: Optional[str] = None,
    industry: Optional[str] = None,
    tech_stack: Optional[str] = None,
    job_top_k: int = 5,
    project_top_k: int = 5
) -> dict:
    """
    根据简历要求搜索招聘要求和开源项目
    
    Args:
        job_title: 目标岗位
        city: 期望城市
        salary: 期望薪资
        industry: 目标行业
        tech_stack: 技术栈
        job_top_k: 招聘要求返回数量
        project_top_k: 开源项目返回数量
    
    Returns:
        {
            "job_requirements": [...],
            "open_source_projects": [...]
        }
    """
    # 构建查询文本
    query_text = f"{job_title} {tech_stack or ''}"
    
    # 搜索招聘要求
    job_requirements = search_job_requirements(
        query=query_text,
        city=city,
        salary=salary,
        industry=industry,
        top_k=job_top_k
    )
    
    # 搜索开源项目
    open_source_projects = search_open_source_projects(
        query=query_text,
        industry=industry,
        tech_stack=tech_stack,
        top_k=project_top_k
    )
    
    return {
        "job_requirements": job_requirements,
        "open_source_projects": open_source_projects
    }

