"""
云端OCR服务 - 支持多个OCR提供商
提供比本地Tesseract更准确的文字识别
"""

import base64
import json
import os
import requests
from typing import Optional
import asyncio
import aiohttp

class CloudOCR:
    """云端OCR服务管理器"""
    
    def __init__(self):
        # 阿里云OCR配置
        self.aliyun_access_key = os.getenv('ALIYUN_ACCESS_KEY_ID')
        self.aliyun_access_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
        
        # 百度OCR配置
        self.baidu_api_key = os.getenv('BAIDU_OCR_API_KEY')
        self.baidu_secret_key = os.getenv('BAIDU_OCR_SECRET_KEY')
        
        # 腾讯云OCR配置
        self.tencent_secret_id = os.getenv('TENCENT_SECRET_ID')
        self.tencent_secret_key = os.getenv('TENCENT_SECRET_KEY')

    async def extract_text_from_image(self, image_content: bytes) -> str:
        """
        从图片中提取文字，自动选择最佳的OCR服务
        """
        # 尝试顺序：阿里云 -> 百度 -> 腾讯云 -> 本地Tesseract
        
        # 1. 尝试阿里云OCR
        if self.aliyun_access_key and self.aliyun_access_secret:
            try:
                result = await self._aliyun_ocr(image_content)
                if result:
                    return result
            except Exception as e:
                print(f"阿里云OCR失败: {e}")
        
        # 2. 尝试百度OCR
        if self.baidu_api_key and self.baidu_secret_key:
            try:
                result = await self._baidu_ocr(image_content)
                if result:
                    return result
            except Exception as e:
                print(f"百度OCR失败: {e}")
        
        # 3. 尝试腾讯云OCR
        if self.tencent_secret_id and self.tencent_secret_key:
            try:
                result = await self._tencent_ocr(image_content)
                if result:
                    return result
            except Exception as e:
                print(f"腾讯云OCR失败: {e}")
        
        # 4. 降级到本地Tesseract
        try:
            from .image_parser import extract_text_from_image
            return await extract_text_from_image(image_content)
        except Exception as e:
            raise Exception(f"所有OCR服务都不可用: {e}")

    async def _aliyun_ocr(self, image_content: bytes) -> Optional[str]:
        """阿里云OCR识别"""
        try:
            # 简化版实现，使用通用文字识别API
            url = "https://ocr-api.cn-hangzhou.aliyuncs.com/"
            
            # 将图片转换为base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            # 构建请求（这里简化了签名过程）
            # 实际使用时建议使用阿里云SDK
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "image": image_base64,
                "configure": {
                    "dataType": "string",
                    "language": "zh_cn",
                    "outputProbability": False
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        # 提取文字内容
                        text_lines = []
                        for item in result.get('data', {}).get('content', []):
                            text_lines.append(item.get('text', ''))
                        return '\n'.join(text_lines)
            
            return None
            
        except Exception as e:
            print(f"阿里云OCR错误: {e}")
            return None

    async def _baidu_ocr(self, image_content: bytes) -> Optional[str]:
        """百度OCR识别"""
        try:
            # 1. 获取access_token
            token_url = "https://aip.baidubce.com/oauth/2.0/token"
            token_params = {
                "grant_type": "client_credentials",
                "client_id": self.baidu_api_key,
                "client_secret": self.baidu_secret_key
            }
            
            async with aiohttp.ClientSession() as session:
                # 获取token
                async with session.post(token_url, data=token_params) as response:
                    token_result = await response.json()
                    access_token = token_result.get("access_token")
                
                if not access_token:
                    return None
                
                # 2. 调用OCR API
                ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
                
                # 图片转base64
                image_base64 = base64.b64encode(image_content).decode('utf-8')
                
                ocr_data = {
                    "image": image_base64,
                    "language_type": "CHN_ENG",  # 中英文混合
                    "detect_direction": "true",  # 检测图像朝向
                    "paragraph": "false",       # 是否输出段落信息
                    "probability": "false"      # 是否返回识别结果中每一行的置信度
                }
                
                async with session.post(ocr_url, data=ocr_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # 提取文字
                        text_lines = []
                        for item in result.get('words_result', []):
                            text_lines.append(item.get('words', ''))
                        
                        return '\n'.join(text_lines)
            
            return None
            
        except Exception as e:
            print(f"百度OCR错误: {e}")
            return None

    async def _tencent_ocr(self, image_content: bytes) -> Optional[str]:
        """腾讯云OCR识别"""
        try:
            # 腾讯云OCR实现（简化版）
            # 实际使用建议用腾讯云SDK
            
            url = "https://ocr.tencentcloudapi.com/"
            
            # 图片转base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            # 构建请求数据
            data = {
                "Action": "GeneralBasicOCR",
                "Version": "2018-11-19",
                "Region": "ap-beijing",
                "ImageBase64": image_base64,
                "LanguageType": "zh"
            }
            
            # 这里需要实现腾讯云的签名算法
            # 为简化，暂时返回None，让其降级到其他方案
            return None
            
        except Exception as e:
            print(f"腾讯云OCR错误: {e}")
            return None

    def is_available(self) -> bool:
        """检查是否有可用的云OCR服务"""
        return (
            (self.aliyun_access_key and self.aliyun_access_secret) or
            (self.baidu_api_key and self.baidu_secret_key) or
            (self.tencent_secret_id and self.tencent_secret_key)
        )

    def get_available_services(self) -> list:
        """获取可用的OCR服务列表"""
        services = []
        
        if self.aliyun_access_key and self.aliyun_access_secret:
            services.append("阿里云OCR")
        
        if self.baidu_api_key and self.baidu_secret_key:
            services.append("百度OCR")
            
        if self.tencent_secret_id and self.tencent_secret_key:
            services.append("腾讯云OCR")
            
        # 检查本地Tesseract
        try:
            from .image_parser import is_tesseract_available
            if is_tesseract_available():
                services.append("本地Tesseract")
        except:
            pass
            
        return services

# 创建全局实例
cloud_ocr = CloudOCR()

# 导出函数
async def extract_text_from_image_cloud(image_input) -> str:
    """使用云端OCR提取图片文字
    
    Args:
        image_input: 可以是bytes内容或者文件路径字符串
    """
    if isinstance(image_input, str):
        # 如果是文件路径，读取文件内容
        with open(image_input, 'rb') as f:
            image_content = f.read()
    elif isinstance(image_input, bytes):
        # 如果是bytes内容，直接使用
        image_content = image_input
    else:
        raise ValueError("image_input must be either bytes or str (file path)")
    
    return await cloud_ocr.extract_text_from_image(image_content)

def is_cloud_ocr_available() -> bool:
    """检查云端OCR是否可用"""
    return cloud_ocr.is_available()

def get_ocr_status() -> dict:
    """获取OCR服务状态"""
    return {
        "available_services": cloud_ocr.get_available_services(),
        "cloud_ocr_available": cloud_ocr.is_available(),
        "total_services": len(cloud_ocr.get_available_services())
    }
