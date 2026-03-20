"""
文件存储服务
支持数据库存储和文件系统存储
"""
import os
import logging
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FileStorageService:
    """文件存储服务"""
    
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.storage_path = Path(settings.STORAGE_PATH)
        
        # 如果启用了文件系统存储，确保目录存在
        if self.storage_type == "filesystem":
            self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        """确保存储目录存在"""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ready: {self.storage_path.absolute()}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {e}")
            raise
    
    def _get_user_dir(self, user_id: int) -> Path:
        """获取用户专属存储目录"""
        user_dir = self.storage_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def save_document(
        self,
        document_id: int,
        user_id: int,
        title: str,
        html_content: str
    ) -> Optional[str]:
        """
        保存文档到文件系统
        
        Args:
            document_id: 文档ID
            user_id: 用户ID
            title: 文档标题
            html_content: HTML内容
        
        Returns:
            文件路径（相对于 storage_path），失败返回 None
        """
        if self.storage_type != "filesystem":
            return None
        
        try:
            # 获取用户目录
            user_dir = self._get_user_dir(user_id)
            
            # 生成文件名：document_{id}_{safe_title}.html
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]  # 限制长度
            filename = f"document_{document_id}_{safe_title or 'untitled'}.html"
            
            # 保存文件
            file_path = user_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 返回相对路径
            relative_path = f"{user_id}/{filename}"
            logger.info(f"Document saved to filesystem: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Failed to save document to filesystem: {e}")
            return None
    
    def read_document(self, file_path: str) -> Optional[str]:
        """
        从文件系统读取文档
        
        Args:
            file_path: 相对路径（如 "123/document_456_title.html"）
        
        Returns:
            HTML 内容，失败返回 None
        """
        if self.storage_type != "filesystem":
            return None
        
        try:
            full_path = self.storage_path / file_path
            
            # 安全检查：确保路径在存储目录内
            if not full_path.resolve().is_relative_to(self.storage_path.resolve()):
                logger.warning(f"Invalid file path (path traversal attempt): {file_path}")
                return None
            
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Failed to read document from filesystem: {e}")
            return None
    
    def delete_document(self, file_path: str) -> bool:
        """
        从文件系统删除文档
        
        Args:
            file_path: 相对路径
        
        Returns:
            是否删除成功
        """
        if self.storage_type != "filesystem":
            return False
        
        try:
            full_path = self.storage_path / file_path
            
            # 安全检查
            if not full_path.resolve().is_relative_to(self.storage_path.resolve()):
                logger.warning(f"Invalid file path (path traversal attempt): {file_path}")
                return False
            
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Document deleted from filesystem: {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete document from filesystem: {e}")
            return False
    
    def get_document_size(self, file_path: str) -> Optional[int]:
        """
        获取文档文件大小
        
        Args:
            file_path: 相对路径
        
        Returns:
            文件大小（字节），失败返回 None
        """
        if self.storage_type != "filesystem":
            return None
        
        try:
            full_path = self.storage_path / file_path
            
            # 安全检查
            if not full_path.resolve().is_relative_to(self.storage_path.resolve()):
                return None
            
            return full_path.stat().st_size if full_path.exists() else None
            
        except Exception as e:
            logger.error(f"Failed to get document size: {e}")
            return None


# 全局文件存储服务实例
file_storage_service = FileStorageService()
