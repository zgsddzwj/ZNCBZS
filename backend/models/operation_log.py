"""
操作日志模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime
from backend.data.database import Base


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=True)
    username = Column(String(100), nullable=True)
    operation = Column(String(50), nullable=False)
    resource = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    ip = Column(String(50), nullable=True)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
