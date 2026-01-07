from docling.document_converter import DocumentConverter

source = "UCSC NLP Project - CB Literature/A. Priyadarsini et al. 2023.pdf"  # file path or URL
converter = DocumentConverter()
doc = converter.convert(source).document

print(doc.export_to_markdown())  # output: "### Docling Technical Report[...]"