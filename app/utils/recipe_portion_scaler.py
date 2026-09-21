from __future__ import annotations

import re


# 匹配：数字 + 单位（g/克/mg/毫克/kg/千克/公斤/斤/两）
_GRAM_RE = re.compile(r"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>g|克|mg|毫克|kg|千克|公斤|斤|两)\b", re.IGNORECASE)


def _format_num(x: float) -> str:
    # 尽量保持“整洁”：接近整数则输出整数，否则 1 位小数
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.1f}".rstrip("0").rstrip(".")


def scale_recipe_text(text: str, factor: float) -> str:
    """
    将配方文本中的所有“数字+单位”按 factor 缩放。
    - 支持 g/克/mg/毫克/kg/千克/公斤/斤/两
    - 仅做数值缩放，不改变单位
    """
    if not text:
        return text
    try:
        f = float(factor)
    except Exception:
        return text
    if f <= 0:
        return text
    if abs(f - 1.0) < 1e-6:
        return text

    def repl(m: re.Match) -> str:
        num = float(m.group("num"))
        unit = m.group("unit")
        new_num = num * f
        return f"{_format_num(new_num)}{unit}"

    return _GRAM_RE.sub(repl, text)

