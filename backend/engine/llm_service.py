"""
大模型服务引擎
"""
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from loguru import logger
from backend.core.config import settings
from backend.models.finetune.lora_trainer import LoRATrainer
from sentence_transformers import SentenceTransformer


class LLMService:
    """大模型服务 - 封装OpenAI、DeepSeek等模型"""
    
    def __init__(self):
        self.deepseek_client = None
        self.finetuned_model = None  # LoRA微调模型
        self.local_embedder: Optional[SentenceTransformer] = None
        
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
        use_deepseek: Optional[bool] = True,
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
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            result = await loop.run_in_executor(
                None,
                lambda: self.finetuned_model.generate(prompt, max_length=max_tokens, temperature=temperature)
            )
            return result
        
        client: Optional[AsyncOpenAI] = self.deepseek_client
        model_name: Optional[str] = model or settings.DEEPSEEK_MODEL

        if client is None:
            raise ValueError("未配置DeepSeek API密钥")
        
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
        embeddings: Optional[List[float]] = None

        client: Optional[AsyncOpenAI] = self.deepseek_client
        model_name: Optional[str] = getattr(settings, "DEEPSEEK_EMBED_MODEL", None)

        if client and model_name:
            try:
                response = await client.embeddings.create(
                    model=model_name,
                    input=text,
                )
                embeddings = response.data[0].embedding  # type: ignore[attr-defined]
            except Exception as e:
                logger.warning(f"DeepSeek嵌入生成失败，将回退本地模型: {e}")
        else:
            logger.warning("未配置可用的DeepSeek嵌入模型，使用本地句向量模型")

        if embeddings is not None:
            return embeddings

        # Fallback: local sentence-transformer
        if self.local_embedder is None:
            local_model_name = getattr(settings, "LOCAL_EMBED_MODEL", "shibing624/text2vec-base-chinese")
            logger.info(f"加载本地句向量模型: {local_model_name}")
            self.local_embedder = SentenceTransformer(local_model_name)

        try:
            local_embedding = self.local_embedder.encode(text, normalize_embeddings=True)
            return local_embedding.tolist()
        except Exception as e:  # pragma: no cover
            logger.error(f"本地嵌入模型生成失败: {e}")
            raise

