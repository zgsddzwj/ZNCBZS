"""
LoRA微调训练器
采用LoRA（Low-Rank Adaptation）技术对基础大模型进行金融领域微调
"""
from typing import Optional, Dict, Any, List
from pathlib import Path
import torch
from loguru import logger
from peft import LoraConfig, get_peft_model, TaskType
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from datasets import Dataset


class LoRATrainer:
    """LoRA微调训练器"""
    
    def __init__(
        self,
        base_model_name: str = "Qwen/Qwen-7B-Chat",  # 或使用其他开源模型
        output_dir: str = "./models/financial_llm_lora",
        device: str = "cuda",
    ):
        self.base_model_name = base_model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.device = device
        
        # 初始化模型和tokenizer
        self.tokenizer = None
        self.model = None
        self.peft_model = None
    
    def load_base_model(self):
        """加载基础模型"""
        logger.info(f"加载基础模型: {self.base_model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_name,
            trust_remote_code=True,
        )
        
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # 配置LoRA
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,  # LoRA rank
            lora_alpha=32,  # LoRA scaling parameter
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # 目标模块
        )
        
        self.peft_model = get_peft_model(self.model, lora_config)
        self.peft_model.print_trainable_parameters()
        
        logger.info("基础模型加载完成")
    
    def prepare_training_data(
        self,
        data_path: str,
        max_length: int = 2048,
    ) -> Dataset:
        """
        准备训练数据
        
        数据格式：
        {
            "instruction": "分析以下财报数据...",
            "input": "财报文本...",
            "output": "分析结果..."
        }
        """
        import json
        
        # 加载标注数据（10万+条）
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def format_prompt(example):
            """格式化提示词"""
            if example.get("input"):
                prompt = f"### 指令:\n{example['instruction']}\n\n### 输入:\n{example['input']}\n\n### 回答:\n"
            else:
                prompt = f"### 指令:\n{example['instruction']}\n\n### 回答:\n"
            
            full_text = prompt + example['output']
            return {"text": full_text}
        
        # 格式化数据
        formatted_data = [format_prompt(item) for item in data]
        
        # 创建Dataset
        dataset = Dataset.from_list(formatted_data)
        
        def tokenize_function(examples):
            """分词函数"""
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=max_length,
                padding="max_length",
            )
        
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=["text"],
        )
        
        return tokenized_dataset
    
    def train(
        self,
        train_dataset: Dataset,
        num_epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4,
        save_steps: int = 500,
    ):
        """训练LoRA模型"""
        logger.info("开始LoRA微调训练...")
        
        training_args = TrainingArguments(
            output_dir=str(self.output_dir),
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=4,
            learning_rate=learning_rate,
            fp16=True,
            logging_steps=100,
            save_steps=save_steps,
            save_total_limit=3,
            warmup_steps=100,
            report_to="tensorboard",
        )
        
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )
        
        trainer = Trainer(
            model=self.peft_model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator,
        )
        
        trainer.train()
        
        # 保存模型
        trainer.save_model()
        self.tokenizer.save_pretrained(self.output_dir)
        
        logger.info(f"LoRA模型训练完成，保存至: {self.output_dir}")
    
    def load_finetuned_model(self, model_path: Optional[str] = None):
        """加载微调后的模型"""
        model_path = model_path or str(self.output_dir)
        
        logger.info(f"加载微调模型: {model_path}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
        )
        
        base_model = AutoModelForCausalLM.from_pretrained(
            self.base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        
        from peft import PeftModel
        self.peft_model = PeftModel.from_pretrained(
            base_model,
            model_path,
        )
        
        logger.info("微调模型加载完成")
    
    def generate(
        self,
        prompt: str,
        max_length: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """使用微调模型生成文本"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.peft_model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

