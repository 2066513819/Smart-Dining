// 简单测试脚本，只测试行匹配逻辑
const testContent = `1. 菜品名称  
 - 菜品类型：晚餐  
 - 菜品名称：山药炖鸡翅  
 - **时令**：冬季（山药、菌菇为时令食材）  
 - **口味**：香浓酱香  
 - **卡路里**：230 kcal  
 - **蛋白质**：18g  
 - **碳水化合物**：15g  
 - **脂肪**：12g  
 - **钙**：85mg  
 - **铁**：4.2mg  
 - **维生素C**：10mg  
 - **配方**：  
   - 鸡翅 300g（去骨）  
   - 山药 200g（去皮切块）  
   - 香菇 50g（泡发）  
   - 洋葱 30g（切丁）  
   - 胡萝卜 50g（切片）  
   - 生姜 10g（切片）  
   - 酱油 15ml  
   - 料酒 10ml  
   - 盐 5g  
   - 食用油 10ml  

2. 菜品名称  
 - 菜品类型：晚餐  
 - 菜品名称：白菜豆腐菌菇汤  
 - **时令**：冬季（白菜、菌菇为时令蔬菜）  
 - **口味**：清鲜微辣  
 - **卡路里**：120 kcal  
 - **蛋白质**：8g  
 - **碳水化合物**：6g  
 - **脂肪**：4g  
 - **钙**：110mg  
 - **铁**：2.5mg  
 - **维生素C**：20mg  
 - **配方**：  
   - 大白菜 150g（切片）  
   - 豆腐 100g（切块）  
   - 蘑菇 50g（泡发）  
   - 香葱 10g（切葱花）  
   - 姜片 5g  
   - 盐 3g  
   - 食用油 5ml  
   - 生抽 10ml  
   - 干辣椒 2个（可选）  

**营养说明**：  
 - **山药炖鸡翅**：山药富含膳食纤维和黏蛋白，有助于暖胃健脾；鸡翅提供优质蛋白质和脂肪，搭配香菇增强风味，钙铁含量适中。  
 - **白菜豆腐菌菇汤**：白菜和菌菇富含维生素C和钾，豆腐提供植物蛋白和钙，汤品清淡易消化，适合冬季补充水分和营养。  

**制作提示**：  
 - 山药需提前浸泡30分钟去皮，炖煮时加姜片去腥。  
 - 豆腐需提前用沸水焯水，菌菇泡发后与白菜同煮，提升汤体鲜味。`;

// 只测试行匹配逻辑
function testLineMatching(content) {
  const dishes = [];
  const lines = content.split('\n');
  let currentDish = null;
  let isInRecipe = false;
  
  console.log('开始行匹配处理，共', lines.length, '行');
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    
    console.log(`处理行 ${i+1}: "${line}"`);
    
    // 检查是否是新菜品开始
    const dishStartMatch = line.match(/^(\d+)\.\s*菜品名称$/);
    if (dishStartMatch) {
      // 保存之前的菜品
      if (currentDish) {
        dishes.push(currentDish);
        console.log(`保存菜品: ${currentDish.name}`);
      }
      
      // 开始新菜品
      currentDish = {
        id: Math.random().toString(36).substr(2, 9),
        name: '',
        meal_type: '',
        season: '',
        flavor: '',
        nutrition: '',
        ingredients: '',
        description: '',
        age_group: '6-8岁小学',
        serving_size: '1人份',
        day: '1天'
      };
      isInRecipe = false;
      console.log('开始新菜品');
      continue;
    }
    
    if (!currentDish) continue;
    
    // 提取菜品名称
    const nameMatch = line.match(/^-\s*菜品名称[:：]\s*(.+)$/);
    if (nameMatch) {
      currentDish.name = nameMatch[1].trim();
      console.log(`提取到菜品名称: ${currentDish.name}`);
      continue;
    }
    
    // 提取菜品类型
    const mealTypeMatch = line.match(/^-\s*菜品类型[:：]\s*(.+)$/);
    if (mealTypeMatch) {
      currentDish.meal_type = mealTypeMatch[1].trim();
      console.log(`提取到菜品类型: ${currentDish.meal_type}`);
      continue;
    }
    
    // 提取时令
    const seasonMatch = line.match(/^-\s*\*\*?时令\*\*?[:：]\s*(.+)$/);
    if (seasonMatch) {
      currentDish.season = seasonMatch[1].trim();
      console.log(`提取到时令: ${currentDish.season}`);
      continue;
    }
    
    // 提取口味
    const flavorMatch = line.match(/^-\s*\*\*?口味\*\*?[:：]\s*(.+)$/);
    if (flavorMatch) {
      currentDish.flavor = flavorMatch[1].trim();
      console.log(`提取到口味: ${currentDish.flavor}`);
      continue;
    }
    
    // 提取营养信息
    const nutritionKeys = ['卡路里', '蛋白质', '碳水化合物', '脂肪', '钙', '铁', '维生素C'];
    let nutritionMatched = false;
    
    for (const key of nutritionKeys) {
      const nutritionMatch = line.match(new RegExp(`^-\s*\*\*?${key}\*\*?[:：]\s*([^\n]+)$`));
      if (nutritionMatch) {
        const value = nutritionMatch[1].trim();
        currentDish.nutrition += (currentDish.nutrition ? '\n' : '') + `${key}：${value}`;
        console.log(`提取到${key}: ${value}`);
        nutritionMatched = true;
        break;
      }
    }
    
    if (nutritionMatched) continue;
    
    // 检查是否开始配方部分
    const recipeStartMatch = line.match(/^-\s*\*\*?配方\*\*?[:：]$/);
    if (recipeStartMatch) {
      isInRecipe = true;
      console.log('开始配方部分');
      continue;
    }
    
    // 提取配料
    if (isInRecipe && line.startsWith('- ')) {
      const ingredient = line.substring(2).trim();
      currentDish.ingredients += (currentDish.ingredients ? '\n' : '') + ingredient;
      console.log(`提取到配料: ${ingredient}`);
      continue;
    }
  }
  
  // 保存最后一道菜品
  if (currentDish) {
    dishes.push(currentDish);
    console.log(`保存最后一道菜品: ${currentDish.name}`);
  }
  
  console.log('\n=== 提取结果 ===');
  console.log('共提取到', dishes.length, '道菜');
  dishes.forEach((dish, index) => {
    console.log(`\n第${index+1}道菜:`);
    console.log('名称:', dish.name);
    console.log('类型:', dish.meal_type);
    console.log('时令:', dish.season);
    console.log('口味:', dish.flavor);
    console.log('营养信息:', dish.nutrition);
    console.log('配料:', dish.ingredients);
  });
  
  return dishes;
}

// 运行测试
console.log('开始测试行匹配逻辑...');
const dishes = testLineMatching(testContent);
console.log('\n测试完成！');
