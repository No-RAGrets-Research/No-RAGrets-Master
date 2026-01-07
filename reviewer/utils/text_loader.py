from docling.document_converter import DocumentConverter
import os
import json

def load_paper(pdf_path, export_dir="outputs"):
    converter = DocumentConverter()
    result = converter.convert(pdf_path)

    # 确保输出目录存在
    os.makedirs(export_dir, exist_ok=True)

    # 提取文件名
    name = pdf_path.split("/")[-1].rsplit(".", 1)[0]
    md_path = f"{export_dir}/{name}.md"
    json_path = f"{export_dir}/{name}.json"

    # ✅ 导出 Markdown
    with open(md_path, "w", encoding="utf-8") as f_md:
        f_md.write(result.document.export_to_markdown())

    # ✅ 导出 JSON （新版 Docling 用 export_to_dict）
    doc_dict = result.document.export_to_dict()
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(doc_dict, f_json, ensure_ascii=False, indent=2)

    # ✅ 返回提取的文本（供 LLM 使用）
    return result.document.export_to_markdown()
