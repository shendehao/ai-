import os
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Optional

# Define output structure using Pydantic
class ProjectRewrite(BaseModel):
    original: str = Field(description="The original project description or work experience text.")
    rewritten: str = Field(description="The rewritten version optimized for the JD.")

class ResumeAnalysis(BaseModel):
    match_score: int = Field(description="A score from 0 to 100 indicating how well the resume matches the job description.")
    missing_keywords: List[str] = Field(description="A list of important keywords or skills found in the JD but missing from the resume.")
    improvement_suggestions: List[str] = Field(description="A list of specific actionable suggestions to improve the resume.")
    rewritten_projects: List[ProjectRewrite] = Field(description="A list of project descriptions or work experiences that could be better tailored to the JD.")

async def analyze_resume(resume_text: str, jd_text: str, api_key: str = None):
    if not api_key:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
    
    if not api_key:
        raise ValueError("DashScope API Key is required")

    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # Create the analysis prompt with HR professional perspective
    prompt = f"""
    你是一位拥有15年经验的资深HR总监、人才招聘专家，同时也是业界知名的简历优化大师，曾在多家知名企业担任招聘负责人，具有丰富的候选人评估和简历优化经验。
    
    【你的专业背景】
    - 15年人力资源管理经验，专精于人才招聘与评估
    - 曾为500强企业筛选过数万份简历，深谙招聘官的心理和偏好
    - 深度了解各行业的人才需求和职业发展路径
    - 擅长从HR视角识别候选人的核心竞争力和潜在风险
    - **简历优化大师**：帮助超过10000+候选人成功优化简历，平均面试邀请率提升300%
    - **文案专家**：精通简历文案包装技巧，善于用数据和成果说话
    - **行业洞察**：对各行业的关键词、热门技能、薪资水平有深度研究
    - **ATS系统专家**：深度了解各大公司的简历筛选系统，知道如何让简历通过机器筛选
    
    【分析任务】
    现在请你以资深HR总监+简历优化大师的双重专业视角，深度分析这份简历与目标职位的匹配度。请像真正的面试官和简历优化专家一样，从以下维度进行专业评估：
    
    1. **技能匹配度**：技术栈、工具使用、专业能力是否符合岗位要求
    2. **经验相关性**：工作经历、项目经验是否与目标岗位高度相关
    3. **职业发展轨迹**：候选人的成长路径是否合理，是否有清晰的职业规划
    4. **潜在加分项**：超出JD要求但有价值的技能或经验
    5. **风险点识别**：可能影响录用的短板或风险因素
    6. **简历优化机会**：从优化大师角度识别可以提升的表达方式和包装技巧
    7. **ATS友好度**：评估简历对自动筛选系统的友好程度
    
    【候选人简历】
    {resume_text}

    【目标职位JD】
    {jd_text}

    【输出要求】
    请以HR专业视角，按照以下JSON格式返回详细分析结果：
    {{
        "match_score": 匹配度分数(0-100整数，严格按HR标准评分),
        "missing_keywords": ["缺失的核心技能", "缺失的关键经验", "缺失的工具/技术"],
        "improvement_suggestions": [
            "从HR视角的具体改进建议1",
            "从HR视角的具体改进建议2", 
            "从HR视角的具体改进建议3",
            "从HR视角的具体改进建议4"
        ],
        "rewritten_projects": [
            {{
                "original": "原始项目/工作经历描述",
                "rewritten": "HR更青睐的优化描述（突出成果、数据、影响力）"
            }}
        ],
        "hr_insights": {{
            "strengths": ["候选人的核心优势1", "核心优势2"],
            "concerns": ["HR关注的潜在问题1", "潜在问题2"],
            "interview_focus": ["面试时应重点考察的方面1", "重点考察方面2"],
            "salary_range_suggestion": "基于经验和技能的薪资建议区间"
        }}
    }}

    【专业要求】
    1. **评分标准**：严格按照HR行业标准，60分以下为不匹配，60-75为基本匹配，75-85为良好匹配，85+为优秀匹配
    2. **关键词识别**：重点关注JD中的核心技能、必备经验、工具要求，识别ATS系统关键词
    3. **改进建议**：必须具体可执行，避免空泛建议，要体现HR+简历优化大师的双重专业判断
    4. **项目重写**：用HR喜欢的STAR法则（情境-任务-行动-结果）+简历优化大师的文案技巧来重新包装
    5. **HR洞察**：提供只有资深HR才能给出的深度见解和面试建议
    6. **优化大师视角**：提供专业的简历包装建议、关键词优化、数据量化技巧
    7. **ATS优化**：确保建议有助于通过自动筛选系统
    8. **所有内容用中文**，语言专业且具有说服力，体现简历优化大师的专业水准
    """

    try:
        completion = client.chat.completions.create(
            model="qwen-max",
            messages=[
                {"role": "system", "content": "你是一位拥有15年经验的资深HR总监兼简历优化大师，具有丰富的人才招聘、评估和简历优化经验。请以HR总监+简历优化大师的双重专业视角进行分析，严格按照要求的JSON格式返回结果，确保评估标准符合行业实际情况，同时提供专业的简历优化建议。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # 降低温度以获得更专业和一致的输出
            max_tokens=3000   # 增加token数量以支持更详细的HR洞察
        )

        response_content = completion.choices[0].message.content
        
        # Try to parse JSON response
        try:
            # Clean up the response to extract JSON
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
            elif "{" in response_content and "}" in response_content:
                json_start = response_content.find("{")
                json_end = response_content.rfind("}") + 1
                json_content = response_content[json_start:json_end]
            else:
                json_content = response_content

            parsed_result = json.loads(json_content)
            
            # Validate and ensure all required fields exist
            result = {
                "match_score": int(parsed_result.get("match_score", 0)),
                "missing_keywords": parsed_result.get("missing_keywords", []),
                "improvement_suggestions": parsed_result.get("improvement_suggestions", []),
                "rewritten_projects": parsed_result.get("rewritten_projects", []),
                "hr_insights": parsed_result.get("hr_insights", {
                    "strengths": [],
                    "concerns": [],
                    "interview_focus": [],
                    "salary_range_suggestion": "需要更多信息才能给出薪资建议"
                })
            }
            
            return result
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {response_content}")
            # Fallback response
            return {
                "match_score": 50,
                "missing_keywords": ["解析错误"],
                "improvement_suggestions": ["AI响应解析失败，请检查API配置或重试"],
                "rewritten_projects": [],
                "error": "Failed to parse AI response",
                "raw_response": response_content
            }

    except Exception as e:
        print(f"API call error: {e}")
        return {
            "match_score": 0,
            "missing_keywords": [],
            "improvement_suggestions": [f"API调用失败: {str(e)}"],
            "rewritten_projects": [],
            "error": str(e)
        }
