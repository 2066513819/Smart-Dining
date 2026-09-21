from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
from datetime import datetime, timezone, timedelta
from app.models.user import User
from app.models.menu_item import MenuItem
from app.schemas.dish import RecommendationRequest, DatabaseRecommendationRequest, MealSetRecommendationRequest
from app.services.db_service import get_db
from app.services.dify_service import DifyService
from app.routers.auth import get_current_user
from app.models.system_setting import SystemSetting
from app.utils.nutrition_adjuster import NutritionAdjuster, normalize_age_group
from app.config.guideline_meal_rules import get_guideline_meal_rules, get_default_meal_rules
from app.config.guideline_portion_ratios import portion_ratio_for_meal
from app.config.guideline_nutrition_standards import get_nutrition_targets
from app.utils.recipe_portion_scaler import scale_recipe_text
import json
import traceback
import math

# 中国时区（UTC+8）
CHINA_TZ = timezone(timedelta(hours=8))

def json_safe_float(v, default=0.0):
    """确保返回一个JSON兼容的浮点数（非inf, 非nan）"""
    if v is None:
        return default
    try:
        f = float(v)
        if math.isinf(f) or math.isnan(f):
            return default
        return f
    except (ValueError, TypeError):
        return default

def format_datetime_with_timezone(dt: datetime) -> str:
    """将datetime转换为ISO格式字符串，包含时区信息（中国时区）"""
    if dt is None:
        return None
    # 如果datetime是naive（没有时区信息），假设它是数据库服务器的本地时间（中国时区）
    if dt.tzinfo is None:
        # 假设数据库返回的时间是中国时区
        dt = dt.replace(tzinfo=CHINA_TZ)
    # 转换为中国时区
    if dt.tzinfo != CHINA_TZ:
        dt = dt.astimezone(CHINA_TZ)
    # 返回ISO格式，包含时区信息
    return dt.isoformat()

router = APIRouter()

ALLOWED_MEAL_TYPES = {"breakfast", "lunch", "dinner"}

def _normalize_age_group_for_db(code: str) -> str:
    s = (code or "").strip().lower()
    m = {
        "primary": "primary_low",
        "primary_low": "primary_low",
        "primary-high": "primary_high",
        "primary_high": "primary_high",
        "junior_low": "primary_high",
        "junior": "junior",
        "junior_high": "junior",
        "senior": "senior"
    }
    return m.get(s, s)

def get_nutrition_targets_db_first(db: Session, age_group: str, meal: str) -> dict:
    ag = _normalize_age_group_for_db(age_group)
    m = (meal or "").strip().lower()
    try:
        q = text("""
            SELECT target_calories_kcal, target_protein_g,
                   target_calcium_mg, target_iron_mg, target_vitamin_c_mg
            FROM vw_nutrition_meal_targets_simple
            WHERE age_group_code = :ag AND meal = :meal
            LIMIT 1
        """)
        row = db.execute(q, {"ag": ag, "meal": m}).mappings().first()
        if row:
            return {
                "target_calories": float(row.get("target_calories_kcal") or 0),
                "target_protein": float(row.get("target_protein_g") or 0),
                "target_calcium": float(row.get("target_calcium_mg") or 0),
                "target_iron": float(row.get("target_iron_mg") or 0),
                "target_vitamin_c": float(row.get("target_vitamin_c_mg") or 0)
            }
    except Exception:
        pass
    return get_nutrition_targets(age_group, meal)

def load_meal_rules(db: Session, user_age_group: str = None):
    """
    加载配餐规则，优先使用管理员配置的规则，如果没有配置则使用指南标准的默认规则
    
    Args:
        db: 数据库会话
        user_age_group: 用户年龄段，如果提供且管理员未配置规则，则使用该年龄段的指南标准规则
    """
    item = db.query(SystemSetting).filter(SystemSetting.key == "meal_rules").first()
    
    # 默认规则
    default_rules = {}
    if user_age_group:
        default_rules = get_guideline_meal_rules(user_age_group)
    else:
        default_rules = get_default_meal_rules()
    
    # 默认成本与人数
    default_costs = {"breakfast": 10.0, "lunch": 20.0, "dinner": 20.0}
    default_num_people = {"breakfast": 1, "lunch": 1, "dinner": 1}
    
    # 如果管理员已配置规则，优先使用
    if item and item.value:
        try:
            data = json.loads(item.value)
            if isinstance(data, dict):
                admin_rules = {
                    "breakfast": data.get("breakfast") if isinstance(data.get("breakfast"), dict) else default_rules.get("breakfast", {}),
                    "lunch": data.get("lunch") if isinstance(data.get("lunch"), dict) else default_rules.get("lunch", {}),
                    "dinner": data.get("dinner") if isinstance(data.get("dinner"), dict) else default_rules.get("dinner", {}),
                    "costs": data.get("costs") if isinstance(data.get("costs"), dict) else default_costs,
                    "num_people": data.get("num_people") if isinstance(data.get("num_people"), dict) else default_num_people,
                    "dining_style": data.get("dining_style", "盘餐")
                }
                return admin_rules
        except Exception:
            pass
    
    # 如果管理员未配置规则，返回默认规则和成本
    res = default_rules.copy()
    res["costs"] = default_costs
    res["num_people"] = default_num_people
    res["dining_style"] = "盘餐"
    return res

def apply_additional_filters_for_request(base_query, request, meal_type: str = None):
    # 如果提供了 ingredient_prices，则跳过 SQL 层的成本过滤，改为在内存中计算并过滤
    # 因为数据库中的 cost_price 可能与导入的价格表不一致
    has_dynamic_prices = getattr(request, "ingredient_prices", None) is not None and len(getattr(request, "ingredient_prices", {})) > 0

    # 推荐规则：只推荐有价格的菜品（必须要有价格显示）
    if not has_dynamic_prices:
        base_query = base_query.filter(MenuItem.cost_price > 0)
    
    # 成本价格过滤
    if not has_dynamic_prices:
        if meal_type == "breakfast":
            max_cost = getattr(request, "max_cost_breakfast", None)
            if max_cost is not None:
                base_query = base_query.filter(MenuItem.cost_price <= float(max_cost))
        elif meal_type == "lunch":
            max_cost = getattr(request, "max_cost_lunch", None)
            if max_cost is not None:
                base_query = base_query.filter(MenuItem.cost_price <= float(max_cost))
        elif meal_type == "dinner":
            max_cost = getattr(request, "max_cost_dinner", None)
            if max_cost is not None:
                base_query = base_query.filter(MenuItem.cost_price <= float(max_cost))
        
        # 通用成本过滤（如果 request 有 max_cost 字段）
        max_cost_generic = getattr(request, "max_cost", None)
        if max_cost_generic is not None:
            base_query = base_query.filter(MenuItem.cost_price <= float(max_cost_generic))

    if getattr(request, "category", None):
        if isinstance(request.category, list) and len(request.category) > 0:
            # 使用 or_ 来匹配多个分类，同时考虑模糊匹配或精确匹配
            category_filters = []
            for cat in request.category:
                if cat:
                    cat_trimmed = cat.strip()
                    # 优化：支持“荤菜”匹配“荤菜类”，也支持“荤菜类”匹配“荤菜”
                    cat_base = cat_trimmed[:-1] if cat_trimmed.endswith("类") else cat_trimmed
                    category_filters.append(MenuItem.category.like(f"%{cat_trimmed}%"))
                    if cat_base != cat_trimmed:
                        category_filters.append(MenuItem.category.like(f"%{cat_base}%"))
            if category_filters:
                base_query = base_query.filter(or_(*category_filters))
    if getattr(request, "flavor", None):
        if isinstance(request.flavor, list) and len(request.flavor) > 0:
            # 只有当风味不是“不限”时才过滤
            active_flavors = [f for f in request.flavor if f and f != "不限"]
            if active_flavors:
                base_query = base_query.filter(MenuItem.flavor.in_(active_flavors))
    if getattr(request, "season", None):
        if isinstance(request.season, list) and len(request.season) > 0:
            # 只有当季节不是“不限”时才过滤
            active_seasons = [s for s in request.season if s and s != "不限"]
            if active_seasons:
                # 匹配逻辑：菜品的季节在用户选择的季节列表中，或者菜品是“四季皆宜”
                base_query = base_query.filter(
                    or_(
                        MenuItem.season.in_(active_seasons),
                        MenuItem.season == "四季皆宜",
                        MenuItem.season == "",
                        MenuItem.season.is_(None)
                    )
                )
    if getattr(request, "nutrition_requirements", None):
        for requirement in request.nutrition_requirements or []:
            if requirement == "高蛋白":
                base_query = base_query.filter(MenuItem.total_protein >= 15.0)
            elif requirement == "低脂肪":
                base_query = base_query.filter(MenuItem.total_fat <= 10.0)
            elif requirement == "低碳水":
                base_query = base_query.filter(MenuItem.total_carbohydrates <= 30.0)
            elif requirement == "高钙":
                base_query = base_query.filter(MenuItem.total_calcium >= 100.0)
            elif requirement == "高铁":
                base_query = base_query.filter(MenuItem.total_iron >= 3.0)
            elif requirement == "高维生素C":
                base_query = base_query.filter(MenuItem.total_vitamin_c >= 20.0)

    # 严格匹配食材已取消，食材列表仅用于偏好排序（优先推荐含指定食材的菜品）
    return base_query

from app.utils.cost_calculator import calculate_dynamic_cost


def _extract_ingredients_from_recipe(recipe_text: str) -> set:
    """从菜谱文本中提取食材名称（用于多样性计算）"""
    if not recipe_text or not recipe_text.strip():
        return set()
    import re
    skip = {'适量', '少许', '少量', '若干', '水', '盐', '油', '酱油', '料酒', '醋', '糖', '味精', '淀粉'}
    ingredients = set()
    for line in recipe_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        # 匹配 "食材名: 100g" 或 "食材名 100克" 等
        for m in re.finditer(r'([\u4e00-\u9fa5a-zA-Z]{2,20}?)\s*[:：]?\s*[0-9.]+', line):
            name = m.group(1).strip()
            if name not in skip:
                ingredients.add(name)
        # 也匹配 "食材A、食材B" 或 "食材A，食材B" 格式
        for part in re.split(r'[,，、\s]+', line):
            part = re.sub(r'[0-9.]+', '', part).strip()
            if 2 <= len(part) <= 20 and part not in skip:
                ingredients.add(part)
    return ingredients

# 常见食材颜色映射（用于多颜色多样化推荐）
_INGREDIENT_COLOR_MAP = {
    "绿": ["青菜", "菠菜", "芹菜", "青椒", "黄瓜", "西蓝花", "生菜", "油菜", "芥蓝", "空心菜", "韭菜", "香菜", "小葱", "莴笋", "豌豆", "青豆", "豆角", "丝瓜", "苦瓜"],
    "红": ["番茄", "胡萝卜", "红椒", "红萝卜", "辣椒", "红枣", "红豆", "山楂", "草莓", "樱桃", "西红柿", "猪肉", "牛肉", "火腿"],
    "黄": ["玉米", "南瓜", "鸡蛋", "黄豆", "土豆", "地瓜", "香蕉", "菠萝", "芒果", "柠檬", "小米", "黄椒", "姜", "玉米粒", "红薯", "南瓜"],
    "白": ["豆腐", "米饭", "牛奶", "萝卜", "白菜", "莲藕", "山药", "银耳", "木耳", "蘑菇", "金针菇", "葱", "蒜", "花菜", "冬瓜", "面粉", "大米"],
    "紫": ["紫甘蓝", "茄子", "紫薯", "紫菜", "蓝莓", "葡萄", "紫洋葱"],
    "黑": ["黑木耳", "黑豆", "黑米", "海带", "黑芝麻"],
}

def _get_ingredient_colors(ingredients: set) -> set:
    """根据食材集合推断涉及的颜色"""
    colors = set()
    for ing in ingredients:
        ing_lower = ing.lower()
        for color, keywords in _INGREDIENT_COLOR_MAP.items():
            if any(kw in ing or ing in kw for kw in keywords):
                colors.add(color)
                break
    return colors

def _diversity_score(dish: "MenuItem", used_ingredients: set, used_colors: set) -> float:
    """
    计算菜品对食材多样性和多颜色的贡献得分。
    新食材、新颜色越多，得分越高。
    """
    ings = _extract_ingredients_from_recipe(dish.dish_recipe or "")
    colors = _get_ingredient_colors(ings)
    new_ings = len(ings - used_ingredients)
    new_colors = len(colors - used_colors)
    return float(new_ings * 2 + new_colors * 3)  # 新颜色权重略高

def calc_match_count_factory(ingredients: list[str], strict: bool = False, ingredient_prices: dict[str, float] = None, max_cost: float = None):
    ingredients_norm = [s.strip().lower() for s in ingredients if s and s.strip()]
    def calc(item: MenuItem) -> int:
        # 如果提供了价格表，计算动态价格并覆盖原有价格
        current_cost = item.cost_price
        if ingredient_prices:
            dynamic_cost = calculate_dynamic_cost(item.dish_recipe, ingredient_prices)
            # 注意：这里我们修改的是内存中的对象，不会写回数据库
            item.cost_price = dynamic_cost
            current_cost = dynamic_cost
            
        # 成本过滤：如果在动态计算模式下超过了预算，返回 -1
        if max_cost is not None and current_cost > float(max_cost):
            return -1

        if not ingredients_norm and not strict:
            return 0
        
        dish_name = (item.dish_name or "").lower()
        dish_recipe = (item.dish_recipe or "").lower()
        text = f"{dish_name}\n{dish_recipe}"
        
        # 基础匹配计数
        cnt = 0
        matched_ingredients = []
        for ing in ingredients_norm:
            if ing and ing in text:
                cnt += 1
                matched_ingredients.append(ing)
        
        # 如果是严格模式，且该菜品包含不在 ingredients_norm 中的食材，则返回 -1 表示不符合
        if strict:
            import re
            lines = dish_recipe.split('\n')
            for line in lines:
                if not line.strip(): continue
                m = re.search(r'([^\s\d,，、:：]+)\s*[:：]?\s*[0-9]+', line)
                if m:
                    ing_name = m.group(1).strip()
                    found = False
                    for target in ingredients_norm:
                        if target in ing_name or ing_name in target:
                            found = True
                            break
                    if not found:
                        return -1
        
        return cnt
    return ingredients_norm, calc

@router.get("/dify-health")
def dify_health():
    s = DifyService(is_analysis=False)
    info = s.validate_config()
    return info

def _age_group_form_to_backend(age_group: str) -> str:
    """前端表单年龄段(PRIMARY/JUNIOR/SENIOR) 转为后端代码"""
    s = (age_group or "").strip().upper()
    if s == "PRIMARY":
        return "primary_high"
    if s == "JUNIOR":
        return "junior_high"
    if s == "SENIOR":
        return "senior"
    return _normalize_age_group_for_db(s) or "junior_high"


def _dish_to_template_item(dish: dict) -> dict:
    """将后端菜品结构转为前端模板期望的 { name, description, ingredients, nutrition }"""
    name = dish.get("dish_name") or dish.get("name") or ""
    recipe = dish.get("dish_recipe") or ""
    desc = (recipe[:200] + "…") if len(recipe) > 200 else recipe
    ingredients = "见菜谱"
    cal = dish.get("total_calories") or 0
    protein = dish.get("total_protein") or 0
    fat = dish.get("total_fat") or 0
    carb = dish.get("total_carbohydrates") or 0
    nutrition = f"热量 {cal:.0f} kcal，蛋白质 {protein:.1f} g，脂肪 {fat:.1f} g，碳水 {carb:.1f} g"
    return {"name": name, "description": desc, "ingredients": ingredients, "nutrition": nutrition}


@router.post("/generate")
def generate_recommendation(
    age_group: str = Form(..., description="年龄段：PRIMARY/JUNIOR/SENIOR"),
    school: str = Form("", description="学校名称"),
    preference: str = Form("", description="饮食偏好"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    供前端（模板页或 Vue）调用的「生成推荐」接口。
    使用后端权重评分推荐（营养40% + 成本35% + 食材种类25%），返回早/午/晚餐推荐。
    前端期望格式：{ recommendation: "JSON字符串" }，解析后为 { breakfast: [], lunch: [], dinner: [] }，
    每项为 { name, description, ingredients, nutrition }。
    """
    try:
        target_age_group = _age_group_form_to_backend(age_group)
        cost_budget = {"breakfast": 10.0, "lunch": 20.0, "dinner": 20.0}

        from app.services.recommendation_service import RecommendationService

        service = RecommendationService(db=db, user=current_user)
        result = service.recommend_meal_plan_with_scoring(
            days=1,
            age_group=target_age_group,
            meal_types=["breakfast", "lunch", "dinner"],
            cost_budget_per_meal=cost_budget,
        )

        if not result.get("success") or not result.get("days"):
            raise HTTPException(status_code=500, detail="生成推荐失败，请稍后重试")

        first_day = result["days"][0]
        meals_data = first_day.get("meals", {})
        breakfast_list = []
        lunch_list = []
        dinner_list = []

        for meal_key, meal_result in meals_data.items():
            if not isinstance(meal_result, dict):
                continue
            best = meal_result.get("best_plan")
            if not best:
                continue
            dishes = best.get("dishes") or []
            items = [_dish_to_template_item(d) for d in dishes]
            if meal_key == "breakfast":
                breakfast_list = items
            elif meal_key == "lunch":
                lunch_list = items
            elif meal_key == "dinner":
                dinner_list = items

        payload = {
            "breakfast": breakfast_list,
            "lunch": lunch_list,
            "dinner": dinner_list,
        }
        return {"recommendation": json.dumps(payload, ensure_ascii=False)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[generate] 错误: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"生成推荐失败: {str(e)}")


@router.post("/get-recommendation")
def get_recommendation(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 加载管理员设置的配餐规则
        meal_rules = load_meal_rules(db)
        current_meal_type = request.meal_type or "lunch"
        # 将英文 meal_type 映射为规则中的 key
        rule_key = "breakfast"
        if "午" in current_meal_type: rule_key = "lunch"
        elif "晚" in current_meal_type: rule_key = "dinner"
        elif current_meal_type in ["breakfast", "lunch", "dinner"]: rule_key = current_meal_type

        rules_desc = ""
        specific_rules = meal_rules.get(rule_key, {})
        if specific_rules:
            rules_parts = [f"{k}: {v}份" for k, v in specific_rules.items() if int(v) > 0]
            if rules_parts:
                rules_desc = f"\n\n[管理员配餐规则 - 必须严格执行]\n当前餐次({current_meal_type})必须包含且仅包含以下种类的菜品：\n" + "\n".join([f"- {p}" for p in rules_parts])
                rules_desc += "\n请确保推荐的菜品总数和分类比例与上述规则完全一致。如果规则中要求了水果类，请务必推荐水果。"

        # 构建查询字符串
        # 若前端已传完整 prompt（通常已含规则和格式要求），后端不再二次拼接，避免规则冲突。
        query = ""
        user_prompt = ""
        if hasattr(request, 'prompt') and request.prompt:
            query = request.prompt.strip()
        else:
            if request.cycle and request.meal_type:
                user_prompt = f"请为学生推荐{request.cycle}的{request.meal_type}菜品"
            else:
                user_prompt = "请为学生推荐菜品"
            query = f"{user_prompt}，包含详细的菜品名称、描述、配料和营养信息。{rules_desc}"
        
        if not query or not query.strip():
            raise ValueError("查询字符串不能为空")
        
        print(f"构建的查询字符串: {query}")
        print(f"请求的user_id: {request.user_id}")
        print(f"当前用户信息: {current_user}")
        print(f"当前用户ID: {current_user.id}")
        
        # 调用Dify服务获取推荐，使用current_user.id作为userid
        # 使用默认推荐智能体
        print("初始化DifyService...")
        dify_service = DifyService(is_analysis=False)
        print(f"DifyService初始化完成，base_url: {dify_service.base_url}")
        
        print("开始调用Dify API...")
        result = dify_service.get_recommendation(query, str(current_user.id))
        
        print(f"获取到的推荐结果: {result}")
        
        if not result:
            raise ValueError("Dify服务返回了空结果")
        
        return result
    except Exception as e:
        print(f"获取推荐失败，详细错误信息:")
        print(traceback.format_exc())
        # 返回统一的友好内容，避免前端出现500
        friendly = (
            "获取推荐失败。请稍后重试，或联系管理员检查Dify服务配置。"
        )
        return {
            "role": "assistant",
            "content": friendly,
            "outputs": {
                "text": friendly,
                "type": "text"
            }
        }

@router.post("/database-recommendation")
def database_recommendation(
    request: DatabaseRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        print(f"===== 数据库推荐请求开始 (count={request.count}) =====")
        print(f"请求参数: type={request.dish_type}, cat={request.category}, exclude={request.exclude_ids}")
        # 加载配餐规则（使用指南标准，因为database-recommendation不需要用户年龄段）
        meal_rules = load_meal_rules(db)
        current_meal_type = request.meal_type or "lunch"
        # 将英文 meal_type 映射为规则中的 key
        rule_key = "breakfast"
        if "午" in current_meal_type: rule_key = "lunch"
        elif "晚" in current_meal_type: rule_key = "dinner"
        elif current_meal_type in ["breakfast", "lunch", "dinner"]: rule_key = current_meal_type
        
        specific_rules = meal_rules.get(rule_key, {})
        # 严格匹配食材已取消（无法做到完全匹配）
        is_strict = False
        # 获取价格参数
        ingredient_prices = getattr(request, "ingredient_prices", {})
        
        # 成本限制优先级：请求参数 > 管理员配置
        max_cost = request.max_cost
        if max_cost is None:
            cost_rules = meal_rules.get("costs", {})
            max_cost = cost_rules.get(rule_key)
            print(f"DEBUG: 数据库推荐 - 使用管理员配置的最大成本限制: {max_cost}")
        else:
            print(f"DEBUG: 数据库推荐 - 使用请求参数的最大成本限制: {max_cost}")

        ingredients_norm, calc_match_count = calc_match_count_factory(
            request.ingredients or [], 
            strict=is_strict, 
            ingredient_prices=ingredient_prices,
            max_cost=max_cost
        )
        ingredients = request.ingredients or []

        recommendations = []
        
        # 如果有具体规则，且没有指定具体分类，且不是请求单个菜品，则按规则获取
        # 增加 request.count > 1 的判断，确保单菜重新生成（count=1）不会触发全餐规则
        if not (request.category and len(request.category) > 0) and \
           request.count > 1 and \
           specific_rules and \
           any(int(v) > 0 for v in specific_rules.values()):
            print(f"按规则获取数据库推荐: {specific_rules}")
            for category, count in specific_rules.items():
                if int(count) <= 0: continue
                
                # 为每个分类构建查询
                def get_cat_items(db, cat, meal_type, request, use_filters=True):
                    q = db.query(MenuItem)
                    # 优化逻辑：如果是奶制品、水果等通用分类，放宽餐次(dish_type)限制
                    is_common_category = cat in ["奶及奶制品类", "水果类", "饮料类"]
                    if not is_common_category:
                        q = q.filter(MenuItem.dish_type == meal_type)
                    
                    # 先尝试精确匹配（使用 TRIM 处理分类名称）
                    cat_trimmed = cat.strip()
                    # 优化：如果分类以“类”结尾，尝试同时匹配带“类”和不带“类”的情况
                    cat_base = cat_trimmed[:-1] if cat_trimmed.endswith("类") else cat_trimmed
                    q_exact = q.filter(or_(
                        func.trim(MenuItem.category) == cat_trimmed,
                        func.trim(MenuItem.category) == cat_base
                    ))
                    
                    if use_filters:
                        q_exact = apply_additional_filters_for_request(q_exact, request, meal_type)
                    
                    type_count = q_exact.count()
                    print(f"DEBUG: 单餐推荐 - 分类 [{cat}] (精确匹配), 结果数: {type_count}")
                    
                    # 如果精确匹配没有结果，尝试模糊匹配
                    if type_count <= 0:
                        print(f"DEBUG: 单餐推荐 - 精确匹配失败，尝试模糊匹配...")
                        q_fuzzy = db.query(MenuItem)
                        
                        # 对于通用分类，不限制 dish_type
                        if not is_common_category:
                            q_fuzzy = q_fuzzy.filter(MenuItem.dish_type == meal_type)
                        
                        # 尝试模糊匹配
                        q_fuzzy = q_fuzzy.filter(MenuItem.category.like(f"%{cat_trimmed}%"))
                        
                        if use_filters:
                            q_fuzzy = apply_additional_filters_for_request(q_fuzzy, request, meal_type)
                        
                        type_count = q_fuzzy.count()
                        if type_count > 0:
                            print(f"DEBUG: 单餐推荐 - 模糊匹配成功，找到 {type_count} 个菜品")
                            q = q_fuzzy
                        else:
                            # 如果还是没找到，对于通用分类，尝试完全不限制任何条件（除了分类）
                            if is_common_category:
                                print(f"DEBUG: 单餐推荐 - 通用分类 [{cat}] 模糊匹配也失败，尝试完全不限制条件...")
                                q_no_filter = db.query(MenuItem).filter(MenuItem.category.like(f"%{cat_trimmed}%"))
                                type_count = q_no_filter.count()
                                if type_count > 0:
                                    print(f"DEBUG: 单餐推荐 - 完全不限制条件后，找到 {type_count} 个菜品")
                                    q = q_no_filter
                                else:
                                    print(f"DEBUG: 单餐推荐 - 警告：分类 [{cat}] 在数据库中完全找不到匹配的菜品")
                                    return []
                            else:
                                print(f"DEBUG: 单餐推荐 - 警告：分类 [{cat}] 在数据库中完全找不到匹配的菜品")
                                return []
                    else:
                        q = q_exact
                    
                    items = q.order_by(func.random()).limit(int(count) * 10).all()
                    if is_strict:
                        # 严格过滤
                        items = [x for x in items if calc_match_count(x) != -1]
                    
                    if ingredients and items:
                        items.sort(key=lambda x: calc_match_count(x), reverse=True)
                    return items[:int(count)]

                # 第一轮：带过滤条件
                cat_items = get_cat_items(db, category, rule_key, request, use_filters=True)
                
                # 第二轮：放宽条件
                if not cat_items:
                    print(f"单餐推荐: 分类 {category} 带条件未匹配到，尝试放宽条件...")
                    cat_items = get_cat_items(db, category, rule_key, request, use_filters=False)
                
                recommendations.extend(cat_items)
        else:
            # 兜底逻辑：如果没有规则，则按原来的随机逻辑
            query = db.query(MenuItem)
            
            # 如果指定了要排除的 ID
            if request.exclude_ids:
                query = query.filter(MenuItem.id.not_in(request.exclude_ids))
                
            # 如果指定了 dish_type
            if request.dish_type and len(request.dish_type) > 0:
                query = query.filter(MenuItem.dish_type.in_(request.dish_type))
            
            # 尝试从 dish_type 中获取第一个作为 meal_type 提示
            hint_meal_type = request.dish_type[0] if request.dish_type else None
            query = apply_additional_filters_for_request(query, request, hint_meal_type)
            total_count = query.count()
            print(f"符合基础条件的菜品总数: {total_count}")
            
            sample_size = max(request.count * 5, 200)
            sample_size = min(sample_size, max(total_count, 0))
            if sample_size > 0:
                candidates = query.order_by(func.random()).limit(sample_size).all()
                if ingredients:
                    candidates.sort(key=lambda x: calc_match_count(x), reverse=True)
                # 使用动态价格时先统一算出成本，再按「必须有价格」过滤
                if getattr(request, "ingredient_prices", None) and len(getattr(request, "ingredient_prices", {})) > 0:
                    for c in candidates:
                        c.cost_price = calculate_dynamic_cost(c.dish_recipe or "", getattr(request, "ingredient_prices", {}))
                # 推荐规则：只保留有价格的菜品
                candidates = [c for c in candidates if json_safe_float(c.cost_price) > 0]
                recommendations = candidates[:request.count]

        print(f"最终返回菜品数量: {len(recommendations)}")
        
        # 打印返回的菜品类型统计
        if recommendations:
            dish_type_stats = {}
            for rec in recommendations:
                dish_type = rec.dish_type
                # 使用get方法安全获取键值，避免KeyError
                dish_type_stats[dish_type] = dish_type_stats.get(dish_type, 0) + 1
            print(f"返回菜品类型统计: {dish_type_stats}")
        
        # 格式化返回结果
        result = []
        for rec in recommendations:
            result.append({
                "id": rec.id,
                "dish_type": rec.dish_type,
                "dish_name": rec.dish_name,
                "category": getattr(rec, "category", "") or "",
                "dish_recipe": rec.dish_recipe,
                "total_calories": float(rec.total_calories),
                "total_carbohydrates": float(rec.total_carbohydrates),
                "total_fat": float(rec.total_fat),
                "total_protein": float(rec.total_protein),
                "total_calcium": float(rec.total_calcium),
                "total_iron": float(rec.total_iron),
                "total_vitamin_c": float(rec.total_vitamin_c),
                "ingredient_count": rec.ingredient_count,
                "matched_count": calc_match_count(rec),
                "season": rec.season,
                "flavor": rec.flavor,
                "created_at": format_datetime_with_timezone(rec.created_at) if rec.created_at else None,
                "updated_at": format_datetime_with_timezone(rec.updated_at) if rec.updated_at else None
            })
        
        print("===== 数据库推荐请求结束 =====")
        return result
    except Exception as e:
        # 打印详细的错误堆栈信息
        print(f"数据库推荐失败，详细错误信息:")
        print(traceback.format_exc())
        
        # 构建详细的错误响应
        error_detail = {
            "message": "数据库推荐失败",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "stack_trace": traceback.format_exc()
        }
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )

@router.post("/generate-ai-dishes")
async def generate_ai_dishes(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    try:
        count = request.get("count", 3)
        category = request.get("category", "")
        
        category_prompt = f"类别为: {category}" if category else "类别随机"
        query = f"请生成 {count} 个餐饮菜品，{category_prompt}。返回格式必须是 JSON 数组，每个对象包含 name, category, description, nutrition 字段。nutrition 字段应包含卡路里、蛋白质、脂肪、碳水化合物信息。"
        
        dify_service = DifyService()
        result = dify_service.get_recommendation(query, str(current_user.id))
        
        # 尝试从回复中解析 JSON
        answer = result.get("answer", "")
        # 寻找 JSON 数组
        start = answer.find("[")
        end = answer.rfind("]") + 1
        if start != -1 and end != -1:
            json_str = answer[start:end]
            dishes = json.loads(json_str)
            return dishes
        else:
            # 如果没找到 JSON，返回一个友好的错误或默认结果
            print(f"无法从 AI 回复中解析 JSON: {answer}")
            return []
            
    except Exception as e:
        print(f"AI 生成菜品失败: {str(e)}")
        print(traceback.format_exc())
        return []

@router.post("/meal-set-recommendation")
def meal_set_recommendation(
    request: MealSetRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    weighted: bool = True  # 默认使用加权评分（营养40%+成本35%+食材种类25%），与前端餐饮推荐页一致
):
    """
    严格按照管理员配餐规则生成菜谱计划
    默认使用加权模式（与前端「菜谱制定」页一致）：
    - 营养值达标 40%、成本 35%、食材种类 25%
    - 系统自动筛选多种组合并按权重评分，返回最优计划
    传 weighted=false 时可切换为普通快速模式。
    如果规则中只有水果类，就只返回水果类，不会返回其他分类
    """
    try:
        print(f"DEBUG: meal-set-recommendation 收到请求 weighted={weighted} (True=按权重评分)")
        # 解析用户年龄段（优先使用请求中的，否则使用用户配置的）
        raw_age_group = request.target_age_group or getattr(current_user, "age_group", "") or ""
        default_target_age_group = normalize_age_group(raw_age_group)
        print(f"DEBUG: 默认目标人群(raw)={raw_age_group}, 归一化={default_target_age_group}")
        
        # 加载配餐规则（优先使用管理员配置，否则使用指南标准规则）
        meal_rules = load_meal_rules(db, user_age_group=default_target_age_group)
        
        # 检查是否使用加权推荐
        if weighted:
            print(f"========== 开始生成加权评分菜谱计划（营养40%%+成本35%%+食材25%%）==========")
            print(f"DEBUG: 使用加权评分模式，将生成多组合并按权重筛选最优")
        else:
            print(f"========== 开始生成菜谱计划（普通模式）==========")
            print(f"DEBUG: 使用普通快速模式")
        
        print(f"DEBUG: 使用的配餐规则: {meal_rules}")
        print(f"DEBUG: 规则来源: {'管理员配置' if db.query(SystemSetting).filter(SystemSetting.key == 'meal_rules').first() and db.query(SystemSetting).filter(SystemSetting.key == 'meal_rules').first().value else '学生餐营养指南标准'}")

        # 待生成的餐次类型
        meal_types = [m for m in (request.meal_types or []) if isinstance(m, str) and m in ALLOWED_MEAL_TYPES]
        if not meal_types:
            meal_types = ["breakfast", "lunch", "dinner"]
        
        # 获取成本规则
        cost_rules = meal_rules.get("costs", {})

        print(f"DEBUG: 待生成的餐次类型: {meal_types}")
        print(f"DEBUG: 生成天数: {request.days}")
        print(f"DEBUG: 使用的成本规则: {cost_rules}")

        is_strict = False  # 严格匹配食材已取消，无法做到完全匹配
        ingredient_prices = getattr(request, "ingredient_prices", {})

        # 如果使用加权推荐，调用加权推荐功能
        if weighted:
            try:
                from app.utils.weighted_recommendation import WeightedRecommendation
                weighted_rec = WeightedRecommendation(db)
                result = weighted_rec.generate_weighted_meal_set(
                    request=request,
                    meal_rules=meal_rules,
                    target_age_group=default_target_age_group,
                    ingredient_prices=ingredient_prices,
                    strict_mode=is_strict
                )
                # 转换为前端期望的格式：days[i].breakfast/lunch/dinner 为菜品数组，与普通模式一致
                if result.get("weighted_recommendation") and result.get("days"):
                    converted_days = []
                    for day_idx, day_plan in enumerate(result["days"]):
                        day_obj = {"day": day_idx + 1}
                        for meal_key in ("breakfast", "lunch", "dinner"):
                            block = day_plan.get(meal_key) or {}
                            items = block.get("items", []) if isinstance(block, dict) else []
                            summary = block.get("summary", {}) if isinstance(block, dict) else {}
                            day_obj[meal_key] = items
                            day_obj[f"{meal_key}_summary"] = summary
                        converted_days.append(day_obj)
                    result["days"] = converted_days
                return result
            except ImportError as e:
                print(f"!!! 加权推荐模块导入失败，回退到普通模式 !!! 错误: {e}")
                print(traceback.format_exc())
            except Exception as e:
                print(f"!!! 加权推荐执行失败，回退到普通模式 !!! 错误: {e}")
                print(traceback.format_exc())

        # 普通模式继续
        used_ids: set[int] = set()
        used_ingredients: set = set()
        used_colors: set = set()
        out_days = []

        for day_index in range(1, int(request.days or 1) + 1):
            day_obj = {"day": day_index, "breakfast": [], "lunch": [], "dinner": []}
            print(f"\n--- 开始处理第 {day_index} 天 ---")
            
            for meal in meal_types:
                # 获取该餐次的特定设置
                meal_spec = (request.meal_settings or {}).get(meal)
                
                # 确定该餐次的目标人群
                target_age_group = default_target_age_group
                if meal_spec and meal_spec.target_age_group:
                    target_age_group = normalize_age_group(meal_spec.target_age_group)
                
                # 确定该餐次的就餐人数
                # 优先级: 
                # 1. 推荐请求中特定餐次的人数 (meal_spec.num_people)
                # 2. 推荐请求中的全局份数 (request.servings)，如果用户设置了大于 1 的值，则视为显式覆盖
                # 3. 后端配餐规则中设置的该餐次人数 (meal_rules.num_people[meal])
                # 4. 推荐请求中的全局份数 (request.servings) 或默认 1
                meal_num_people = 1
                if meal_spec and meal_spec.num_people:
                    meal_num_people = meal_spec.num_people
                elif request.servings and request.servings > 1:
                    meal_num_people = request.servings
                elif isinstance(meal_rules.get("num_people"), dict) and meal_rules.get("num_people").get(meal):
                    meal_num_people = meal_rules.get("num_people").get(meal)
                else:
                    meal_num_people = request.servings or 1
                
                if meal_num_people < 1: meal_num_people = 1
                
                # 为当前餐次初始化匹配函数，包含对应的成本限制
                # 优先级：请求参数中的成本限制 > 管理员配置的成本限制
                max_cost_meal = None
                if meal == "breakfast": 
                    max_cost_meal = request.max_cost_breakfast if request.max_cost_breakfast is not None else cost_rules.get("breakfast")
                elif meal == "lunch": 
                    max_cost_meal = request.max_cost_lunch if request.max_cost_lunch is not None else cost_rules.get("lunch")
                elif meal == "dinner": 
                    max_cost_meal = request.max_cost_dinner if request.max_cost_dinner is not None else cost_rules.get("dinner")
                
                print(f"DEBUG: 餐次 [{meal}] 使用的最大成本限制: {max_cost_meal}")
                
                ingredients_norm, calc_match_count = calc_match_count_factory(
                    request.ingredients or [], 
                    strict=is_strict, 
                    ingredient_prices=ingredient_prices,
                    max_cost=max_cost_meal
                )
                
                # 获取该餐次的营养目标（来自营养指南表 vw_nutrition_meal_targets_simple）
                nutrition_targets = get_nutrition_targets_db_first(db, target_age_group, meal)
                target_calories_meal = json_safe_float(nutrition_targets.get("target_calories", 0))
                
                # 获取该餐次的配餐规则
                per_cat = meal_rules.get(meal) or {}
                print(f"\nDEBUG: 处理餐次 [{meal}]")
                print(f"DEBUG: 该餐次规则: {per_cat}")
                
                if not isinstance(per_cat, dict):
                    per_cat = {}
                
                # 如果规则为空，跳过该餐次（不生成任何菜品）
                if not per_cat or len(per_cat) == 0:
                    print(f"DEBUG: 警告 - 餐次 [{meal}] 没有配置规则，跳过该餐次（返回空列表）")
                    continue
                
                selected_items: list[MenuItem] = []

                # 严格按照规则中的每个分类生成菜品
                for category, cnt in per_cat.items():
                    if not isinstance(cnt, int) or cnt <= 0:
                        print(f"DEBUG: 跳过分类 [{category}]，数量无效: {cnt}")
                        continue
                    
                    print(f"\nDEBUG: 开始为分类 [{category}] 寻找 {cnt} 个菜品")
                    
                    # 判断是否为通用分类（水果、奶制品、饮料不限制餐次类型）
                    is_common_category = category.strip() in ["奶及奶制品类", "水果类", "饮料类"]
                    
                    # 构建查询
                    q = db.query(MenuItem)
                    
                    # 对于非通用分类，限制餐次类型
                    if not is_common_category:
                        q = q.filter(MenuItem.dish_type == meal)
                        print(f"DEBUG: 分类 [{category}] 限制餐次类型为: {meal}")
                    else:
                        print(f"DEBUG: 分类 [{category}] 是通用分类，不限制餐次类型")
                    
                    # 严格匹配分类名称（多种方式尝试）
                    cat_trimmed = category.strip()
                    
                    # 方式1: 使用 TRIM 的精确匹配
                    q1 = q.filter(func.trim(MenuItem.category) == cat_trimmed)
                    count1 = q1.count()
                    print(f"DEBUG: 方式1 (TRIM精确匹配): {count1} 个菜品")
                    
                    # 方式2: 直接精确匹配
                    q2 = q.filter(MenuItem.category == cat_trimmed)
                    count2 = q2.count()
                    print(f"DEBUG: 方式2 (直接精确匹配): {count2} 个菜品")
                    
                    # 选择有结果的查询
                    if count1 > 0:
                        q_final = q1
                        final_count = count1
                    elif count2 > 0:
                        q_final = q2
                        final_count = count2
                    else:
                        # 如果精确匹配都没有结果，对于通用分类尝试模糊匹配
                        if is_common_category:
                            print(f"DEBUG: 精确匹配失败，通用分类 [{category}] 尝试模糊匹配...")
                            q_fuzzy = db.query(MenuItem).filter(
                                or_(
                                    func.trim(MenuItem.category).like(f"%{cat_trimmed}%"),
                                    MenuItem.category.like(f"%{cat_trimmed}%")
                                )
                            )
                            final_count = q_fuzzy.count()
                            if final_count > 0:
                                q_final = q_fuzzy
                                print(f"DEBUG: 模糊匹配成功，找到 {final_count} 个菜品")
                            else:
                                print(f"DEBUG: 错误 - 分类 [{category}] 在数据库中完全找不到匹配的菜品")
                                # 打印数据库中所有分类，帮助调试
                                all_cats = db.query(MenuItem.category).distinct().all()
                                cat_list = sorted(set([c[0] for c in all_cats if c[0]]))
                                print(f"DEBUG: 数据库中存在的所有分类: {cat_list}")
                                # 不添加任何菜品，继续下一个分类
                                continue
                        else:
                            print(f"DEBUG: 错误 - 分类 [{category}] 在数据库中完全找不到匹配的菜品")
                            # 打印数据库中所有分类，帮助调试
                            all_cats = db.query(MenuItem.category).distinct().all()
                            cat_list = sorted(set([c[0] for c in all_cats if c[0]]))
                            print(f"DEBUG: 数据库中存在的所有分类: {cat_list}")
                            # 不添加任何菜品，继续下一个分类
                            continue
                    
                    # 应用额外的过滤条件（口味、时令、营养需求等）
                    q_final = apply_additional_filters_for_request(q_final, request, meal)
                    filtered_count = q_final.count()
                    print(f"DEBUG: 应用过滤条件后: {filtered_count} 个菜品")
                    
                    # 如果应用过滤条件后没有结果，尝试不应用过滤条件
                    if filtered_count == 0:
                        print(f"DEBUG: 应用过滤条件后无结果，尝试不应用过滤条件...")
                        # 重新构建查询（不应用过滤条件）
                        if count1 > 0:
                            q_final = q1
                        elif count2 > 0:
                            q_final = q2
                        elif is_common_category:
                            q_final = db.query(MenuItem).filter(
                                or_(
                                    func.trim(MenuItem.category).like(f"%{cat_trimmed}%"),
                                    MenuItem.category.like(f"%{cat_trimmed}%")
                                )
                            )
                        else:
                            continue

                    # 应用成本过滤
                    max_cost = max_cost_meal
                    
                    if max_cost is not None and max_cost > 0:
                        # 如果没有提供动态价格，则在 SQL 层进行过滤以提高效率
                        if not ingredient_prices:
                            total_items_in_meal = sum(per_cat.values())
                            
                            if meal_rules.get("dining_style") == "团餐":
                                # 团餐模式：max_cost 是人均成本，需要乘以总人数得到该餐次总预算
                                # 每道菜的参考上限 = (人均预算 * 总人数) / 计划菜品总数
                                avg_item_cost = (max_cost * meal_num_people) / total_items_in_meal
                                # 团餐选菜可以更宽松一些，只要最后平均下来不超标即可
                                q_final = q_final.filter(MenuItem.cost_price <= avg_item_cost * 1.5)
                            else:
                                # 盘餐模式：max_cost 就是该份套餐的总成本
                                avg_item_cost = max_cost / total_items_in_meal
                                # 盘餐选菜相对严格，避免单品过贵导致套餐总价超标
                                q_final = q_final.filter(MenuItem.cost_price <= avg_item_cost * 1.2)
                            
                            print(f"DEBUG: 应用成本过滤 (style={meal_rules.get('dining_style')}, avg_item_limit={avg_item_cost}), 剩余菜品数: {q_final.count()}")
                        else:
                            print(f"DEBUG: 跳过 SQL 层成本过滤，将在内存中基于导入价格计算并过滤")

                    # 获取候选菜品（性价比优先：按成本升序，满足营养需求前提下选最低价）
                    sample_size = max(cnt * 15, 80)
                    sample_size = min(sample_size, max(q_final.count(), 0))
                    candidates = q_final.order_by(MenuItem.cost_price.asc()).limit(sample_size).all()
                    
                    # 营养指南过滤：单道菜卡路里不应超过该餐次总目标的 1.2 倍
                    if target_calories_meal > 0:
                        candidates = [c for c in candidates if json_safe_float(c.total_calories) <= target_calories_meal * 1.2]
                    
                    # 严格模式过滤
                    if is_strict:
                        candidates = [c for c in candidates if calc_match_count(c) != -1]
                    
                    # 排序：食材匹配度(如有) > 成本升序(性价比) > 多样性(新食材+多颜色)
                    if ingredients_norm:
                        candidates.sort(key=lambda x: (
                            -calc_match_count(x),
                            json_safe_float(x.cost_price),
                            -_diversity_score(x, used_ingredients, used_colors)
                        ))
                    else:
                        candidates.sort(key=lambda x: (
                            json_safe_float(x.cost_price),
                            -_diversity_score(x, used_ingredients, used_colors)
                        ))

                    # 推荐规则：只保留有价格的菜品（动态价已在上面的 sort/calc_match_count 中写入 cost_price）
                    candidates = [c for c in candidates if json_safe_float(c.cost_price) > 0]
                    
                    # 严格验证并添加菜品
                    cat_added_count = 0
                    for candidate in candidates:
                        if cat_added_count >= cnt:
                            break
                        if candidate.id in used_ids:
                            continue
                        
                        # 严格验证分类是否匹配
                        item_cat = (candidate.category or "").strip()
                        if item_cat != cat_trimmed and cat_trimmed not in item_cat and item_cat not in cat_trimmed:
                            print(f"DEBUG: 跳过 - 菜品 [{candidate.dish_name}] 的分类 [{item_cat}] 与期望 [{cat_trimmed}] 不匹配")
                            continue
                        
                        selected_items.append(candidate)
                        used_ids.add(candidate.id)
                        ings = _extract_ingredients_from_recipe(candidate.dish_recipe or "")
                        used_ingredients.update(ings)
                        used_colors.update(_get_ingredient_colors(ings))
                        cat_added_count += 1
                        print(f"DEBUG: ✓ 已添加分类 [{category}] 的菜品: {candidate.dish_name} (ID: {candidate.id}, 分类: {item_cat}, 成本: {json_safe_float(candidate.cost_price):.2f})")
                    
                    if cat_added_count < cnt:
                        print(f"DEBUG: 警告 - 分类 [{category}] 需求 {cnt} 份，实际仅匹配到 {cat_added_count} 份")
                
                # 验证最终结果
                print(f"\nDEBUG: 餐次 [{meal}] 最终选定的菜品总数: {len(selected_items)}")
                if selected_items:
                    category_stats = {}
                    for item in selected_items:
                        cat = (item.category or "").strip()
                        category_stats[cat] = category_stats.get(cat, 0) + 1
                    print(f"DEBUG: 最终菜品分类统计: {category_stats}")
                    print(f"DEBUG: 期望规则: {per_cat}")
                    
                    # 验证是否严格按照规则生成
                    expected_cats = set([k.strip() for k, v in per_cat.items() if isinstance(v, int) and v > 0])
                    actual_cats = set(category_stats.keys())
                    if expected_cats != actual_cats:
                        print(f"DEBUG: ⚠️ 警告 - 期望分类 {expected_cats} 与实际分类 {actual_cats} 不完全匹配")
                else:
                    print(f"DEBUG: ⚠️ 警告 - 餐次 [{meal}] 配置了规则 {per_cat}，但没有匹配到任何菜品！")

                # 格式化返回结果
                day_obj[meal] = []
                total_nutrition = {
                    "total_calories": 0.0,
                    "total_carbohydrates": 0.0,
                    "total_fat": 0.0,
                    "total_protein": 0.0,
                    "total_calcium": 0.0,
                    "total_iron": 0.0,
                    "total_vitamin_c": 0.0,
                }
                
                for rec in selected_items:
                    base_nutrition = {
                        "total_calories": json_safe_float(rec.total_calories),
                        "total_carbohydrates": json_safe_float(rec.total_carbohydrates),
                        "total_fat": json_safe_float(rec.total_fat),
                        "total_protein": json_safe_float(rec.total_protein),
                        "total_calcium": json_safe_float(rec.total_calcium),
                        "total_iron": json_safe_float(rec.total_iron),
                        "total_vitamin_c": json_safe_float(rec.total_vitamin_c),
                    }
                    adjusted = NutritionAdjuster.adjust_nutrition(target_age_group, base_nutrition)
                    
                    # 累加总营养（单份营养 * 份数）
                    # 这里的份数优先使用全局设置的 servings
                    # 在团餐模式下，如果用户没有特别设置 servings，我们默认每道菜提供 meal_num_people 份
                    dish_servings = request.servings or 1
                    if meal_rules.get("dining_style") == "团餐" and (not request.servings or request.servings == 1) and meal_num_people > 1:
                        dish_servings = meal_num_people
                        
                    for k in total_nutrition:
                        total_nutrition[k] += adjusted.get(k, 0.0) * dish_servings

                    # 1) 先按“年龄段 + 餐次(早餐/午/晚)”将配方克数整体缩放到指南表的量级
                    portion_factor = portion_ratio_for_meal(target_age_group, meal)
                    
                    # 如果是团餐，适当增加份量系数（因为是自助形式，损耗和冗余较多）
                    if meal_rules.get("dining_style") == "团餐":
                        portion_factor *= 1.2
                        
                    scaled_recipe = scale_recipe_text(rec.dish_recipe or "", portion_factor)
                    # 2) 再追加一句说明
                    adjusted_recipe = scaled_recipe
                    if meal_rules.get("dining_style") == "团餐":
                        adjusted_recipe += f"\n(团餐模式：已按自助形式调整配比，份量上浮20%)"
                    # if scaled_recipe:
                    #     adjusted_recipe = f"{scaled_recipe}\n(已按学生餐营养指南：{target_age_group} + {meal} 的供给量范围整体缩放 {portion_factor:.2f} 倍)"

                    # 3) 调整成本价格 (团餐模式下份量上浮 20%，成本也应相应上浮)
                    adjusted_cost = json_safe_float(rec.cost_price)
                    if meal_rules.get("dining_style") == "团餐":
                        adjusted_cost *= 1.2

                    day_obj[meal].append({
                        "id": rec.id,
                        "dish_type": rec.dish_type,
                        "dish_name": rec.dish_name,
                        "category": getattr(rec, "category", "") or "",
                        "dish_recipe": adjusted_recipe,
                        "total_calories": json_safe_float(adjusted["total_calories"]),
                        "total_carbohydrates": json_safe_float(adjusted["total_carbohydrates"]),
                        "total_fat": json_safe_float(adjusted["total_fat"]),
                        "total_protein": json_safe_float(adjusted["total_protein"]),
                        "total_calcium": json_safe_float(adjusted["total_calcium"]),
                        "total_iron": json_safe_float(adjusted["total_iron"]),
                        "total_vitamin_c": json_safe_float(adjusted["total_vitamin_c"]),
                        "ingredient_count": rec.ingredient_count,
                        "matched_count": calc_match_count(rec),
                        "season": rec.season,
                        "flavor": rec.flavor,
                        "cost_price": round(json_safe_float(adjusted_cost), 2),
                        "created_at": format_datetime_with_timezone(rec.created_at) if rec.created_at else None,
                        "updated_at": format_datetime_with_timezone(rec.updated_at) if rec.updated_at else None,
                        "age_group": target_age_group,
                        "portion_factor": json_safe_float(portion_factor),
                    })

                # 团餐模式下的平均营养与成本计算与指南校验
                if meal_rules.get("dining_style") == "团餐":
                    # 计算总成本与平均成本
                    total_cost = sum(json_safe_float(item.get("cost_price", 0)) * (request.servings or 1 if not (meal_rules.get("dining_style") == "团餐" and (not request.servings or request.servings == 1) and meal_num_people > 1) else meal_num_people) for item in day_obj[meal])
                    # 注意：上面的 total_cost 计算逻辑需要与 total_nutrition 累加逻辑保持一致
                    # 简化逻辑：直接累加该餐次所有菜品的 adjusted_cost * 对应份数
                    meal_total_cost = 0.0
                    for item_data in day_obj[meal]:
                        # 份数逻辑与营养累加一致
                        dish_servings = request.servings or 1
                        if meal_rules.get("dining_style") == "团餐" and (not request.servings or request.servings == 1) and meal_num_people > 1:
                            dish_servings = meal_num_people
                        meal_total_cost += json_safe_float(item_data.get("cost_price", 0)) * dish_servings
                    
                    avg_cost = round(meal_total_cost / meal_num_people, 2)

                    # 计算平均营养
                    avg_nutrition = {k: round(json_safe_float(v / meal_num_people), 2) for k, v in total_nutrition.items()}
                    
                    targets = get_nutrition_targets_db_first(db, target_age_group, meal)
                    
                    compliance = {}
                    is_compliant = True
                    
                    nutrient_map = {
                        "total_calories": "target_calories",
                        "total_protein": "target_protein",
                        "total_fat": "target_fat",
                        "total_carbohydrates": "target_carbohydrates",
                        "total_calcium": "target_calcium",
                        "total_iron": "target_iron",
                        "total_vitamin_c": "target_vitamin_c"
                    }
                    
                    for nutrient, target_key in nutrient_map.items():
                        target_val = json_safe_float(targets.get(target_key, 0))
                        actual_val = json_safe_float(avg_nutrition.get(nutrient, 0))
                        
                        if target_val > 0:
                            # 能量和三大营养素允许 ±15% 波动，微量元素建议不低于 90%
                            if nutrient in ["total_calories", "total_protein", "total_fat", "total_carbohydrates"]:
                                lower_bound = round(target_val * 0.85, 2)
                                upper_bound = round(target_val * 1.15, 2)
                                status = lower_bound <= actual_val <= upper_bound
                                compliance[nutrient] = {
                                    "status": status,
                                    "target": json_safe_float(target_val),
                                    "actual": json_safe_float(actual_val),
                                    "min": json_safe_float(lower_bound),
                                    "max": json_safe_float(upper_bound)
                                }
                            else:
                                lower_bound = round(target_val * 0.9, 2)
                                status = actual_val >= lower_bound
                                compliance[nutrient] = {
                                    "status": status,
                                    "target": json_safe_float(target_val),
                                    "actual": json_safe_float(actual_val),
                                    "min": json_safe_float(lower_bound),
                                    "max": None
                                }
                            
                            if not status: is_compliant = False
                    
                    day_obj[f"{meal}_summary"] = {
                        "avg_nutrition": avg_nutrition,
                        "avg_cost": avg_cost,
                        "targets": {tk: json_safe_float(tv) for tk, tv in targets.items()},
                        "is_compliant": is_compliant,
                        "compliance_details": compliance,
                        "num_people": meal_num_people,
                        "target_age_group": target_age_group
                    }

            out_days.append(day_obj)
        
        print(f"\n========== 菜谱计划生成完成 ==========")
        return {"days": out_days, "rules": meal_rules}
    except Exception as e:
        print("按规则生成套餐推荐失败，详细错误信息:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"按规则生成套餐推荐失败: {str(e)}")

@router.post("/analyze-dishes")
def analyze_dishes(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # 构建菜品分析查询字符串
        query = f"请分析当前用户保存的菜品，并给出下一步的菜品推荐。分析应包括营养均衡性、菜品多样性、适合的年龄阶段等方面，并基于分析结果给出具体的菜品推荐，包含详细的菜品名称、描述、配料和营养信息。"
        
        print(f"构建的分析查询字符串: {query}")
        print(f"请求的user_id: {request.user_id}")
        print(f"当前用户信息: {current_user}")
        
        # 调用Dify服务获取菜品分析和推荐，使用current_user.id作为userid
        # 使用菜品分析智能体
        dify_service = DifyService(is_analysis=True)
        result = dify_service.get_recommendation(query, str(current_user.id))
        
        print(f"获取到的菜品分析结果: {result}")
        
        return result
    except Exception as e:
        # 打印详细的错误堆栈信息
        print(f"菜品分析失败，详细错误信息:")
        print(traceback.format_exc())
        
        # 构建详细的错误响应
        error_detail = {
            "message": "菜品分析失败",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "stack_trace": traceback.format_exc()
        }
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )
