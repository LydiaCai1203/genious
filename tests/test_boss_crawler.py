"""
Boss 直聘爬虫测试用例
用于爬取 Python 后端开发岗位的 JD 数据
"""
import sys
import os

# 添加项目根目录到 Python 路径，确保可以导入 app 模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import random
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from loguru import logger

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium 未安装，请运行: pip install selenium")


class BossCrawler:
    """Boss 直聘爬虫"""
    
    def __init__(self, headless: bool = False):
        """
        初始化爬虫
        
        Args:
            headless: 是否使用无头模式（不显示浏览器）
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("需要安装 selenium: pip install selenium")
        
        self.driver = None
        self.headless = headless
        self._init_driver()
    
    def _init_driver(self):
        """初始化浏览器驱动"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置 User-Agent
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # 执行脚本隐藏 webdriver 特征
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
        except Exception as e:
            logger.error(f"初始化浏览器驱动失败: {e}")
            logger.info("请确保已安装 Chrome 浏览器和 chromedriver")
            raise
    
    def search_jobs(
        self,
        job_title: str = "Python后端开发",
        city: str = "北京",
        limit: int = 20
    ) -> List[Dict]:
        """
        搜索岗位并获取 JD 列表
        
        Args:
            job_title: 岗位名称
            city: 城市
            limit: 获取数量限制
        
        Returns:
            JD 列表
        """
        logger.info(f"开始搜索: {job_title} in {city}, 目标数量: {limit}")
        
        try:
            # 先访问 Boss 直聘首页（不带搜索参数）
            base_url = "https://www.zhipin.com/web/geek/job"
            logger.info(f"先访问 Boss 直聘首页: {base_url}")
            self.driver.get(base_url)
            time.sleep(10)  # 初次访问等待更久，降低触发风控概率

            self._wait_job_page_ready()

            # 构建搜索 URL
            # Boss 直聘的搜索 URL 格式
            query = quote_plus(job_title)
            search_url = f"https://www.zhipin.com/web/geek/job?query={query}&city={self._get_city_code(city)}"
            logger.info(f"访问搜索页: {search_url}")
            
            self.driver.get(search_url)
            time.sleep(20)  # 降低访问频率，避免频繁触发安全校验

            self._wait_job_page_ready()
            
            # 检查是否需要登录
            if self._check_login_required():
                logger.warning("需要登录，请手动登录后按回车继续...")
                input("登录完成后按回车继续...")
            
            # 滚动加载更多
            job_list = []
            scroll_count = 0
            max_scrolls = 10  # 最多滚动10次
            
            while len(job_list) < limit and scroll_count < max_scrolls:
                # 获取当前页面的岗位列表
                jobs = self._extract_job_list()
                
                for job in jobs:
                    if len(job_list) >= limit:
                        break
                    
                    # 获取详细 JD
                    try:
                        job_detail = self._get_job_detail(job)
                        if job_detail:
                            job_detail["location"] = job.get("location")
                            job_detail["job_url"] = job.get("job_url")

                            if job_detail not in job_list:
                                job_list.append(job_detail)
                                logger.info(f"已获取 {len(job_list)}/{limit} 条 JD: {job_detail.get('job_title', '')}")
                                self._save_job_detail(job_detail)
                                wait_time = random.uniform(30, 60)
                                logger.debug(f"等待 {wait_time:.2f}s 后再请求下一条")
                                time.sleep(wait_time)
                    except Exception as e:
                        logger.warning(f"获取 JD 详情失败: {e}")
                        continue
                
                # 滚动加载更多
                if len(job_list) < limit:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    scroll_count += 1
            
            logger.info(f"共获取 {len(job_list)} 条 JD")
            return job_list
        
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def _wait_job_page_ready(self):
        """等待职位列表页及元素加载"""

        def _page_back_to_jobs(driver):
            current = driver.current_url
            return "web/geek/job" in current or "web/geek/jobs" in current

        try:
            WebDriverWait(self.driver, 30).until(_page_back_to_jobs)
            logger.debug("已通过安全校验，返回职位列表页")
        except TimeoutException:
            logger.warning(f"等待职位列表页超时，当前 URL: {self.driver.current_url}")

        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-card-wrap"))
            )
            logger.debug("职位列表元素加载完成")
        except TimeoutException:
            logger.warning("职位列表元素未及时加载，可能需要手动处理安全验证或登录")
            # 为了兼容手动操作，再额外等待几秒
            time.sleep(5)

    def _get_city_code(self, city: str) -> str:
        """获取城市代码"""
        city_map = {
            "北京": "101010100",
            "上海": "101020100",
            "深圳": "101280600",
            "杭州": "101210100",
            "广州": "101280100",
        }
        return city_map.get(city, "101010100")  # 默认北京
    
    def _check_login_required(self) -> bool:
        """检查是否需要登录"""
        try:
            # 检查是否有登录提示
            login_elements = self.driver.find_elements(By.CLASS_NAME, "login-btn")
            return len(login_elements) > 0
        except:
            return False
    
    def _extract_job_list(self) -> List[Dict]:
        """提取岗位列表"""
        jobs = []
        try:

            # Boss 直聘的岗位列表卡片容器
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-wrap")
            
            for card in job_cards:
                try:
                    job_title_elem = card.find_element(By.CSS_SELECTOR, "a.job-name")
                    salary_elem = card.find_element(By.CSS_SELECTOR, ".job-salary")
                    company_elem = card.find_element(By.CSS_SELECTOR, ".boss-name")
                    location_elem = card.find_element(By.CSS_SELECTOR, ".company-location")

                    job_info = {
                        "job_title": job_title_elem.text.strip(),
                        "company_name": company_elem.text.strip(),
                        "salary": salary_elem.text.strip(),
                        "location": location_elem.text.strip(),
                        "job_url": job_title_elem.get_attribute("href")
                    }
                    jobs.append(job_info)
                except Exception as e:
                    logger.debug(f"提取岗位信息失败: {e}")
                    continue

        except Exception as e:
            logger.warning(f"提取岗位列表失败: {e}")
        
        return jobs
    
    def _get_job_detail(self, job_info: Dict) -> Optional[Dict]:
        """获取岗位详细信息"""
        try:
            job_url = job_info.get("job_url")
            if not job_url:
                return None
            
            # 打开新标签页
            self.driver.execute_script(f"window.open('{job_url}');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(2)  # 等待页面加载
            
            # 提取详细信息
            detail = {
                "city": self._extract_text(By.CSS_SELECTOR, ".job-location, .city"),
                "salary": job_info.get("salary") or self._extract_text(By.CSS_SELECTOR, ".salary, .job-salary"),
                "seniority": self._extract_text(By.CSS_SELECTOR, ".job-experience, .experience"),
                "company_name": job_info.get("company_name") or self._extract_text(By.CSS_SELECTOR, ".company-name"),
                "company_industry": self._extract_text(By.CSS_SELECTOR, ".company-industry, .industry"),
                "company_info": self._extract_text(By.CSS_SELECTOR, ".company-info, .company-desc"),
                "job_title": job_info.get("job_title") or self._extract_text(By.CSS_SELECTOR, ".job-title, .job-name"),
                "job_detail": self._extract_text(By.CSS_SELECTOR, ".job-detail, .job-description, .job-sec-text"),
            }
            
            # 关闭当前标签页，返回原标签页
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return detail
        
        except Exception as e:
            logger.warning(f"获取岗位详情失败: {e}")
            # 确保返回原标签页
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return None
    
    def _extract_text(self, by, selector: str, default: str = "") -> str:
        """提取文本内容"""
        try:
            element = self.driver.find_element(by, selector)
            return element.text.strip()
        except:
            return default

    def _save_job_detail(self, job_detail: Dict):
        """保存职位到 Milvus"""
        try:
            from app.service.data_collector import data_collector

            # 构造符合数据仓库的字段
            record = {
                "city": job_detail.get("city"),
                "salary": job_detail.get("salary"),
                "seniority": job_detail.get("seniority"),
                "company_name": job_detail.get("company_name"),
                "company_industry": job_detail.get("company_industry"),
                "company_info": job_detail.get("company_info"),
                "job_title": job_detail.get("job_title"),
                "job_detail": job_detail.get("job_detail"),
            }

            data_collector.save_job_requirements_to_milvus([record])
            logger.info("已保存职位到 Milvus")
        except Exception as e:
            logger.warning(f"保存职位到 Milvus 失败: {e}")
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()


def test_crawl_python_jobs():
    """测试爬取 Python 后端开发岗位"""
    logger.info("开始测试 Boss 直聘爬虫")
    
    crawler = None
    try:
        # 创建爬虫实例（不使用无头模式，方便观察和手动处理验证码）
        crawler = BossCrawler(headless=False)
        
        # 爬取 Python 后端开发岗位
        jobs = crawler.search_jobs(
            job_title="Python后端开发",
            city="北京",
            limit=10  # 先爬取10条用于测试
        )
        
        logger.info(f"成功爬取 {len(jobs)} 条 JD")
        
        # 打印结果
        for i, job in enumerate(jobs, 1):
            logger.info(f"\n=== JD {i} ===")
            logger.info(f"岗位: {job.get('job_title')}")
            logger.info(f"公司: {job.get('company_name')}")
            logger.info(f"薪资: {job.get('salary')}")
            logger.info(f"城市: {job.get('city')}")
            logger.info(f"经验: {job.get('seniority')}")
            logger.info(f"行业: {job.get('company_industry')}")
            logger.info(f"详情: {job.get('job_detail', '')[:100]}...")
        
        return jobs
    
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        if crawler:
            crawler.close()


if __name__ == "__main__":
    test_crawl_python_jobs()

