"""
语音交互服务 - 语音识别和合成
"""
from typing import Optional
import speech_recognition as sr
import pyttsx3
import io
from loguru import logger
from backend.engine.llm_service import LLMService


class VoiceService:
    """语音服务 - 支持普通话、粤语"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.llm_service = LLMService()
        
        # 配置TTS引擎
        self.tts_engine.setProperty('rate', 150)  # 语速
        self.tts_engine.setProperty('volume', 0.8)  # 音量
    
    async def recognize_speech(
        self,
        audio_data: bytes,
        language: str = "zh-CN",  # 普通话
    ) -> str:
        """
        语音识别
        
        Args:
            audio_data: 音频数据（WAV格式）
            language: 语言代码
                - zh-CN: 普通话
                - zh-HK: 粤语
                - en-US: 英语
        
        Returns:
            识别的文本
        """
        try:
            # 使用Google Speech Recognition（需要网络）
            # 实际部署时可以使用百度、讯飞等国内服务
            audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
            
            try:
                text = self.recognizer.recognize_google(audio, language=language)
                logger.info(f"语音识别成功: {text}")
                return text
            except sr.UnknownValueError:
                logger.warning("无法识别语音")
                return ""
            except sr.RequestError as e:
                logger.error(f"语音识别服务错误: {e}")
                # 备用方案：使用本地模型或离线识别
                return ""
                
        except Exception as e:
            logger.error(f"语音识别失败: {e}")
            return ""
    
    async def text_to_speech(
        self,
        text: str,
        language: str = "zh-CN",
    ) -> bytes:
        """
        文本转语音
        
        Args:
            text: 要转换的文本
            language: 语言代码
        
        Returns:
            音频数据（WAV格式）
        """
        try:
            # 设置语言
            if language == "zh-CN":
                self.tts_engine.setProperty('voice', 'chinese')
            elif language == "zh-HK":
                self.tts_engine.setProperty('voice', 'cantonese')
            
            # 生成语音（保存到内存）
            audio_buffer = io.BytesIO()
            self.tts_engine.save_to_file(text, "temp_audio.wav")
            self.tts_engine.runAndWait()
            
            # 读取生成的音频文件
            with open("temp_audio.wav", "rb") as f:
                audio_data = f.read()
            
            return audio_data
            
        except Exception as e:
            logger.error(f"语音合成失败: {e}")
            return b""
    
    async def process_voice_query(
        self,
        audio_data: bytes,
        language: str = "zh-CN",
    ) -> dict:
        """
        处理语音查询（识别 -> 处理 -> 合成）
        
        Returns:
            {
                "text": "识别的文本",
                "response": "回答文本",
                "audio": "回答音频数据（base64编码）"
            }
        """
        try:
            # 1. 语音识别
            text = await self.recognize_speech(audio_data, language)
            
            if not text:
                return {
                    "text": "",
                    "response": "抱歉，无法识别您的语音，请重试。",
                    "audio": None,
                }
            
            # 2. 处理查询（使用对话服务）
            from backend.engine.coordinator import Coordinator
            coordinator = Coordinator()
            result = await coordinator.process_query(text)
            response_text = result["answer"]
            
            # 3. 语音合成
            response_audio = await self.text_to_speech(response_text, language)
            
            import base64
            audio_base64 = base64.b64encode(response_audio).decode() if response_audio else None
            
            return {
                "text": text,
                "response": response_text,
                "audio": audio_base64,
            }
            
        except Exception as e:
            logger.error(f"语音查询处理失败: {e}")
            return {
                "text": "",
                "response": "处理语音查询时出现错误，请重试。",
                "audio": None,
            }

