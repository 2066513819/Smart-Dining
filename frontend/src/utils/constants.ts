export const dishTypeToText = (v: string): string => {
  if (!v) return '未分类'
  if (v === '早餐' || v === '午餐' || v === '晚餐') return v
  switch (v.toLowerCase()) {
    case 'breakfast':
      return '早餐'
    case 'lunch':
      return '午餐'
    case 'dinner':
      return '晚餐'
    default:
      return v
  }
}

export const dishTypeToBackend = (v: string): string => {
  switch (v) {
    case '早餐':
      return 'breakfast'
    case '午餐':
      return 'lunch'
    case '晚餐':
      return 'dinner'
    default:
      return v
  }
}

export const ageGroupCodeToText = (code: string): string => {
  switch (code) {
    case 'primary':
      return '小学'
    case 'junior_low':
      return '初中低龄'
    case 'junior_high':
      return '初中高龄'
    case 'senior':
      return '高中'
    default:
      return code || '小学'
  }
}

export const AGE_GROUP_SCALE: Record<string, number> = {
  小学: 0.8,
  初中低龄: 0.9,
  初中高龄: 1.0,
  高中: 1.1,
}

