"""
Token 速率限制器 - 简化版
使用简单的令牌桶算法
"""
import time
import threading
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TokenRateLimiter:
    """
    Token 速率限制器 - 简化版
    
    限制规则：1分钟内不超过 max_tokens_per_minute
    使用滑动窗口 + 简单计数
    """
    
    def __init__(self, max_tokens_per_minute: int = 3_000_000, safety_margin: float = 0.9):
        """
        初始化速率限制器
        
        Args:
            max_tokens_per_minute: 每分钟最大 Token 数
            safety_margin: 安全余量
        """
        self.max_tokens = int(max_tokens_per_minute * safety_margin)
        self.window_seconds = 60
        
        # 使用列表记录 (timestamp, tokens)
        self._records = []
        self._lock = threading.Lock()
        
        logger.info(f"TokenRateLimiter initialized: max_tokens={self.max_tokens}")
    
    def _clean_old_records(self):
        """清理过期的记录"""
        cutoff = time.time() - self.window_seconds
        self._records = [(t, n) for t, n in self._records if t > cutoff]
    
    def get_current_usage(self) -> int:
        """获取当前窗口内的 Token 使用量"""
        with self._lock:
            self._clean_old_records()
            return sum(n for _, n in self._records)
    
    def acquire(self, estimated_tokens: int, timeout: Optional[float] = None) -> bool:
        """
        尝试获取 Token 配额
        
        Args:
            estimated_tokens: 估计需要的 Token 数
            timeout: 最大等待时间（秒）
            
        Returns:
            是否成功获取配额
        """
        start_time = time.time()
        
        while True:
            with self._lock:
                self._clean_old_records()
                current_usage = sum(n for _, n in self._records)
                available = self.max_tokens - current_usage
                
                if available >= estimated_tokens:
                    # 配额充足，直接获取
                    self._records.append((time.time(), estimated_tokens))
                    logger.debug(f"Acquired {estimated_tokens} tokens, current: {current_usage + estimated_tokens}")
                    return True
                
                # 配额不足，计算需要等待多久
                # 找到最早的记录，等待它过期
                if self._records:
                    earliest_time = min(t for t, _ in self._records)
                    wait_time = (earliest_time + self.window_seconds) - time.time()
                    wait_time = max(0.1, wait_time)  # 至少等待 0.1 秒
                else:
                    wait_time = 1.0
            
            # 检查超时
            elapsed = time.time() - start_time
            if timeout is not None and elapsed >= timeout:
                logger.warning(f"Token acquisition timeout after {elapsed:.1f}s")
                return False
            
            # 等待（但不超过剩余超时时间）
            sleep_time = min(wait_time, 1.0)
            if timeout is not None:
                sleep_time = min(sleep_time, timeout - elapsed)
            
            if sleep_time > 0.5:  # 只有等待时间较长才打日志
                logger.info(f"Rate limit: waiting {sleep_time:.1f}s for {estimated_tokens} tokens")
            
            time.sleep(max(0.1, sleep_time))
    
    def record_actual_usage(self, actual_tokens: int):
        """
        记录实际使用的 Token 数，释放差额
        """
        with self._lock:
            if self._records:
                last_time, last_tokens = self._records[-1]
                if actual_tokens < last_tokens:
                    self._records[-1] = (last_time, actual_tokens)
                    saved = last_tokens - actual_tokens
                    logger.info(f"Token usage corrected: {last_tokens} -> {actual_tokens} (saved {saved})")
    
    def get_status(self) -> dict:
        """获取当前状态"""
        with self._lock:
            self._clean_old_records()
            usage = sum(n for _, n in self._records)
            return {
                "max_tokens": self.max_tokens,
                "current_usage": usage,
                "available": self.max_tokens - usage,
                "usage_percent": round(usage / self.max_tokens * 100, 2),
                "records_count": len(self._records)
            }


# 全局速率限制器实例
token_rate_limiter = TokenRateLimiter(
    max_tokens_per_minute=3_000_000,
    safety_margin=0.9
)
