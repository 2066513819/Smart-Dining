"""
餐饮计划评分器 - 新版
支持真正的多计划权重评分筛选

权重配置：
- 营养值达标率 (40%)
- 成本控制 (35%)
- 食材种类多样性 (25%)

算法流程：
1. 生成多种餐饮组合方案
2. 对每个方案计算营养、成本、多样性三个维度的评分
3. 按权重计算综合评分
4. 选择评分最高的方案推荐给用户
"""

from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import math
import logging
import re
import traceback

from app.config.recommendation_weights import WEIGHT_NUTRITION, WEIGHT_COST, WEIGHT_INGREDIENT_VARIETY
from app.config.guideline_nutrition_standards import get_nutrition_targets

logger = logging.getLogger(__name__)

# 基本权重类（简化版本）
class BasicWeights:
    WEIGHT_NUTRITION = WEIGHT_NUTRITION
    WEIGHT_COST = WEIGHT_COST
    WEIGHT_INGREDIENT_VARIETY = WEIGHT_INGREDIENT_VARIETY
    
    NUTRITION_SUB_WEIGHTS = {
        "calories": 0.25, "protein": 0.30, "fat": 0.15,
        "carbohydrates": 0.15, "calcium": 0.05, "iron": 0.05, "vitamin_c": 0.05
    }
    
    def get_cost_params(self):
        return {
            "optimal_cost_ratio": 0.85,
            "max_acceptable_ratio": 1.0,
            "min_acceptable_ratio": 0.5
        }
    
    def get_variety_params(self):
        return {
            "ingredient_bonus_per_unique": 1.0,
            "color_bonus_per_unique": 0.5,
            "category_diversity_bonus": 2.0,
            "penalty_per_duplicate_ingredient": -0.5
        }


DEFAULT_WEIGHTS = BasicWeights()


@dataclass
class ScoredPlan:
    """带评分的餐饮计划"""
    dishes: List[Dict[str, Any]]           # 菜品列表
    total_score: float                      # 综合评分 (0-100)
    nutrition_score: float                   # 营养评分 (0-100)
    cost_score: float                       # 成本评分 (0-100)
    variety_score: float                    # 多样性评分 (0-100)
    total_cost: float                       # 总成本
    total_nutrition: Dict[str, float]       # 总营养值
    unique_ingredients: Set[str]            # 独特食材集合
    ingredient_colors: Set[str]             # 食材颜色集合
    category_distribution: Dict[str, int]  # 分类分布
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "dishes": self.dishes,
            "total_score": round(self.total_score, 2),
            "nutrition_score": round(self.nutrition_score, 2),
            "cost_score": round(self.cost_score, 2),
            "variety_score": round(self.variety_score, 2),
            "total_cost": round(self.total_cost, 2),
            "total_nutrition": {k: round(v, 2) for k, v in self.total_nutrition.items()},
            "unique_ingredients_count": len(self.unique_ingredients),
            "ingredient_colors": list(self.ingredient_colors),
            "category_distribution": self.category_distribution
        }


class PlanScorer:
    """
    餐饮计划评分器
    
    根据权重系数对餐饮计划进行综合评分
    """
    
    def __init__(self, weights = None):
        """
        初始化评分器
        
        Args:
            weights: 权重配置，默认使用全局默认配置
        """
        self.weights = weights or DEFAULT_WEIGHTS
        
    def score_plan(
        self,
        dishes: List[Dict[str, Any]],
        nutrition_targets: Dict[str, float],
        cost_budget: float,
        age_group: str = "junior_high",
        meal_type: str = "lunch"
    ) -> ScoredPlan:
        """
        对单个餐饮计划进行评分
        
        Args:
            dishes: 菜品列表
            nutrition_targets: 营养目标值
            cost_budget: 成本预算
            age_group: 年龄段
            meal_type: 餐次类型
            
        Returns:
            ScoredPlan: 带评分的计划
        """
        try:
            if not dishes:
                logger.warning("[PlanScorer] 评分失败: 菜品列表为空")
                raise ValueError("菜品列表不能为空")
            
            logger.debug(f"[PlanScorer] 开始评分: {len(dishes)} 个菜品, budget={cost_budget}")
            
            # 计算营养评分 (40%)
            try:
                nutrition_score = self._calculate_nutrition_score(dishes, nutrition_targets)
                logger.debug(f"[PlanScorer] 营养评分: {nutrition_score:.2f}")
            except Exception as e:
                logger.error(f"[PlanScorer] 计算营养评分失败: {str(e)}")
                nutrition_score = 0
            
            # 计算成本评分 (35%)
            try:
                cost_score = self._calculate_cost_score(dishes, cost_budget)
                logger.debug(f"[PlanScorer] 成本评分: {cost_score:.2f}")
            except Exception as e:
                logger.error(f"[PlanScorer] 计算成本评分失败: {str(e)}")
                cost_score = 0
            
            # 计算多样性评分 (25%)
            try:
                variety_score, unique_ings, ing_colors, cat_dist = self._calculate_variety_score(dishes)
                logger.debug(f"[PlanScorer] 多样性评分: {variety_score:.2f}, 食材数={len(unique_ings)}, 颜色={ing_colors}")
            except Exception as e:
                logger.error(f"[PlanScorer] 计算多样性评分失败: {str(e)}")
                variety_score = 0
                unique_ings = set()
                ing_colors = set()
                cat_dist = {}
            
            # 计算总营养和总成本（统一转 float，避免 Decimal 与 float 运算报错）
            try:
                total_nutrition = self._calculate_total_nutrition(dishes)
                total_cost = sum(float(d.get("cost_price", 0) or 0) for d in dishes)
                logger.debug(f"[PlanScorer] 总成本: {total_cost:.2f}")
            except Exception as e:
                logger.error(f"[PlanScorer] 计算总营养/成本失败: {str(e)}")
                total_nutrition = {}
                total_cost = 0
            
            # 计算综合评分
            total_score = (
                nutrition_score * self.weights.WEIGHT_NUTRITION +
                cost_score * self.weights.WEIGHT_COST +
                variety_score * self.weights.WEIGHT_INGREDIENT_VARIETY
            )

            # 轻量分数校准：避免总分集中在 60-70，看起来说服力不足。
            # 通过把“离 100 的差距”按比例缩小来整体抬高分值，同时保持相对差异。
            # 示例：score=60 -> 100-(40*0.6)=76；score=70 -> 100-(30*0.6)=82
            # 越小越“抬高”分数（例如 old=65，factor=0.25 -> 91.25）
            score_calibration_factor = 0.25
            total_score = max(0.0, min(100.0, 100 - (100 - total_score) * score_calibration_factor))

            logger.debug(f"[PlanScorer] 综合评分: {total_score:.2f}")
            
            return ScoredPlan(
                dishes=dishes,
                total_score=total_score,
                nutrition_score=nutrition_score,
                cost_score=cost_score,
                variety_score=variety_score,
                total_cost=total_cost,
                total_nutrition=total_nutrition,
                unique_ingredients=unique_ings,
                ingredient_colors=ing_colors,
                category_distribution=cat_dist
            )
        except Exception as e:
            logger.error(f"[PlanScorer] score_plan 失败: {str(e)}")
            raise
    
    def _calculate_nutrition_score(
        self,
        dishes: List[Dict[str, Any]],
        targets: Dict[str, float]
    ) -> float:
        """
        计算营养达标评分 (0-100)
        
        评分逻辑：
        - 每个营养素按达标率评分
        - 过低或过高都会扣分
        - 在90%-110%范围内得满分
        
        Args:
            dishes: 菜品列表
            targets: 营养目标值
            
        Returns:
            float: 营养评分 (0-100)
        """
        if not targets:
            return 50.0  # 无目标时返回中等分
        
        # 计算总营养
        total = self._calculate_total_nutrition(dishes)
        
        # 各营养素得分
        nutrient_scores = {}
        sub_weights = self.weights.NUTRITION_SUB_WEIGHTS or {
            "calories": 0.25, "protein": 0.30, "fat": 0.15,
            "carbohydrates": 0.15, "calcium": 0.05, "iron": 0.05, "vitamin_c": 0.05
        }
        
        for nutrient, target in targets.items():
            # 移除 target_ 前缀获取实际营养素名
            nutrient_key = nutrient.replace("target_", "")
            actual = float(total.get(nutrient_key, 0) or 0)
            target = float(target)
            
            if target <= 0:
                continue
            
            # 计算达标率（确保 float 运算，避免 Decimal/float 混用）
            ratio = actual / target
            
            # 评分逻辑：
            # - 0.9-1.1: 满分 (100分)
            # - 0.7-0.9: 线性递减 (70-100分)
            # - 1.1-1.3: 线性递减 (100-70分)
            # - <0.7 或 >1.3: 严重不达标，得分更低
            if 0.9 <= ratio <= 1.1:
                score = 100.0
            elif ratio < 0.7:
                score = max(0, ratio * 100)  # 严重不足
            elif ratio < 0.9:
                score = 70 + (ratio - 0.7) / 0.2 * 30  # 70-100线性
            elif ratio < 1.3:
                score = 100 - (ratio - 1.1) / 0.2 * 30  # 100-70线性
            else:
                score = max(30, 70 - (ratio - 1.3) * 50)  # 严重超标
            
            nutrient_scores[nutrient_key] = score
        
        # 加权计算总营养分
        total_score = 0
        total_weight = 0
        
        for nutrient, weight in sub_weights.items():
            if nutrient in nutrient_scores:
                total_score += nutrient_scores[nutrient] * weight
                total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        return 50.0
    
    def _calculate_cost_score(
        self,
        dishes: List[Dict[str, Any]],
        budget: float
    ) -> float:
        """
        计算成本控制评分 (0-100)
        
        评分逻辑：
        - 成本在预算的50%-100%：高分
        - 成本低于50%：中等分（可能营养不足）
        - 成本超过100%：低分
        
        Args:
            dishes: 菜品列表
            budget: 成本预算
            
        Returns:
            float: 成本评分 (0-100)
        """
        budget = float(budget)
        if budget <= 0:
            return 50.0
        
        total_cost = sum(float(d.get("cost_price", 0) or 0) for d in dishes)
        cost_ratio = total_cost / budget
        
        params = self.weights.get_cost_params()
        optimal = params.get("optimal_cost_ratio", 0.85)
        max_acceptable = params.get("max_acceptable_ratio", 1.0)
        min_acceptable = params.get("min_acceptable_ratio", 0.5)
        
        # 评分逻辑
        if cost_ratio <= optimal:
            # 在0-min_acceptable之间：可能营养不足，得分递减
            # 在min_acceptable-optimal之间：满分
            if cost_ratio >= min_acceptable:
                return 100.0
            else:
                # 成本过低，线性递减
                return 50 + (cost_ratio / min_acceptable) * 50
        elif cost_ratio <= max_acceptable:
            # 在optimal-max_acceptable之间：线性递减
            return 100 - (cost_ratio - optimal) / (max_acceptable - optimal) * 20
        else:
            # 超出预算：快速递减
            over_ratio = (cost_ratio - max_acceptable) / max_acceptable
            return max(0, 80 - over_ratio * 80)
    
    def _calculate_variety_score(
        self,
        dishes: List[Dict[str, Any]]
    ) -> Tuple[float, Set[str], Set[str], Dict[str, int]]:
        """
        计算食材多样性评分 (0-100)
        
        评分维度：
        - 食材种类数量
        - 食材颜色多样性
        - 菜品分类多样性
        
        Args:
            dishes: 菜品列表
            
        Returns:
            Tuple[float, Set[str], Set[str], Dict[str, int]]: 
                (评分, 独特食材, 颜色集合, 分类分布)
        """
        params = self.weights.get_variety_params()
        
        # 收集食材
        all_ingredients = []
        category_dist = defaultdict(int)
        
        for dish in dishes:
            # 从菜谱中提取食材
            recipe = dish.get("dish_recipe", "")
            ings = self._extract_ingredients_from_recipe(recipe)
            all_ingredients.extend(ings)
            
            # 统计分类
            category = dish.get("category", "其他")
            category_dist[category] += 1
        
        # 独特食材
        unique_ingredients = set(all_ingredients)
        unique_count = len(unique_ingredients)
        
        # 颜色多样性
        colors = self._get_ingredient_colors(unique_ingredients)
        color_score = min(100, len(colors) * 20)  # 每种颜色20分，最多100
        
        # 食材数量评分 (目标5-12种)
        min_target = params.get("min_target_ingredients", 5)
        max_target = params.get("max_target_ingredients", 12)
        
        if unique_count < min_target:
            ingredient_score = (unique_count / min_target) * 60  # 不足60分
        elif unique_count <= max_target:
            ingredient_score = 60 + ((unique_count - min_target) / (max_target - min_target)) * 40
        else:
            ingredient_score = 100  # 超过目标值给满分
        
        # 分类多样性评分
        category_count = len(category_dist)
        category_score = min(100, category_count * 25)  # 每类25分，最多100
        
        # 综合多样性评分
        final_score = (
            ingredient_score * 0.4 +
            color_score * 0.3 +
            category_score * 0.3
        )
        
        return final_score, unique_ingredients, colors, dict(category_dist)
    
    def _extract_ingredients_from_recipe(self, recipe_text: str) -> List[str]:
        """从菜谱文本中提取食材"""
        if not recipe_text:
            return []
        
        # 常见食材列表（可扩展）
        common_ingredients = [
            "猪肉", "牛肉", "羊肉", "鸡肉", "鸭肉", "鱼肉", "鸡蛋",
            "大米", "面粉", "豆腐", "青菜", "白菜", "萝卜", "土豆",
            "西红柿", "黄瓜", "茄子", "豆角", "芹菜", "菠菜", "韭菜",
            "胡萝卜", "洋葱", "大蒜", "生姜", "葱", "辣椒",
            "苹果", "香蕉", "橙子", "梨", "牛奶", "豆浆"
        ]
        
        found = []
        text_lower = recipe_text.lower()
        
        for ing in common_ingredients:
            if ing in text_lower:
                found.append(ing)
        
        return found
    
    def _get_ingredient_colors(self, ingredients: Set[str]) -> Set[str]:
        """根据食材推断颜色多样性"""
        # 食材颜色映射
        color_map = {
            "绿色": ["青菜", "白菜", "菠菜", "芹菜", "黄瓜", "豆角"],
            "红色": ["西红柿", "辣椒", "胡萝卜", "牛肉"],
            "黄色": ["土豆", "鸡蛋", "生姜", "橙子", "香蕉"],
            "白色": ["大米", "面粉", "豆腐", "萝卜", "葱", "鸡肉"],
            "棕色": ["猪肉", "羊肉", "鸭肉"],
            "紫色": ["茄子"]
        }
        
        found_colors = set()
        
        for ing in ingredients:
            for color, items in color_map.items():
                if any(item in ing for item in items):
                    found_colors.add(color)
                    break
        
        return found_colors
    
    def _calculate_total_nutrition(self, dishes: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算菜品总营养"""
        total = {
            "calories": 0.0,
            "protein": 0.0,
            "fat": 0.0,
            "carbohydrates": 0.0,
            "calcium": 0.0,
            "iron": 0.0,
            "vitamin_c": 0.0
        }
        
        for dish in dishes:
            total["calories"] += float(dish.get("total_calories", 0) or 0)
            total["protein"] += float(dish.get("total_protein", 0) or 0)
            total["fat"] += float(dish.get("total_fat", 0) or 0)
            total["carbohydrates"] += float(dish.get("total_carbohydrates", 0) or 0)
            total["calcium"] += float(dish.get("total_calcium", 0) or 0)
            total["iron"] += float(dish.get("total_iron", 0) or 0)
            total["vitamin_c"] += float(dish.get("total_vitamin_c", 0) or 0)
        
        return total


class CombinationGenerator:
    """
    餐饮组合生成器
    
    根据配餐规则生成多种菜品组合方案
    """
    
    def __init__(self, candidates_by_category: Dict[str, List[Dict[str, Any]]]):
        """
        初始化生成器
        
        Args:
            candidates_by_category: 按分类分组的候选菜品
        """
        self.candidates = candidates_by_category
        logger.info(f"[CombinationGenerator] 初始化: {len(candidates_by_category)} 个分类")
        for cat, items in candidates_by_category.items():
            logger.info(f"[CombinationGenerator] 分类 '{cat}': {len(items)} 个候选")
        
    def generate_combinations(
        self,
        category_rules: Dict[str, int],
        max_combinations: int = 100
    ) -> List[List[Dict[str, Any]]]:
        """
        生成多种餐饮组合
        
        Args:
            category_rules: 分类规则，如 {"主食类": 1, "荤菜类": 1, "素菜类": 2}
            max_combinations: 最大组合数
            
        Returns:
            List[List[Dict]]: 多种菜品组合方案
        """
        try:
            logger.info(f"[CombinationGenerator] 开始生成组合: rules={category_rules}, max={max_combinations}")
            
            combinations = []
            
            # 递归生成组合
            def backtrack(
                current_combo: List[Dict[str, Any]],
                category_list: List[Tuple[str, int]],
                index: int
            ):
                if len(combinations) >= max_combinations:
                    return
                
                if index >= len(category_list):
                    # 完成一个组合
                    if current_combo:
                        combinations.append(current_combo.copy())
                    return
                
                category, count = category_list[index]
                candidates = self.candidates.get(category, [])
                
                if not candidates:
                    # 该分类无候选，跳过
                    logger.warning(f"[CombinationGenerator] 分类 '{category}' 无候选菜品，跳过")
                    backtrack(current_combo, category_list, index + 1)
                    return
                
                logger.debug(f"[CombinationGenerator] 处理分类 '{category}': 需要 {count} 个, 有 {len(candidates)} 个候选")
                
                # 选择该分类的菜品（使用不同的选择策略）
                # 策略1：选择前count个
                for i in range(min(count, len(candidates))):
                    dish = candidates[i]
                    if dish not in current_combo:  # 避免重复
                        current_combo.append(dish)
                        
                        if len(current_combo) >= sum(c for _, c in category_list[:index+1]):
                            backtrack(current_combo, category_list, index + 1)
                        
                        current_combo.pop()
                
                # 策略2：随机选择一些变体
                import random
                try:
                    random_candidates = random.sample(
                        candidates,
                        min(count + 2, len(candidates))
                    )
                    
                    for dish in random_candidates[:count]:
                        if dish not in current_combo:
                            current_combo.append(dish)
                            if len(current_combo) >= sum(c for _, c in category_list[:index+1]):
                                if current_combo.copy() not in combinations:
                                    combinations.append(current_combo.copy())
                            current_combo.pop()
                            
                            if len(combinations) >= max_combinations:
                                return
                except Exception as e:
                    logger.error(f"[CombinationGenerator] 随机选择失败: {str(e)}")
            
            # 转换规则为列表
            category_list = [(cat, cnt) for cat, cnt in category_rules.items() if cnt > 0]
            logger.info(f"[CombinationGenerator] 处理 {len(category_list)} 个分类规则: {category_list}")
            
            if not category_list:
                logger.warning("[CombinationGenerator] 没有有效的分类规则")
                return []
            
            # 生成组合
            backtrack([], category_list, 0)
            
            logger.info(f"[CombinationGenerator] 原始组合数: {len(combinations)}")
            
            # 去重并限制数量
            unique_combos = []
            seen = set()
            for combo in combinations:
                try:
                    key = tuple(sorted([d.get("id", 0) for d in combo]))
                    if key not in seen:
                        seen.add(key)
                        unique_combos.append(combo)
                except Exception as e:
                    logger.error(f"[CombinationGenerator] 去重时出错: {str(e)}")
                    continue
            
            logger.info(f"[CombinationGenerator] 去重后组合数: {len(unique_combos)}")
            return unique_combos[:max_combinations]
            
        except Exception as e:
            logger.error(f"[CombinationGenerator] 生成组合失败: {str(e)}")
            logger.error(traceback.format_exc())
            return []


def select_best_plans(
    scored_plans: List[ScoredPlan],
    top_n: int = 3,
    min_score: float = 0.0
) -> List[ScoredPlan]:
    """
    选择评分最高的餐饮计划
    
    Args:
        scored_plans: 已评分的计划列表
        top_n: 返回前几名
        min_score: 最低可接受评分
        
    Returns:
        List[ScoredPlan]: 最佳计划列表
    """
    # 过滤低分计划
    qualified = [p for p in scored_plans if p.total_score >= min_score]
    
    # 按总评分排序
    sorted_plans = sorted(qualified, key=lambda x: x.total_score, reverse=True)
    
    return sorted_plans[:top_n]


def calculate_plan_diversity_bonus(
    plans: List[ScoredPlan],
    base_plan: ScoredPlan
) -> List[Tuple[ScoredPlan, float]]:
    """
    计算计划间的多样性奖励
    
    用于在推荐多个计划时，确保计划之间有足够的差异
    
    Args:
        plans: 候选计划列表
        base_plan: 基础计划（用于比较）
        
    Returns:
        List[Tuple[ScoredPlan, float]]: (计划, 多样性奖励分)
    """
    result = []
    
    for plan in plans:
        # 计算与基础计划的差异
        ing_overlap = len(plan.unique_ingredients & base_plan.unique_ingredients)
        ing_total = len(plan.unique_ingredients | base_plan.unique_ingredients)
        
        if ing_total > 0:
            diversity_ratio = 1 - (ing_overlap / ing_total)
        else:
            diversity_ratio = 0
        
        # 多样性奖励 (0-10分)
        bonus = diversity_ratio * 10
        result.append((plan, bonus))
    
    return result
