from pathlib import Path
from typing import List, Dict, Any

import yaml
from jinja2 import Template


DEFAULT_TEMPLATE = """
你是一个严谨的论文阅读助手。请只基于给定的论文片段回答问题。
如果片段中没有答案，请明确说明“根据当前检索片段无法判断”，不要编造。

【历史对话】
{{ history }}

【论文片段】
{% for doc in docs %}
片段 {{ loop.index }}，第 {{ doc.metadata.page_num }} 页：
{{ doc.text }}
{% endfor %}

【用户问题】
{{ question }}

请用中文回答，并尽量分点说明。回答末尾给出引用页码，例如：来源：第 3 页、第 5 页。
""".strip()


def load_template(template_path: str | None = None) -> Template:
    if not template_path:
        return Template(DEFAULT_TEMPLATE)

    path = Path(template_path)
    if not path.exists():
        return Template(DEFAULT_TEMPLATE)

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    template_text = data.get("template", DEFAULT_TEMPLATE)
    return Template(template_text)


def render_prompt(
    question: str,
    docs: List[Dict[str, Any]],
    history: List[Dict[str, str]] | None = None,
) -> str:
    history = history or []
    history_text = "\n".join([
        f"用户：{h.get('question', '')}\n助手：{h.get('answer', '')}"
        for h in history
    ])

    template = load_template()
    return template.render(
        question=question,
        docs=docs,
        history=history_text or "无",
    )
