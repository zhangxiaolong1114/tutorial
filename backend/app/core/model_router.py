"""
AI 模型配置与路由系统
支持多模型配置、动态路由、用户级模型选择
"""
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """模型提供商枚举"""
    MOONSHOT = "moonshot"      # Kimi / Moonshot
    ANTHROPIC = "anthropic"    # Claude
    DEEPSEEK = "deepseek"      # DeepSeek
    OPENAI = "openai"          # OpenAI
    QWEN = "qwen"              # 通义千问
    GLM = "glm"                # 智谱 GLM
    CUSTOM = "custom"          # 自定义 OpenAI 兼容接口


class GenerationTask(str, Enum):
    """生成任务类型"""
    OUTLINE = "outline"           # 大纲生成
    SECTION = "section"           # 章节内容生成
    SIMULATION = "simulation"     # 交互仿真生成
    IMAGE = "image"


@dataclass
class ModelConfig:
    """模型配置数据类"""
    id: str                              # 唯一标识，如 "kimi-k2.5"
    name: str                            # 显示名称，如 "Kimi K2.5"
    provider: ModelProvider              # 提供商
    model_id: str                        # API 模型ID，如 "kimi-k2.5"
    api_key: str = ""                    # API Key
    base_url: str = ""                   # 自定义 Base URL（可选）
    
    # 模型能力配置
    supports_temperature: bool = True     # 是否支持 temperature 参数
    default_temperature: float = 0.7     # 默认 temperature
    max_tokens: int = 8192               # 最大输出 tokens
    supports_system_prompt: bool = True  # 是否支持 system prompt
    
    # 成本与性能（用于排序/推荐）
    input_price_per_1k: float = 0.0      # 输入价格（元/千 tokens）
    output_price_per_1k: float = 0.0     # 输出价格（元/千 tokens）
    speed_score: int = 3                 # 速度评分 1-5
    quality_score: int = 3               # 质量评分 1-5
    
    # 功能标记
    is_default: bool = False             # 是否为默认模型
    is_enabled: bool = True              # 是否启用
    is_premium: bool = False             # 是否为会员专属
    supported_tasks: List[GenerationTask] = field(default_factory=list)  # 支持的任务类型
    
    def to_dict(self) -> dict:
        """转换为字典（用于前端展示，隐藏敏感信息）"""
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider.value,
            "model_id": self.model_id,
            "supports_temperature": self.supports_temperature,
            "default_temperature": self.default_temperature,
            "max_tokens": self.max_tokens,
            "input_price_per_1k": self.input_price_per_1k,
            "output_price_per_1k": self.output_price_per_1k,
            "speed_score": self.speed_score,
            "quality_score": self.quality_score,
            "is_default": self.is_default,
            "is_enabled": self.is_enabled,
            "is_premium": self.is_premium,
            "supported_tasks": [t.value for t in self.supported_tasks],
        }


@dataclass
class TaskModelConfig:
    """任务级别的模型配置（用户可自定义）"""
    task: GenerationTask
    model_id: str           # 使用的模型ID
    temperature: float = 0.7
    custom_prompt_suffix: str = ""  # 自定义 Prompt 后缀
    
    def to_dict(self) -> dict:
        return {
            "task": self.task.value,
            "model_id": self.model_id,
            "temperature": self.temperature,
            "custom_prompt_suffix": self.custom_prompt_suffix,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TaskModelConfig":
        return cls(
            task=GenerationTask(data["task"]),
            model_id=data["model_id"],
            temperature=data.get("temperature", 0.7),
            custom_prompt_suffix=data.get("custom_prompt_suffix", ""),
        )


class ModelRegistry:
    """模型注册中心 - 管理所有可用模型"""
    
    def __init__(self):
        self._models: Dict[str, ModelConfig] = {}
        self._load_default_models()
    
    def _load_default_models(self):
        """加载默认模型配置（基础定义，实际 API Key 从环境/数据库加载）"""
        
        # Kimi / Moonshot 系列
        self.register(ModelConfig(
            id="kimi-k2.5",
            name="Kimi K2.5",
            provider=ModelProvider.MOONSHOT,
            model_id="kimi-k2.5",
            supports_temperature=False,
            default_temperature=1.0,
            max_tokens=8192,  # 仿真任务使用较小值，分块生成更快
            input_price_per_1k=0.004,
            output_price_per_1k=0.021,
            speed_score=4,
            quality_score=5,
            is_default=True,
            supported_tasks=[GenerationTask.OUTLINE, GenerationTask.SECTION, GenerationTask.SIMULATION],
        ))
        
        # DeepSeek 系列
        self.register(ModelConfig(
            id="deepseek-reasoner",
            name="deepseek-reasoner",
            provider=ModelProvider.DEEPSEEK,
            model_id="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
            supports_temperature=True,
            default_temperature=0.7,
            max_tokens=8192,
            input_price_per_1k=0.002,
            output_price_per_1k=0.003,
            speed_score=4,
            quality_score=5,
            supported_tasks=[GenerationTask.OUTLINE, GenerationTask.SECTION, GenerationTask.SIMULATION],
        ))
        
        self.register(ModelConfig(
            id="deepseek-chat",
            name="deepseek-chat",
            provider=ModelProvider.DEEPSEEK,
            model_id="deepseek-reasoner",
            base_url="https://api.deepseek.com/v1",
            supports_temperature=True,
            default_temperature=0.7,
            max_tokens=8192,
            input_price_per_1k=0.002,
            output_price_per_1k=0.003,
            speed_score=3,
            quality_score=5,
            supported_tasks=[GenerationTask.OUTLINE, GenerationTask.SECTION],
        ))
        
        # 通义千问系列
        self.register(ModelConfig(
            id="Qwen-3.5-Plus",
            name="Qwen 3.5 Plus",
            provider=ModelProvider.QWEN,
            model_id="qwen3.5-plus",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            supports_temperature=True,
            default_temperature=0.7,
            max_tokens=8192,
            input_price_per_1k=0.0008,
            output_price_per_1k=0.0048,
            speed_score=4,
            quality_score=4,
            supported_tasks=[GenerationTask.OUTLINE, GenerationTask.SECTION, GenerationTask.SIMULATION],
        ))
        
        self.register(ModelConfig(
            id="qwen-image-2.0",
            name="qwen image 2.0",
            provider=ModelProvider.QWEN,
            model_id="qwen-image-2.0",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            supports_temperature=True,
            default_temperature=2,
            max_tokens=8192,
            input_price_per_1k=0,
            output_price_per_1k=0.2,
            speed_score=5,
            quality_score=4,
            supported_tasks=[GenerationTask.IMAGE],
        ))

        self.register(ModelConfig(
            id="MiniMax-M2.5",
            name="MiniMax-M2.5",
            provider=ModelProvider.QWEN,
            model_id="MiniMax-M2.5",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            supports_temperature=True,
            default_temperature=2,
            max_tokens=8192,
            input_price_per_1k=0.0021,
            output_price_per_1k=0.0084,
            speed_score=5,
            quality_score=4,
            supported_tasks=[GenerationTask.OUTLINE, GenerationTask.SECTION, GenerationTask.SIMULATION],
        ))
        
        # 智谱 GLM 系列
        self.register(ModelConfig(
            id="glm-5",
            name="GLM-5",
            provider=ModelProvider.GLM,
            model_id="glm-5",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            supports_temperature=True,
            default_temperature=0.7,
            max_tokens=8192,
            input_price_per_1k=0.004,
            output_price_per_1k=0.018,
            speed_score=4,
            quality_score=4,
            supported_tasks=[GenerationTask.OUTLINE, GenerationTask.SECTION],
        ))
        

    
    def register(self, config: ModelConfig):
        """注册模型"""
        self._models[config.id] = config
        logger.info(f"[ModelRegistry] 注册模型: {config.id} ({config.name})")
    
    def unregister(self, model_id: str):
        """注销模型"""
        if model_id in self._models:
            del self._models[model_id]
            logger.info(f"[ModelRegistry] 注销模型: {model_id}")
    
    def get(self, model_id: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self._models.get(model_id)
    
    def list_all(self, enabled_only: bool = True) -> List[ModelConfig]:
        """列出所有模型"""
        models = list(self._models.values())
        if enabled_only:
            models = [m for m in models if m.is_enabled]
        return models
    
    def list_by_task(self, task: GenerationTask, enabled_only: bool = True) -> List[ModelConfig]:
        """列出支持特定任务的模型"""
        models = self.list_all(enabled_only)
        return [m for m in models if task in m.supported_tasks]
    
    def get_default(self, task: Optional[GenerationTask] = None) -> Optional[ModelConfig]:
        """获取默认模型"""
        # 先找任务特定的默认模型
        if task:
            for model in self._models.values():
                if model.is_default and model.is_enabled and task in model.supported_tasks:
                    return model
        
        # 再找全局默认
        for model in self._models.values():
            if model.is_default and model.is_enabled:
                return model
        
        # 最后返回第一个启用的
        enabled = [m for m in self._models.values() if m.is_enabled]
        return enabled[0] if enabled else None
    
    def update_api_key(self, model_id: str, api_key: str):
        """更新模型 API Key"""
        if model_id in self._models:
            self._models[model_id].api_key = api_key
            logger.info(f"[ModelRegistry] 更新 {model_id} 的 API Key")
    
    def update_base_url(self, model_id: str, base_url: str):
        """更新模型 Base URL"""
        if model_id in self._models:
            self._models[model_id].base_url = base_url
            logger.info(f"[ModelRegistry] 更新 {model_id} 的 Base URL: {base_url}")


# 全局模型注册中心
model_registry = ModelRegistry()


class ModelRouter:
    """模型路由器 - 根据配置选择合适的模型并调用"""
    
    def __init__(self, registry: ModelRegistry = None):
        self.registry = registry or model_registry
        self._callers: Dict[ModelProvider, Callable] = {}
    
    def register_caller(self, provider: ModelProvider, caller: Callable):
        """注册模型调用器"""
        self._callers[provider] = caller
        logger.info(f"[ModelRouter] 注册调用器: {provider.value}")
    
    def route(
        self,
        task: GenerationTask,
        messages: List[Dict[str, str]],
        model_id: Optional[str] = None,
        temperature: Optional[float] = None,
        task_config: Optional[TaskModelConfig] = None,
        **kwargs
    ) -> Tuple[str, str]:
        """
        路由到合适的模型并调用
        
        Args:
            task: 任务类型
            messages: 对话消息列表
            model_id: 指定模型ID（优先级最高）
            temperature: 温度参数
            task_config: 任务级别的模型配置
            **kwargs: 额外参数
            
        Returns:
            (content, log_file_path)
        """
        # 确定使用的模型
        config = None
        if model_id:
            config = self.registry.get(model_id)
            if not config:
                # 尝试大小写不敏感匹配
                for m in self.registry.list_all(enabled_only=False):
                    if m.id.lower() == model_id.lower():
                        config = m
                        logger.warning(f"[ModelRouter] 模型ID大小写不匹配: 请求={model_id}, 匹配={m.id}")
                        break
            if config:
                logger.info(f"[ModelRouter] 使用指定模型: {model_id} -> {config.id}")
            else:
                logger.warning(f"[ModelRouter] 模型不存在: {model_id}")
        elif task_config:
            config = self.registry.get(task_config.model_id)
            logger.info(f"[ModelRouter] 使用task_config模型: {task_config.model_id}")
        
        if not config:
            config = self.registry.get_default(task)
            logger.info(f"[ModelRouter] 使用默认模型: {config.id if config else 'None'}")
        
        if not config:
            raise ValueError(f"没有找到可用的模型来处理任务: {task.value}")
        
        if not config.is_enabled:
            raise ValueError(f"模型 {config.id} 已禁用")
        
        if task not in config.supported_tasks:
            raise ValueError(f"模型 {config.id} 不支持任务类型: {task.value}")
        
        # 确定温度参数
        if temperature is not None:
            final_temp = temperature
        elif task_config:
            final_temp = task_config.temperature
        else:
            final_temp = config.default_temperature
        
        if not config.supports_temperature:
            final_temp = None
        
        # 获取调用器
        caller = self._callers.get(config.provider)
        if not caller:
            raise ValueError(f"未找到 {config.provider.value} 的调用器")
        
        logger.info(f"[ModelRouter] 任务 {task.value} 路由到模型: {config.id}")
        
        # 调用模型
        return caller(
            config=config,
            messages=messages,
            temperature=final_temp,
            task=task,
            **kwargs
        )
    
    def get_available_models(self, task: Optional[GenerationTask] = None) -> List[dict]:
        """获取可用模型列表（用于前端展示）"""
        if task:
            models = self.registry.list_by_task(task)
        else:
            models = self.registry.list_all()
        
        return [m.to_dict() for m in models]


# 全局模型路由器
model_router = ModelRouter()
