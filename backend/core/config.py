"""
应用配置管理
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "智能财报助手"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # 服务地址
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # 大模型配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    DEEPSEEK_API_KEY: str = "sk-a9323e658d5344dbbb09573ba9792459"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_EMBED_MODEL: str = "deepseek-embedding"
    LOCAL_EMBED_MODEL: str = "shibing624/text2vec-base-chinese"
    
    # 知识图谱数据库 (Neo4j)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4j123456"
    
    # 向量数据库 (Milvus)
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "financial_reports"
    
    # 缓存 (Redis)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/zncbzs.db"
    
    # 文件存储
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    
    # 安全配置
    JWT_SECRET_KEY: str = "dev-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # 性能配置
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT: int = 30
    CACHE_ENABLED: bool = True
    
    # OCR配置
    TESSERACT_CMD: str = "/usr/bin/tesseract"
    OCR_LANG: str = "chi_sim+eng"

    # 数据采集配置
    A_SHARE_BANKS: List[str] = [
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
    MACRO_INDICATORS: List[str] = ["GDP", "利率", "通胀率", "M2", "社会融资规模"]
    POLICY_SOURCES: List[str] = ["央行", "银保监会", "证监会", "国家统计局"]

    # 数据清洗配置
    INDICATOR_MAPPING: dict = {
        "营业收入": "营收",
        "营业收入合计": "营收",
        "净利润": "净利润",
        "归属于母公司所有者的净利润": "净利润",
        "总资产": "总资产",
        "总负债": "总负债",
        "不良贷款率": "不良率",
        "拨备覆盖率": "拨备覆盖率",
        "资本充足率": "资本充足率",
        "核心一级资本充足率": "核心一级资本充足率",
        "净资产收益率": "ROE",
        "资产收益率": "ROA",
    }
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例）"""
    return Settings()


settings = get_settings()

