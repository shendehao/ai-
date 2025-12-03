import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import shutil
import uuid

from services.pdf_parser import extract_text_from_pdf
from services.image_parser import extract_text_from_image, is_tesseract_available
from services.cloud_ocr import extract_text_from_image_cloud, is_cloud_ocr_available, get_ocr_status
from services.ai_advisor import analyze_resume
from services.contract_analyzer import analyze_contract
from database import init_db, get_db, AnalysisRecord

app = FastAPI(title="Resume Polisher AI")

# 添加安全响应头
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    # 防止点击劫持
    response.headers["X-Frame-Options"] = "DENY"
    # 防止 MIME 类型嗅探
    response.headers["X-Content-Type-Options"] = "nosniff"
    # XSS 防护
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # 强制 HTTPS (生产环境启用)
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # 内容安全策略
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' https://dashscope.aliyuncs.com"
    # 引用策略
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # 权限策略
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Initialize DB
init_db()

# CORS - 生产环境应该限制具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # 只允许必要的方法
    allow_headers=["*"],
    max_age=600,  # 预检请求缓存时间
)

# Serve static files
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse('static/index.html')

@app.get("/contract")
async def contract_analyzer():
    return FileResponse('static/contract.html')

@app.post("/analyze")
async def analyze_resume_endpoint(
    resume: UploadFile = File(...),
    jd_text: str = Form(...),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # ========== 安全检查 1: 文件名验证 ==========
    if not resume.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 防止路径遍历攻击 (../../../etc/passwd)
    safe_filename = os.path.basename(resume.filename)
    if safe_filename != resume.filename:
        raise HTTPException(status_code=400, detail="文件名包含非法字符")
    
    # 防止特殊字符和脚本注入
    import re
    if not re.match(r'^[\w\-. ]+$', safe_filename):
        raise HTTPException(status_code=400, detail="文件名只能包含字母、数字、下划线、连字符和点")
    
    # ========== 安全检查 2: 文件扩展名验证 ==========
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.webp']
    file_ext = os.path.splitext(safe_filename.lower())[1]
    
    if not file_ext:
        raise HTTPException(status_code=400, detail="文件必须有扩展名")
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="只支持 PDF、JPG、PNG、WebP 格式")
    
    # ========== 安全检查 3: 文件大小限制 ==========
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await resume.read()
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件不能为空")
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
    
    # ========== 安全检查 4: 文件内容类型验证 (Magic Number) ==========
    import imghdr
    
    # 验证文件真实类型，防止伪造扩展名
    if file_ext == '.pdf':
        # PDF 文件应该以 %PDF- 开头
        if not content.startswith(b'%PDF-'):
            raise HTTPException(status_code=400, detail="文件内容与 PDF 格式不符，可能是伪造的文件")
    else:
        # 验证图片文件的真实类型
        try:
            image_type = imghdr.what(None, h=content)
            valid_image_types = ['jpeg', 'png', 'webp']
            
            if image_type not in valid_image_types:
                raise HTTPException(status_code=400, detail=f"文件内容与声明的图片格式不符，检测到的类型: {image_type}")
        except Exception as e:
            raise HTTPException(status_code=400, detail="无法验证图片文件类型，文件可能已损坏")

    # ========== 安全检查 5: JD 文本验证 ==========
    if not jd_text or not jd_text.strip():
        raise HTTPException(status_code=400, detail="职位描述不能为空")
    
    # 限制 JD 文本长度，防止 DoS 攻击
    MAX_JD_LENGTH = 50000  # 50KB
    if len(jd_text) > MAX_JD_LENGTH:
        raise HTTPException(status_code=400, detail="职位描述过长，请精简到 50000 字符以内")
    
    # 清理 JD 文本中的潜在危险字符
    jd_text = jd_text.strip()
    
    # ========== 安全检查 6: API Key 验证 ==========
    if api_key:
        # 验证 API Key 格式
        if not api_key.startswith('sk-'):
            raise HTTPException(status_code=400, detail="API Key 格式不正确")
        
        # 限制 API Key 长度
        if len(api_key) > 200:
            raise HTTPException(status_code=400, detail="API Key 长度异常")

    try:
        
        # 1. Extract text based on file type
        if file_ext == '.pdf':
            resume_text = await extract_text_from_pdf(content)
        else:
            # For image files, use cloud OCR first, then fallback to local
            try:
                if is_cloud_ocr_available():
                    # 使用云端OCR（更准确）
                    resume_text = await extract_text_from_image_cloud(content)
                elif is_tesseract_available():
                    # 降级到本地Tesseract
                    resume_text = await extract_text_from_image(content)
                else:
                    # 没有任何OCR可用
                    ocr_status = get_ocr_status()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"图片文字识别功能不可用。\n\n可用服务: {', '.join(ocr_status['available_services']) if ocr_status['available_services'] else '无'}\n\n解决方案：\n1. 配置云端OCR服务（推荐）\n2. 安装本地Tesseract OCR\n3. 将简历转换为 PDF 格式\n\n详细说明请查看项目文档。"
                    )
                
            except HTTPException:
                raise  # 重新抛出HTTP异常
            except Exception as e:
                raise HTTPException(
                    status_code=400, 
                    detail=f"图片文字识别失败：{str(e)}。\n\n建议：\n1. 确保图片清晰可读\n2. 使用 PDF 格式（推荐）\n3. 检查OCR服务配置"
                )
        
        if not resume_text.strip():
             raise HTTPException(status_code=400, detail="无法从文件中提取文字内容。如果是图片格式，请确保图片清晰可读。")

        # 2. AI Analysis
        analysis_result = await analyze_resume(resume_text, jd_text, api_key)
        
        # 3. Save to DB
        try:
            score = int(analysis_result.get("match_score", 0))
        except:
            score = 0
            
        db_record = AnalysisRecord(
            filename=resume.filename,
            job_description_snippet=jd_text[:100], # Save first 100 chars
            match_score=score
        )
        db.add(db_record)
        db.commit()
        
        return {
            "filename": resume.filename,
            "analysis": analysis_result,
            "db_record_id": db_record.id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-contract")
async def analyze_contract_endpoint(
    contract: UploadFile = File(...),
    contract_type: str = Form(...),
    context: str = Form(""),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """合同分析端点"""
    
    # ========== 安全检查 1: 文件名验证 ==========
    if not contract.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    # 防止路径遍历攻击
    safe_filename = os.path.basename(contract.filename)
    if safe_filename != contract.filename:
        raise HTTPException(status_code=400, detail="文件名包含非法字符")
    
    # 防止特殊字符和脚本注入
    import re
    if not re.match(r'^[\w\-. ]+$', safe_filename):
        raise HTTPException(status_code=400, detail="文件名只能包含字母、数字、下划线、连字符和点")
    
    # ========== 安全检查 2: 文件扩展名验证 ==========
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.webp']
    file_ext = os.path.splitext(safe_filename.lower())[1]
    
    if not file_ext:
        raise HTTPException(status_code=400, detail="文件必须有扩展名")
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="只支持 PDF、Word、图片、文本格式")
    
    # ========== 安全检查 3: 文件大小限制 ==========
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    content = await contract.read()
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件不能为空")
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
    
    # ========== 安全检查 4: 文件内容类型验证 ==========
    import imghdr
    
    # 验证文件真实类型，防止伪造扩展名
    if file_ext == '.pdf':
        # PDF 文件应该以 %PDF- 开头
        if not content.startswith(b'%PDF-'):
            raise HTTPException(status_code=400, detail="文件内容与 PDF 格式不符")
    elif file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
        # 验证图片文件的真实类型
        try:
            image_type = imghdr.what(None, h=content)
            valid_image_types = ['jpeg', 'png', 'webp']
            
            if image_type not in valid_image_types:
                raise HTTPException(status_code=400, detail=f"文件内容与声明的图片格式不符，检测到的类型: {image_type}")
        except Exception as e:
            raise HTTPException(status_code=400, detail="无法验证图片文件类型，文件可能已损坏")

    try:
        # 1. Extract text based on file type
        if file_ext == '.pdf':
            contract_text = await extract_text_from_pdf(content)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
            # For image files, use cloud OCR first, then fallback to local
            try:
                if is_cloud_ocr_available():
                    # 使用云端OCR（更准确）
                    contract_text = await extract_text_from_image_cloud(content)
                elif is_tesseract_available():
                    # 降级到本地Tesseract
                    contract_text = await extract_text_from_image(content)
                else:
                    # 没有任何OCR可用
                    ocr_status = get_ocr_status()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"图片文字识别功能不可用。\n\n可用服务: {', '.join(ocr_status['available_services']) if ocr_status['available_services'] else '无'}\n\n解决方案：\n1. 配置云端OCR服务（推荐）\n2. 安装本地Tesseract OCR\n3. 将合同转换为 PDF 格式\n\n详细说明请查看项目文档。"
                    )
                
            except HTTPException:
                raise  # 重新抛出HTTP异常
            except Exception as e:
                raise HTTPException(
                    status_code=400, 
                    detail=f"图片文字识别失败：{str(e)}。\n\n建议：\n1. 确保图片清晰可读\n2. 使用 PDF 格式（推荐）\n3. 检查OCR服务配置"
                )
        elif file_ext == '.txt':
            # 纯文本文件
            contract_text = content.decode('utf-8')
        else:
            # Word文档等其他格式
            raise HTTPException(status_code=400, detail="暂不支持该文件格式，请转换为PDF或图片格式")
        
        if not contract_text.strip():
            raise HTTPException(status_code=400, detail="无法从文件中提取文字内容。如果是图片格式，请确保图片清晰可读。")

        # 2. Get API key (use manual input if provided, otherwise use environment variable)
        if api_key:
            # 验证手动输入的API Key格式
            if not api_key.startswith('sk-'):
                raise HTTPException(status_code=400, detail="API Key 格式不正确，应以 'sk-' 开头")
            
            # 限制 API Key 长度
            if len(api_key) > 200:
                raise HTTPException(status_code=400, detail="API Key 长度异常")
        else:
            # 使用环境变量中的API Key
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if not api_key or api_key == "sk-your-dashscope-api-key-here":
                raise HTTPException(
                    status_code=400, 
                    detail="请提供有效的 DashScope API Key。\n\n解决方案：\n1. 在表单中填写您的 API Key\n2. 或在服务器 .env 文件中配置 DASHSCOPE_API_KEY\n\n获取 API Key：https://dashscope.aliyun.com/"
                )
        
        # 3. AI Contract Analysis
        analysis_result = await analyze_contract(contract_text, contract_type, context, api_key)
        
        return {
            "filename": contract.filename,
            "contract_type": contract_type,
            "analysis": analysis_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/ocr-status")
async def ocr_status():
    """获取OCR服务状态"""
    return get_ocr_status()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
