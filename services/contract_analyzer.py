"""
合同分析服务 - 说人话的法律助手
"""

import json
import os
from typing import Dict, List, Any
from pydantic import BaseModel
from openai import OpenAI

class RiskItem(BaseModel):
    title: str
    description: str
    level: str  # 高风险、中风险、低风险
    clause_reference: str = ""

class PlainExplanation(BaseModel):
    clause_title: str
    original_text: str
    plain_explanation: str

class Suggestion(BaseModel):
    title: str
    content: str
    priority: str = "中等"

class ContractSummary(BaseModel):
    contract_type: str
    overall_risk: str
    key_points: str
    parties_involved: List[str] = []

class ContractAnalysis(BaseModel):
    contract_summary: ContractSummary
    risks: List[RiskItem]
    plain_explanations: List[PlainExplanation]
    suggestions: List[Suggestion]

async def analyze_contract(contract_text: str, contract_type: str, context: str, api_key: str) -> Dict[str, Any]:
    """
    分析合同内容，识别风险并提供通俗解释
    """
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    # 构建专业的合同分析提示词
    system_message = """你是一位经验丰富的法律顾问和合同专家，专门帮助普通人理解复杂的法律文件。你的任务是：

1. **专业背景**：
   - 拥有15年法律从业经验
   - 专精合同法、消费者权益保护法
   - 擅长用通俗易懂的语言解释法律条款
   - 站在普通人的角度，保护他们的合法权益

2. **分析原则**：
   - 仔细识别对普通人不利的条款
   - 重点关注隐藏的风险和陷阱
   - 用大白话解释复杂的法律术语
   - 提供实用的应对建议和谈判策略

3. **风险等级定义**：
   - **高风险**：可能造成重大经济损失或法律后果的条款
   - **中风险**：可能影响权益但后果相对较轻的条款  
   - **低风险**：需要注意但影响较小的条款

4. **输出要求**：
   - 语言通俗易懂，避免过多法律术语
   - 重点突出，条理清晰
   - 提供具体可操作的建议
   - 保持客观中立，但偏向保护普通人权益"""

    # 根据合同类型定制分析重点
    contract_focus = get_contract_focus(contract_type)
    
    user_prompt = f"""请分析以下{get_contract_type_name(contract_type)}，重点关注{contract_focus}。

**合同内容：**
{contract_text}

**用户补充说明：**
{context if context else "无特别说明"}

**分析要求：**
1. 识别合同类型和基本信息
2. 找出所有潜在风险点，特别是对普通人不利的条款
3. 用通俗语言解释复杂条款的真实含义
4. 提供具体的建议和应对策略

请严格按照以下JSON格式输出分析结果：

{{
    "contract_summary": {{
        "contract_type": "识别出的具体合同类型",
        "overall_risk": "整体风险等级（高风险/中风险/低风险）",
        "key_points": "合同核心要点的简要总结（100字以内）",
        "parties_involved": ["合同各方当事人"]
    }},
    "risks": [
        {{
            "title": "风险点标题",
            "description": "风险的具体描述和可能后果",
            "level": "风险等级（高风险/中风险/低风险）",
            "clause_reference": "相关条款内容摘要"
        }}
    ],
    "plain_explanations": [
        {{
            "clause_title": "条款标题或主题",
            "original_text": "原始条款内容（关键部分）",
            "plain_explanation": "用大白话解释这个条款的真实含义和影响"
        }}
    ],
    "suggestions": [
        {{
            "title": "建议标题",
            "content": "具体的建议内容和应对策略",
            "priority": "建议优先级（高/中/低）"
        }}
    ]
}}

**重要提醒：**
- 请仔细阅读每一个条款，不要遗漏重要风险
- 用普通人能理解的语言，避免法律术语
- 重点关注可能让普通人吃亏的"霸王条款"
- 提供的建议要具体可操作，不要空泛
- 严格按照JSON格式输出，确保格式正确"""

    try:
        # 调用AI进行分析
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # 降低随机性，提高分析的一致性
            max_tokens=4000
        )
        
        # 解析AI响应
        ai_response = response.choices[0].message.content.strip()
        
        # 尝试解析JSON
        try:
            # 清理可能的markdown格式
            if ai_response.startswith('```json'):
                ai_response = ai_response.replace('```json', '').replace('```', '').strip()
            elif ai_response.startswith('```'):
                ai_response = ai_response.replace('```', '').strip()
            
            analysis_data = json.loads(ai_response)
            
            # 验证数据结构
            analysis = ContractAnalysis(**analysis_data)
            
            return analysis.dict()
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"AI响应内容: {ai_response}")
            
            # 返回错误时的默认结构
            return {
                "contract_summary": {
                    "contract_type": "未能识别",
                    "overall_risk": "需要人工审查",
                    "key_points": "AI分析出现错误，建议咨询专业律师",
                    "parties_involved": []
                },
                "risks": [{
                    "title": "分析错误",
                    "description": "AI分析过程中出现错误，无法完成自动分析。建议将合同提交给专业律师进行人工审查。",
                    "level": "高风险",
                    "clause_reference": ""
                }],
                "plain_explanations": [],
                "suggestions": [{
                    "title": "寻求专业帮助",
                    "content": "由于自动分析失败，强烈建议咨询专业律师或法律顾问，确保合同条款对您有利。",
                    "priority": "高"
                }]
            }
            
    except Exception as e:
        print(f"合同分析错误: {str(e)}")
        raise Exception(f"合同分析失败: {str(e)}")

def get_contract_type_name(contract_type: str) -> str:
    """获取合同类型的中文名称"""
    type_mapping = {
        'rental': '租房合同',
        'service': '服务协议',
        'employment': '劳动合同',
        'purchase': '购买协议',
        'cooperation': '合作协议',
        'other': '合同文件'
    }
    return type_mapping.get(contract_type, '合同文件')

def get_contract_focus(contract_type: str) -> str:
    """根据合同类型获取分析重点"""
    focus_mapping = {
        'rental': '租金支付、押金退还、违约责任、房屋维修、提前解约等条款',
        'service': '服务范围、费用结算、责任承担、违约处理、知识产权等条款',
        'employment': '工资待遇、工作时间、社会保险、竞业限制、解除条件等条款',
        'purchase': '商品质量、付款方式、退换货政策、违约责任、售后服务等条款',
        'cooperation': '权利义务分配、利益分配、责任承担、合作期限、终止条件等条款',
        'other': '双方权利义务、违约责任、争议解决、合同终止等核心条款'
    }
    return focus_mapping.get(contract_type, '合同的核心条款和潜在风险')

def extract_key_clauses(contract_text: str) -> List[str]:
    """提取合同中的关键条款（辅助功能）"""
    # 这里可以实现更复杂的条款提取逻辑
    # 目前返回基本的文本分段
    paragraphs = contract_text.split('\n')
    key_clauses = []
    
    for para in paragraphs:
        para = para.strip()
        if len(para) > 50:  # 过滤掉太短的段落
            key_clauses.append(para)
    
    return key_clauses[:10]  # 返回前10个关键段落
