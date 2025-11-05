"""
大模型服务引擎
"""
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from loguru import logger
from backend.core.config import settings
from backend.models.finetune.lora_trainer import LoRATrainer


class LLMService:
    """大模型服务 - 封装OpenAI、DeepSeek等模型"""
    
    def __init__(self):
        self.openai_client = None
        self.deepseek_client = None
        self.finetuned_model = None  # LoRA微调模型
        
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
            )
        
        if settings.DEEPSEEK_API_KEY:
            self.deepseek_client = AsyncOpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
            )
        
        # 尝试加载微调模型
        try:
            from pathlib import Path
            model_path = Path("./models/financial_llm_lora")
            if model_path.exists():
                self.lora_trainer = LoRATrainer()
                self.lora_trainer.load_finetuned_model(str(model_path))
                self.finetuned_model = self.lora_trainer
                logger.info("LoRA微调模型加载成功")
        except Exception as e:
            logger.warning(f"LoRA微调模型加载失败: {e}")
            self.finetuned_model = None
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
        use_deepseek: bool = False,
        use_finetuned: bool = False,
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 用户提示
            model: 模型名称（可选）
            temperature: 温度参数
            max_tokens: 最大token数
            system_prompt: 系统提示
            use_deepseek: 是否使用DeepSeek（用于长文本处理）
            use_finetuned: 是否使用LoRA微调模型
        """
        # 优先使用微调模型（如果是金融领域问题）
        if use_finetuned and self.finetuned_model:
            # LoRA模型是同步的，需要包装为异步
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.finetuned_model.generate(prompt, max_length=max_tokens, temperature=temperature)
            )
            return result
        
        client = self.deepseek_client if use_deepseek else self.openai_client
        
        if client is None:
            raise ValueError("未配置大模型API密钥")
        
        model_name = model or (
            settings.DEEPSEEK_MODEL if use_deepseek else settings.OPENAI_MODEL
        )
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"大模型生成失败: {e}")
            raise
    
    async def generate_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs,
    ) -> str:
        """带重试的生成"""
        for attempt in range(max_retries):
            try:
                return await self.generate(prompt, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"生成失败，重试 {attempt + 1}/{max_retries}: {e}")
                import asyncio
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("生成失败，已重试所有次数")
    
    async def embed(self, text: str) -> list:
        """
        生成文本嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表
        """
        # 使用OpenAI的embedding模型
        if self.openai_client is None:
            raise ValueError("未配置OpenAI API密钥")
        
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise

