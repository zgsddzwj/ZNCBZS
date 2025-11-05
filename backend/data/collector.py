"""
数据采集器 - 采集银行财报、宏观经济数据、政策文件
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import aiohttp
import aiofiles
from loguru import logger
from backend.core.config import settings


class BankReportCollector:
    """银行财报数据采集器"""
    
    # 42家A股上市银行列表
    A_SHARE_BANKS = [
        "工商银行", "建设银行", "农业银行", "中国银行", "交通银行",
        "招商银行", "浦发银行", "兴业银行", "民生银行", "光大银行",
        "华夏银行", "平安银行", "中信银行", "北京银行", "上海银行",
        "江苏银行", "宁波银行", "南京银行", "杭州银行", "成都银行",
        "长沙银行", "西安银行", "贵阳银行", "郑州银行", "青岛银行",
        "苏州银行", "厦门银行", "重庆银行", "齐鲁银行", "兰州银行",
        "瑞丰银行", "常熟银行", "张家港行", "江阴银行", "无锡银行",
        "苏农银行", "紫金银行", "青农商行", "渝农商行", "沪农商行",
        "邮储银行", "浙商银行",
    ]
    
    def __init__(self):
        self.data_dir = Path("./data/raw/bank_reports")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def collect_bank_reports(
        self,
        bank_names: Optional[List[str]] = None,
        years: Optional[List[int]] = None,
        report_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        采集银行财报数据
        
        Args:
            bank_names: 银行名称列表，None表示采集所有银行
            years: 年份列表，None表示采集近10年
            report_types: 报告类型列表（annual, semi_annual, quarterly）
        
        Returns:
            采集到的财报信息列表
        """
        if bank_names is None:
            bank_names = self.A_SHARE_BANKS
        
        if years is None:
            current_year = datetime.now().year
            years = list(range(current_year - 9, current_year + 1))
        
        if report_types is None:
            report_types = ["annual", "semi_annual", "quarterly"]
        
        collected_reports = []
        
        # 并发采集（限制并发数）
        semaphore = asyncio.Semaphore(5)  # 最多5个并发
        
        tasks = []
        for bank in bank_names:
            for year in years:
                for report_type in report_types:
                    task = self._collect_single_report(
                        semaphore, bank, year, report_type
                    )
                    tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                collected_reports.append(result)
            elif isinstance(result, Exception):
                logger.error(f"采集失败: {result}")
        
        logger.info(f"共采集 {len(collected_reports)} 份财报")
        return collected_reports
    
    async def _collect_single_report(
        self,
        semaphore: asyncio.Semaphore,
        bank: str,
        year: int,
        report_type: str,
    ) -> Dict[str, Any]:
        """采集单份财报"""
        async with semaphore:
            try:
                # 这里应该调用实际的财报数据源API
                # 示例：从Wind、同花顺、巨潮资讯网等获取
                report_info = await self._fetch_report_from_source(
                    bank, year, report_type
                )
                
                if report_info:
                    # 保存财报文件
                    file_path = await self._download_report(report_info)
                    
                    return {
                        "bank": bank,
                        "year": year,
                        "report_type": report_type,
                        "file_path": file_path,
                        "source": report_info.get("source", ""),
                        "publish_date": report_info.get("publish_date", ""),
                        "collected_at": datetime.now().isoformat(),
                    }
                
                return None
                
            except Exception as e:
                logger.error(f"采集财报失败 {bank} {year} {report_type}: {e}")
                raise
    
    async def _fetch_report_from_source(
        self,
        bank: str,
        year: int,
        report_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        从数据源获取财报信息
        
        注意：这里需要根据实际数据源实现
        可能的来源：
        1. 巨潮资讯网（cninfo.com.cn）- 官方披露
        2. Wind/同花顺API（需要付费）
        3. 银行官网
        """
        # 示例：从巨潮资讯网获取
        # 实际实现需要解析HTML或调用API
        try:
            async with aiohttp.ClientSession() as session:
                # 构建查询URL（示例）
                url = self._build_query_url(bank, year, report_type)
                
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        # 解析响应，提取财报下载链接
                        # 这里需要根据实际网站结构实现
                        return {
                            "download_url": "",  # 实际下载链接
                            "source": "cninfo",
                            "publish_date": f"{year}-12-31",
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"获取财报信息失败: {e}")
            return None
    
    def _build_query_url(self, bank: str, year: int, report_type: str) -> str:
        """构建查询URL（示例）"""
        # 巨潮资讯网查询URL示例格式
        base_url = "http://www.cninfo.com.cn/new/information/topSearch/query"
        # 实际需要根据网站API调整
        return base_url
    
    async def _download_report(self, report_info: Dict[str, Any]) -> str:
        """下载财报文件"""
        download_url = report_info.get("download_url")
        if not download_url:
            return ""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, timeout=300) as response:
                    if response.status == 200:
                        # 保存文件
                        filename = f"{report_info.get('bank', 'unknown')}_{report_info.get('year', 'unknown')}_{report_info.get('report_type', 'unknown')}.pdf"
                        file_path = self.data_dir / filename
                        
                        async with aiofiles.open(file_path, 'wb') as f:
                            content = await response.read()
                            await f.write(content)
                        
                        return str(file_path)
            
            return ""
            
        except Exception as e:
            logger.error(f"下载财报失败: {e}")
            return ""


class MacroDataCollector:
    """宏观经济数据采集器"""
    
    def __init__(self):
        self.data_dir = Path("./data/raw/macro_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def collect_macro_data(
        self,
        indicators: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        采集宏观经济数据
        
        Args:
            indicators: 指标列表（GDP, 利率, 通胀率, M2等）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
        """
        if indicators is None:
            indicators = ["GDP", "利率", "通胀率", "M2", "社会融资规模"]
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365 * 10)).strftime("%Y-%m-%d")
        
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        collected_data = []
        
        for indicator in indicators:
            try:
                data = await self._fetch_indicator_data(
                    indicator, start_date, end_date
                )
                if data:
                    collected_data.append({
                        "indicator": indicator,
                        "data": data,
                        "start_date": start_date,
                        "end_date": end_date,
                        "collected_at": datetime.now().isoformat(),
                    })
            except Exception as e:
                logger.error(f"采集指标 {indicator} 失败: {e}")
        
        return collected_data
    
    async def _fetch_indicator_data(
        self,
        indicator: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        从数据源获取指标数据
        
        数据源：
        1. 国家统计局API
        2. 央行官网
        3. Wind/同花顺API
        """
        try:
            # 示例：从国家统计局获取
            async with aiohttp.ClientSession() as session:
                # 构建API URL（需要根据实际API调整）
                url = self._build_indicator_url(indicator, start_date, end_date)
                
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_indicator_data(data, indicator)
            
            return []
            
        except Exception as e:
            logger.warning(f"获取指标数据失败: {e}")
            return []
    
    def _build_indicator_url(
        self,
        indicator: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """构建指标查询URL"""
        # 国家统计局API示例
        base_url = "http://data.stats.gov.cn/easyquery.htm"
        # 实际需要根据API文档调整
        return base_url
    
    def _parse_indicator_data(
        self,
        raw_data: Any,
        indicator: str,
    ) -> List[Dict[str, Any]]:
        """解析指标数据"""
        # 根据实际API响应格式解析
        return []


class PolicyFileCollector:
    """政策文件采集器"""
    
    def __init__(self):
        self.data_dir = Path("./data/raw/policy_files")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    async def collect_policy_files(
        self,
        sources: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        采集政策文件
        
        Args:
            sources: 数据源列表（央行, 银保监会, 证监会等）
            start_date: 开始日期
            end_date: 结束日期
        """
        if sources is None:
            sources = ["央行", "银保监会", "证监会", "国家统计局"]
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365 * 2)).strftime("%Y-%m-%d")
        
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        collected_files = []
        
        for source in sources:
            try:
                files = await self._fetch_policy_files(source, start_date, end_date)
                collected_files.extend(files)
            except Exception as e:
                logger.error(f"采集 {source} 政策文件失败: {e}")
        
        return collected_files
    
    async def _fetch_policy_files(
        self,
        source: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """从指定来源获取政策文件"""
        try:
            async with aiohttp.ClientSession() as session:
                # 根据来源构建URL
                url = self._build_policy_url(source, start_date, end_date)
                
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        # 解析政策文件列表
                        files = await self._parse_policy_list(response, source)
                        
                        # 下载文件
                        downloaded_files = []
                        for file_info in files:
                            file_path = await self._download_policy_file(
                                file_info, source
                            )
                            if file_path:
                                downloaded_files.append({
                                    **file_info,
                                    "file_path": file_path,
                                    "collected_at": datetime.now().isoformat(),
                                })
                        
                        return downloaded_files
            
            return []
            
        except Exception as e:
            logger.warning(f"获取政策文件失败: {e}")
            return []
    
    def _build_policy_url(
        self,
        source: str,
        start_date: str,
        end_date: str,
    ) -> str:
        """构建政策文件查询URL"""
        # 根据来源返回不同URL
        urls = {
            "央行": "http://www.pbc.gov.cn/zhengcehuobisi/125207/125213/",
            "银保监会": "http://www.cbirc.gov.cn/cn/view/pages/index/index.html",
            "证监会": "http://www.csrc.gov.cn/pub/newsite/",
        }
        return urls.get(source, "")
    
    async def _parse_policy_list(
        self,
        response: aiohttp.ClientResponse,
        source: str,
    ) -> List[Dict[str, Any]]:
        """解析政策文件列表"""
        # 需要根据实际网站HTML结构解析
        return []
    
    async def _download_policy_file(
        self,
        file_info: Dict[str, Any],
        source: str,
    ) -> str:
        """下载政策文件"""
        download_url = file_info.get("download_url", "")
        if not download_url:
            return ""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, timeout=300) as response:
                    if response.status == 200:
                        filename = f"{source}_{file_info.get('title', 'unknown')}.pdf"
                        file_path = self.data_dir / filename
                        
                        async with aiofiles.open(file_path, 'wb') as f:
                            content = await response.read()
                            await f.write(content)
                        
                        return str(file_path)
            
            return ""
            
        except Exception as e:
            logger.error(f"下载政策文件失败: {e}")
            return ""

