"""
数据采集器 - 采集银行财报、宏观经济数据、政策文件
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import aiohttp
import aiofiles
import ssl
import pandas as pd
from loguru import logger
from backend.core.config import settings


class BankReportCollector:
    """银行财报数据采集器"""
    
    def __init__(self):
        self.data_dir = Path("./data/raw/bank_reports")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.A_SHARE_BANKS = settings.A_SHARE_BANKS
        
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
            years = list(range(current_year - settings.DEFAULT_REPORT_YEARS_RANGE + 1, current_year + 1))
        
        if report_types is None:
            report_types = ["annual", "semi_annual", "quarterly"]
        
        collected_reports = []
        
        # 并发采集（限制并发数）
        semaphore = asyncio.Semaphore(settings.COLLECTOR_CONCURRENCY_LIMIT)
        
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
        从巨潮资讯网获取财报信息
        """
        # 巨潮资讯网的查询API
        query_url = settings.CNINFO_QUERY_URL
        
        # 根据报告类型设置查询参数
        report_type_map = {
            "annual": ("category_ndbg_szsh;", f"{year}-01-01", f"{year}-12-31"),
            "semi_annual": ("category_bndbg_szsh;", f"{year}-01-01", f"{year}-08-31"),
            "quarterly_1": ("category_yjdbg_szsh;", f"{year}-01-01", f"{year}-04-30"),
            "quarterly_3": ("category_sjdbg_szsh;", f"{year}-07-01", f"{year}-10-31"),
        }

        query_report_type = report_type
        if report_type == "quarterly": # 简化处理，默认查三季报
            query_report_type = "quarterly_3"

        if query_report_type not in report_type_map:
            logger.warning(f"不支持的报告类型: {report_type}")
            return None

        category, start_date, end_date = report_type_map[query_report_type]
        se_date = f"{start_date}~{end_date}"

        # 构造查询payload，不区分沪深交易所，使用searchkey进行模糊搜索
        payload = {
            "pageNum": 1,
            "pageSize": 10, # 通常第一个就是最新的
            "tabName": "fulltext",
            "searchkey": f"{bank} {year} {report_type_map[query_report_type][0][:4]}报告", # 构造更精确的搜索词
            "seDate": se_date,
            "category": category,
            "isHLtitle": "true"
        }

        headers = {
            'User-Agent': settings.COLLECTOR_USER_AGENT
        }

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(query_url, data=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        announcements = data.get("announcements")
                        if announcements:
                            # 通常第一个是最相关的
                            report = announcements[0]
                            return {
                                "download_url": f"http://static.cninfo.com.cn/{report['adjunctUrl']}",
                                "source": "cninfo",
                                "publish_date": report.get("announcementTime", ""),
                                "title": report.get("announcementTitle", "")
                            }
            logger.warning(f"在巨潮资讯网未找到 {bank} {year} 年 {report_type} 报告")
            return None
        except Exception as e:
            logger.error(f"从巨潮资讯网获取财报信息失败: {e}")
            return None
    
    async def _download_report(self, report_info: Dict[str, Any]) -> str:
        """下载财报文件"""
        download_url = report_info.get("download_url")
        if not download_url:
            return ""

        try:
            # 从URL或标题中提取信息来构建更可靠的文件名
            # 假设 report_info 包含 'title' 字段，如 "招商银行2023年年度报告"
            title = report_info.get("title", "")
            original_filename = download_url.split('/')[-1]
            # 清理标题以用作文件名的一部分
            safe_title = title.replace(':', '：').replace('/', '_').replace('\\', '_')
            filename = f"{safe_title}_{original_filename}" if title else original_filename
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'

            file_path = self.data_dir / filename

            if file_path.exists():
                logger.info(f"文件已存在，跳过下载: {file_path}")
                return str(file_path)

            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, timeout=300) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as f:
                            content = await response.read()
                            await f.write(content)
                        logger.info(f"下载财报成功: {file_path}")
                        return str(file_path)
                    else:
                        logger.warning(f"下载财报失败，状态码: {response.status}, URL: {download_url}")
                        return ""

        except Exception as e:
            logger.error(f"下载财报时发生错误: {e}, URL: {download_url}")
            return ""


class MacroDataCollector:
    """宏观经济数据采集器"""

    def __init__(self):
        self.data_dir = Path("./data/raw/macro_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            'User-Agent': settings.COLLECTOR_USER_AGENT
        }
        # 指标到采集函数的映射
        self.indicator_map = {
            "GDP": self._fetch_stats_gov_data,
            "CPI": self._fetch_stats_gov_data,
            "利率": self._fetch_lpr_data,
            "M2": self._fetch_m2_data,
            "社会融资规模": self._fetch_m2_data,
        }
        # 国家统计局指标参数
        self.stats_gov_params = {
            "GDP": {"dbcode": "hgnd", "wdscode": "zb", "valuecode": "A020101"},  # 年度GDP
            "CPI": {"dbcode": "hgyd", "wdscode": "zb", "valuecode": "A010101"},  # 月度CPI
        }
        # 东方财富宏观指标参数
        self.eastmoney_macro_params = {
            "M2": {
                "reportName": "RPT_MACRO_MONEY_SUPPLY",
                "columns": {
                    "m2_balance": "M2_BALANCE",
                    "m2_yoy": "M2_YOY",
                    "m1_balance": "M1_BALANCE",
                    "m1_yoy": "M1_YOY",
                    "m0_balance": "M0_BALANCE",
                    "m0_yoy": "M0_YOY",
                }
            },
            "社会融资规模": {
                "reportName": "RPT_MACRO_SOCIAL_FINANCE",
                "columns": {
                    "social_finance_scale": "SOCIAL_FINANCE_SCALE",
                    "social_finance_yoy": "SOCIAL_FINANCE_YOY",
                    "rmb_loans": "RMB_LOANS",
                    "rmb_loans_yoy": "RMB_LOANS_YOY",
                }
            }
        }
        # 东方财富宏观指标参数
        self.eastmoney_macro_params = {
            "M2": {
                "reportName": "RPT_MACRO_MONEY_SUPPLY",
                "columns": {
                    "m2_balance": "M2_BALANCE",
                    "m2_yoy": "M2_YOY",
                    "m1_balance": "M1_BALANCE",
                    "m1_yoy": "M1_YOY",
                    "m0_balance": "M0_BALANCE",
                    "m0_yoy": "M0_YOY",
                }
            },
            "社会融资规模": {
                "reportName": "RPT_MACRO_SOCIAL_FINANCE",
                "columns": {
                    "social_finance_scale": "SOCIAL_FINANCE_SCALE",
                    "social_finance_yoy": "SOCIAL_FINANCE_YOY",
                    "rmb_loans": "RMB_LOANS",
                    "rmb_loans_yoy": "RMB_LOANS_YOY",
                }
            }
        }

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
            indicators = settings.MACRO_INDICATORS

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=settings.DEFAULT_MACRO_DATA_DAYS_RANGE)).strftime("%Y-%m-%d")

        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        collected_data_all = []

        for indicator in indicators:
            fetch_func = self.indicator_map.get(indicator)
            if not fetch_func:
                logger.warning(f"暂不支持采集指标: {indicator}，请在 indicator_map 中配置。")
                continue
            try:
                data = await fetch_func(indicator, start_date, end_date)
                if data:
                    filepath = self._save_data_to_csv(indicator, data)
                    logger.info(f"指标 {indicator} 数据已保存至 {filepath}")
                    collected_data_all.append({
                        "indicator": indicator,
                        "file_path": filepath,
                        "records_count": len(data),
                        "collected_at": datetime.now().isoformat(),
                    })
            except Exception as e:
                logger.error(f"采集指标 {indicator} 失败: {e}")

        return collected_data_all

    def _save_data_to_csv(self, indicator: str, data: List[Dict[str, Any]]) -> str:
        """将采集的数据保存到CSV文件"""
        if not data:
            return ""
        
        df = pd.DataFrame(data)
        # 标准化列名
        if 'time' in df.columns:
            df = df.rename(columns={'time': 'date'})

        # 确保 'date' 列是第一列
        if 'date' in df.columns:
            cols = ['date'] + [col for col in df.columns if col != 'date']
            df = df[cols]

        filepath = self.data_dir / f"{indicator}.csv"
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        return str(filepath)

    async def _fetch_stats_gov_data(
        self,
        indicator: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """
        从国家统计局获取指标数据
        """
        base_url = settings.NBS_QUERY_URL
        params = self._build_stats_gov_params(indicator, start_date, end_date)
        if not params:
            logger.warning(f"无法为指标构建查询参数: {indicator}")
            return []

        try:
            # 国家统计局网站可能需要禁用SSL验证
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            async with aiohttp.ClientSession(headers=self.headers, connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(base_url, params=params, timeout=60) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        return self._parse_stats_gov_data(json_data, indicator)
                    else:
                        logger.error(f"采集 {indicator} 数据失败，状态码: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"采集 {indicator} 数据时发生错误: {e}")
            return []

    def _build_stats_gov_params(
        self,
        indicator: str,
        start_date: str,
        end_date: str,
    ) -> Optional[Dict[str, Any]]:
        """构建国家统计局指标查询URL参数"""
        import time
        indicator_params = self.stats_gov_params.get(indicator)
        if not indicator_params:
            return None

        dbcode = indicator_params["dbcode"]
        if dbcode == 'hgnd':  # 年度
            start_str = start_date[:4]
            end_str = end_date[:4]
        elif dbcode == 'hgyd':  # 月度
            start_str = start_date[:7].replace('-', '')
            end_str = end_date[:7].replace('-', '')
        else:
            logger.warning(f"未知的指标频率代码: {dbcode}")
            return None

        return {
            'm': 'QueryData',
            'dbcode': dbcode,
            'rowcode': 'zb',
            'colcode': 'sj',
            'wds': '[]',
            'dfwds': f'[{{"wdcode":"zb","valuecode":"{indicator_params["valuecode"]}"}},{{"wdcode":"sj","valuecode":"{start_str}-{end_str}"}}]',
            'k1': str(int(time.time() * 1000)),
        }

    def _parse_stats_gov_data(
        self,
        raw_data: Any,
        indicator: str,
    ) -> List[Dict[str, Any]]:
        """解析国家统计局返回的指标数据"""
        if raw_data.get("returncode") != 200:
            logger.warning(f"国家统计局API返回错误: {raw_data.get('returntype')}")
            return []

        datanodes = raw_data.get("returndata", {}).get("datanodes", [])
        if not datanodes:
            logger.warning(f"未找到指标 {indicator} 的数据")
            return []

        records = []
        for node in datanodes:
            if node.get("data", {}).get("hasdata"):
                time_code = next((item['valuecode'] for item in node['wds'] if item['wdcode'] == 'sj'), None)
                value = node["data"]["data"]
                if time_code:
                    records.append({"time": time_code, "value": value})
        return records

    async def _fetch_lpr_data(
        self,
        indicator: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """从东方财富网获取LPR数据"""
        logger.info("开始从东方财富网采集LPR数据...")
        url = settings.EASTMONEY_QUERY_URL
        params = {
            "reportName": "RPT_LPR_HIST",
            "columns": "ALL",
            "pageSize": 500, # 获取尽可能多的历史数据
            "sortColumns": "TRADE_DATE",
            "sortTypes": "-1",
        }
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params, timeout=60) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        if not json_data.get("success"):
                            logger.error(f"东方财富LPR接口返回失败: {json_data.get('message')}")
                            return []
                        
                        data = json_data.get("result", {}).get("data", [])
                        if not data:
                            logger.warning("东方财富LPR接口未返回数据")
                            return []

                        records = []
                        for item in data:
                            trade_date = item.get("TRADE_DATE", "").split(" ")[0]
                            # 筛选日期范围
                            if start_date <= trade_date <= end_date:
                                records.append({
                                    "date": trade_date,
                                    "lpr_1y": item.get("LPR1Y"),
                                    "lpr_5y": item.get("LPR5Y"),
                                })
                        return records
                    else:
                        logger.error(f"采集LPR数据失败，状态码: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"采集LPR数据时发生错误: {e}")
            return []

    async def _fetch_m2_data(
        self,
        indicator: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """从东方财富网获取M2、社融等宏观数据"""
        logger.info(f"开始从东方财富网采集 {indicator} 数据...")
        
        param_config = self.eastmoney_macro_params.get(indicator)
        if not param_config:
            logger.error(f"未找到指标 {indicator} 在 eastmoney_macro_params 中的配置")
            return []

        url = settings.EASTMONEY_QUERY_URL
        params = {
            "reportName": param_config["reportName"],
            "columns": "ALL",
            "pageSize": 500, # 获取足够多的数据
            "sortColumns": "REPORT_DATE",
            "sortTypes": "-1",
            "filter": f"(REPORT_DATE>='{start_date}')(REPORT_DATE<='{end_date}')"
        }

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, params=params, timeout=60) as response:
                    if response.status == 200:
                        json_data = await response.json()
                        if not json_data.get("success"):
                            logger.error(f"东方财富 {indicator} 接口返回失败: {json_data.get('message')}")
                            return []
                        
                        data = json_data.get("result", {}).get("data", [])
                        if not data:
                            logger.warning(f"东方财富 {indicator} 接口在指定日期范围内未返回数据")
                            return []

                        records = []
                        for item in data:
                            report_date = item.get("REPORT_DATE", "").split(" ")[0]
                            record = {"date": report_date}
                            for col, key in param_config["columns"].items():
                                record[col] = item.get(key)
                            records.append(record)
                        return records
                    else:
                        logger.error(f"采集 {indicator} 数据失败，状态码: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"采集 {indicator} 数据时发生错误: {e}")
            return []


class PolicyFileCollector:
    """政策文件采集器"""

    def __init__(self):
        self.data_dir = Path("./data/raw/policy_files")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            'User-Agent': settings.COLLECTOR_USER_AGENT
        }
        self.source_map = {
            "gov_cn": {
                "base_url": "http://www.gov.cn",
                "fetch_func": self._fetch_policy_files_from_gov_cn
            }
        }

    async def collect_policy_files(
        self,
        sources: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        采集政策文件

        Args:
            sources: 数据源列表, 对应 source_map 中的key
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        """
        if sources is None:
            sources = settings.POLICY_SOURCES

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=settings.DEFAULT_POLICY_DATA_DAYS_RANGE)).strftime("%Y-%m-%d") # 默认采集近30天

        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        collected_files = []
        semaphore = asyncio.Semaphore(5) # 限制并发下载数

        for source in sources:
            source_config = self.source_map.get(source)
            if not source_config:
                logger.warning(f"未知的政策文件来源: {source}")
                continue
            
            try:
                logger.info(f"开始从 {source} 采集政策文件...")
                fetch_func = source_config["fetch_func"]
                files = await fetch_func(source, start_date, end_date, semaphore)
                collected_files.extend(files)
            except Exception as e:
                logger.error(f"采集 {source} 政策文件失败: {e}")

        logger.info(f"共采集到 {len(collected_files)} 份政策文件。")
        return collected_files

    async def _fetch_policy_files_from_gov_cn(
        self,
        source: str,
        start_date: str,
        end_date: str,
        semaphore: asyncio.Semaphore
    ) -> List[Dict[str, Any]]:
        """从中华人民共和国中央人民政府网站 (www.gov.cn) 采集最新政策文件"""
        from bs4 import BeautifulSoup
        import urllib.parse

        list_url = f"{self.source_map[source]['base_url']}/zhengce/zuixin.htm"
        base_url = self.source_map[source]['base_url']
        
        all_policy_info = []

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(list_url, timeout=60) as response:
                    if response.status != 200:
                        logger.error(f"访问政策列表页面失败: {list_url}, 状态码: {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    policy_links = soup.select(".news_box .list li a")
                    policy_dates = soup.select(".news_box .list li .date")

                    for i, link_tag in enumerate(policy_links):
                        try:
                            policy_date_str = policy_dates[i].text.strip()
                            
                            if not (start_date <= policy_date_str <= end_date):
                                continue

                            title = link_tag.text.strip()
                            relative_url = link_tag['href']
                            if relative_url.startswith('./'):
                                relative_url = relative_url[2:]
                            
                            content_url = urllib.parse.urljoin(f"{base_url}/zhengce/", relative_url)

                            all_policy_info.append({
                                "title": title,
                                "url": content_url,
                                "publish_date": policy_date_str,
                                "source": source,
                            })
                        except IndexError:
                            logger.warning(f"解析政策列表时索引错误，跳过该条目。")
                        except Exception as e:
                            logger.warning(f"解析政策列表条目时出错: {e}")

        except Exception as e:
            logger.error(f"获取政策列表时发生错误: {e}")
            return []

        tasks = [
            self._process_single_policy(semaphore, policy_info)
            for policy_info in all_policy_info
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        downloaded_files = [res for res in results if isinstance(res, dict)]
        return downloaded_files

    async def _process_single_policy(self, semaphore: asyncio.Semaphore, policy_info: Dict) -> Optional[Dict]:
        """获取单个政策的内容并保存"""
        async with semaphore:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                content = await self._fetch_policy_content(session, policy_info["url"])
                if content:
                    policy_info["content"] = content
                    file_path = await self._save_policy_file(policy_info)
                    if file_path:
                        del policy_info["content"]
                        policy_info["file_path"] = file_path
                        policy_info["collected_at"] = datetime.now().isoformat()
                        return policy_info
        return None

    async def _fetch_policy_content(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """获取单个政策页面的正文内容"""
        from bs4 import BeautifulSoup

        try:
            await asyncio.sleep(0.5)
            async with session.get(url, timeout=60) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    content_div = soup.find('div', id='UCAP-CONTENT')
                    if content_div:
                        paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p')]
                        return "\n".join(paragraphs)
                    else:
                        logger.warning(f"在页面 {url} 中未找到ID为 'UCAP-CONTENT' 的内容区域")
                        return None
                else:
                    logger.error(f"获取政策内容失败: {url}, 状态码: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"获取政策内容时发生错误: {url}, 错误: {e}")
            return None

    async def _save_policy_file(self, policy_info: Dict[str, Any]) -> str:
        """将政策内容保存到文件"""
        source = policy_info.get("source", "unknown")
        title = policy_info.get("title", "untitled")
        publish_date = policy_info.get("publish_date", "nodate")
        content = policy_info.get("content", "")

        source_dir = self.data_dir / source
        source_dir.mkdir(parents=True, exist_ok=True)

        safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '：').replace('"', '“').replace('*', '_')
        filename = f"{publish_date}_{safe_title}.txt"
        file_path = source_dir / filename

        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(f"标题: {title}\n")
                await f.write(f"发布日期: {publish_date}\n")
                await f.write(f"来源URL: {policy_info.get('url', '')}\n\n")
                await f.write(content)
            logger.info(f"政策文件已保存: {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"保存政策文件失败: {file_path}, 错误: {e}")
            return ""
                        
            
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

