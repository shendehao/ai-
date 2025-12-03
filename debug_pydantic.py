from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

class ResumeAnalysis(BaseModel):
    match_score: int = Field(description="A score from 0 to 100 indicating how well the resume matches the job description.")
    missing_keywords: List[str] = Field(description="A list of important keywords or skills found in the JD but missing from the resume.")
    improvement_suggestions: List[str] = Field(description="A list of specific actionable suggestions to improve the resume.")
    # complex types might be tricky for simple parser but let's see
    
parser = PydanticOutputParser(pydantic_object=ResumeAnalysis)
print(parser.get_format_instructions())
