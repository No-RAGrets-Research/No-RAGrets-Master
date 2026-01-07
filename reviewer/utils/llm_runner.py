from openai import OpenAI

def run_llm(prompt: str, model: str = "gpt-4o", temperature: float = 0.2):
    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()
