"""
食材成本计算：根据配方文本和价格表计算动态成本，供推荐与采购共用。
"""
import re
from typing import Dict

_RECIPE_UNIT_TO_GRAMS = {
    "个": 50, "只": 50, "枚": 50, "颗": 30,
    "瓶": 500, "盒": 250, "袋": 100, "包": 100,
    "根": 50, "片": 10, "块": 30, "勺": 10, "瓣": 5,
}


def find_best_price_match(recipe_ing_name: str, ingredient_prices: Dict[str, float]) -> float:
    """
    为配方中的食材名在价格表中找最合适的单价（精确 > 包含取最长 > 正则）。
    """
    if not recipe_ing_name or not ingredient_prices:
        return 0.0
    r = recipe_ing_name.strip()
    if r in ingredient_prices:
        return float(ingredient_prices[r])
    containing = [k for k in ingredient_prices if r in k]
    if containing:
        return float(ingredient_prices[max(containing, key=len)])
    contained = [k for k in ingredient_prices if k in r]
    if contained:
        return float(ingredient_prices[max(contained, key=len)])
    for price_ing, price in ingredient_prices.items():
        if not price_ing or len(price_ing) < 2:
            continue
        if not any(c in price_ing for c in (".*", "|", "(", "[")):
            continue
        try:
            if re.search(price_ing, r):
                return float(price)
        except re.error:
            continue
    return 0.0


def calculate_dynamic_cost(recipe_text: str, ingredient_prices: Dict[str, float]) -> float:
    """
    根据菜谱文本和食材单价字典计算动态成本。
    配方格式：食材名 + 数量 + 单位；ingredient_prices 为 {食材名或别名: 单价(每克)}。
    """
    if not recipe_text or not ingredient_prices:
        return 0.0
    total_cost = 0.0
    unit_group = r"(g|克|kg|千克|ml|毫升|l|升|个|只|枚|颗|瓶|盒|袋|包|根|片|块|勺|瓣)?"
    pat = re.compile(r"([^\s\d,，、:：]+)\s*[:：]?\s*([0-9.]+)\s*" + unit_group, re.I)
    for line in recipe_text.split("\n"):
        if not line.strip():
            continue
        m = pat.search(line)
        if not m:
            continue
        ing_name = m.group(1).strip()
        amount = float(m.group(2))
        unit = (m.group(3) or "g").strip().lower()
        if unit in ("kg", "千克", "公斤"):
            amount *= 1000
        elif unit in ("l", "升"):
            amount *= 1000
        elif unit in _RECIPE_UNIT_TO_GRAMS:
            amount *= _RECIPE_UNIT_TO_GRAMS[unit]
        total_cost += amount * find_best_price_match(ing_name, ingredient_prices)
    return round(total_cost, 2)
