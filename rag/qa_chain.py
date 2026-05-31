from typing import List, Dict, Any, Generator

from openai import OpenAI

from config import Config
from rag.prompt_template import render_prompt


client = OpenAI(api_key=Config.OPENAI_API_KEY)


def answer_question(
    question: str,
    docs: List[Dict[str, Any]],
    history: List[Dict[str, str]] | None = None,
) -> str:
    prompt = render_prompt(question, docs, history)

    response = client.chat.completions.create(
        model=Config.MODEL_NAME,
        messages=[
            {"role": "system", "content": "你是一个严谨的 RAG 论文问答助手。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""


def stream_answer_question(
    question: str,
    docs: List[Dict[str, Any]],
    history: List[Dict[str, str]] | None = None,
) -> Generator[str, None, None]:
    prompt = render_prompt(question, docs, history)

    stream = client.chat.completions.create(
        model=Config.MODEL_NAME,
        messages=[
            {"role": "system", "content": "你是一个严谨的 RAG 论文问答助手。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        stream=True,
    )

    for event in stream:
        delta = event.choices[0].delta
        if delta and delta.content:
            yield delta.content
