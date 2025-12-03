# OCR 功能安装指南

为了支持图片格式的简历文件（JPG、PNG、WebP），需要安装 Tesseract OCR 引擎。

## Windows 安装

1. **下载 Tesseract**
   - 访问：https://github.com/UB-Mannheim/tesseract/wiki
   - 下载最新版本的 Windows 安装包

2. **安装 Tesseract**
   - 运行下载的 `.exe` 文件
   - 安装时选择包含中文语言包 (`chi_sim`)
   - 默认安装路径：`C:\Program Files\Tesseract-OCR`

3. **配置环境变量**
   - 将 Tesseract 安装路径添加到系统 PATH
   - 或者在代码中指定路径：
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

4. **安装 Python 依赖**
   ```bash
   pip install pillow pytesseract
   ```

## Linux (Ubuntu/Debian) 安装

```bash
# 安装 Tesseract 和中文语言包
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-chi-sim

# 安装 Python 依赖
pip install pillow pytesseract
```

## macOS 安装

```bash
# 使用 Homebrew 安装
brew install tesseract tesseract-lang

# 安装 Python 依赖
pip install pillow pytesseract
```

## 验证安装

运行以下命令验证安装是否成功：

```bash
tesseract --version
```

## 支持的图片格式

- **JPG/JPEG**：最常用的图片格式
- **PNG**：支持透明背景，适合截图
- **WebP**：现代图片格式，文件更小

## 使用建议

1. **图片质量**：确保图片清晰，分辨率至少 300 DPI
2. **文字方向**：避免倾斜或旋转的文字
3. **背景干净**：纯色背景效果最佳
4. **文字大小**：文字不要太小，至少 12pt
5. **格式推荐**：PDF 格式仍然是最佳选择

## 故障排除

如果遇到 OCR 识别问题：

1. **检查图片质量**：确保图片清晰可读
2. **调整图片**：可以先用图片编辑软件调整对比度
3. **使用 PDF**：对于复杂布局，建议转换为 PDF 格式
4. **手动输入**：如果 OCR 效果不佳，可以手动将简历内容输入到职位描述框中进行分析
