import json

def to_markdown(data_dict):
    md = ""
    for key, value in data_dict.items():
        md += f"### {key}\n{value}\n\n"
    return md

def to_json(text):
    try:
        return json.loads(text)
    except Exception:
        return {"raw_output": text}
