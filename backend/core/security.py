"""
安全模块 - 加密、IP白名单、操作日志
"""
from typing import Optional, List
from datetime import datetime
from cryptography.fernet import Fernet
from fastapi import Request, HTTPException
from loguru import logger
import hashlib
import json
from backend.core.config import settings

# AES-256加密（使用Fernet，基于AES-128，但可以扩展）
_encryption_key: Optional[bytes] = None


def get_encryption_key() -> bytes:
    """获取加密密钥"""
    global _encryption_key
    if _encryption_key is None:
        # 从配置或环境变量获取密钥
        key_str = settings.SECRET_KEY
        # 生成32字节密钥
        key = hashlib.sha256(key_str.encode()).digest()
        # Fernet需要base64编码的32字节密钥
        from base64 import urlsafe_b64encode
        _encryption_key = urlsafe_b64encode(key)
    return _encryption_key


def encrypt_data(data: str) -> str:
    """加密敏感数据"""
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(data.encode())
    return encrypted.decode()


def decrypt_data(encrypted_data: str) -> str:
    """解密敏感数据"""
    f = Fernet(get_encryption_key())
    decrypted = f.decrypt(encrypted_data.encode())
    return decrypted.decode()


class IPWhitelist:
    """IP白名单管理"""
    
    def __init__(self):
        self.allowed_ips: List[str] = []
        self.enabled = False  # 默认关闭，需要时启用
    
    def add_ip(self, ip: str):
        """添加允许的IP"""
        if ip not in self.allowed_ips:
            self.allowed_ips.append(ip)
    
    def remove_ip(self, ip: str):
        """移除IP"""
        if ip in self.allowed_ips:
            self.allowed_ips.remove(ip)
    
    def is_allowed(self, ip: str) -> bool:
        """检查IP是否允许"""
        if not self.enabled:
            return True  # 未启用时允许所有IP
        return ip in self.allowed_ips or ip.startswith("127.0.0.1") or ip.startswith("::1")


# 全局IP白名单实例
ip_whitelist = IPWhitelist()


def get_client_ip(request: Request) -> str:
    """获取客户端IP"""
    if request.client:
        return request.client.host
    return "unknown"


def check_ip_whitelist(request: Request):
    """检查IP白名单（中间件用）"""
    if ip_whitelist.enabled:
        client_ip = get_client_ip(request)
        if not ip_whitelist.is_allowed(client_ip):
            logger.warning(f"IP白名单拒绝: {client_ip}")
            raise HTTPException(
                status_code=403,
                detail="IP地址不在白名单中"
            )


class OperationLogger:
    """操作日志记录器"""
    
    def __init__(self):
        self.log_file = "logs/operations.log"
    
    def log(
        self,
        user_id: str,
        username: str,
        operation: str,
        resource: str,
        details: Optional[dict] = None,
        ip: Optional[str] = None,
        success: bool = True,
    ):
        """记录操作日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "username": username,
            "operation": operation,  # 如：login, query, generate_report
            "resource": resource,  # 如：/api/v1/chat/query
            "details": details or {},
            "ip": ip,
            "success": success,
        }
        
        # 写入日志文件（保留至少1年）
        logger.info(f"操作日志: {json.dumps(log_entry, ensure_ascii=False)}")
        
        # 同时保存到数据库（如果需要）
        # TODO: 实现数据库存储


# 全局操作日志实例
operation_logger = OperationLogger()


def log_operation(
    operation: str,
    resource: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    details: Optional[dict] = None,
    ip: Optional[str] = None,
    success: bool = True,
):
    """记录操作的便捷函数"""
    operation_logger.log(
        user_id=user_id or "anonymous",
        username=username or "anonymous",
        operation=operation,
        resource=resource,
        details=details,
        ip=ip,
        success=success,
    )

