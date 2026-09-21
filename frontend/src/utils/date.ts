// 日期格式化工具
import dayjs from 'dayjs'
import timezone from 'dayjs/plugin/timezone'
import utc from 'dayjs/plugin/utc'

// 启用插件
dayjs.extend(utc)
dayjs.extend(timezone)

/**
 * 格式化日期时间（自动处理时区）
 * @param dateString 日期字符串（ISO格式，可能是UTC时间）
 * @param format 格式化模板，默认：YYYY-MM-DD HH:mm:ss
 * @returns 格式化后的本地日期字符串
 */
export const formatDate = (dateString: string, format: string = 'YYYY-MM-DD HH:mm:ss'): string => {
  if (!dateString) return ''
  // 如果字符串包含Z或+00:00，说明是UTC时间，需要转换为本地时间
  // 否则直接解析为本地时间
  const date = dayjs(dateString)
  // 如果原始字符串是UTC时间，使用utc()解析然后转换为本地时间
  if (dateString.includes('Z') || dateString.endsWith('+00:00')) {
    return dayjs.utc(dateString).local().format(format)
  }
  // 否则直接解析并格式化为本地时间
  return date.local().format(format)
}

/**
 * 格式化日期时间为本地时间
 * @param dateString 日期字符串
 * @param format 格式化模板，默认：YYYY-MM-DD HH:mm:ss
 * @returns 格式化后的本地日期字符串
 */
export const formatLocalDate = (dateString: string, format: string = 'YYYY-MM-DD HH:mm:ss'): string => {
  if (!dateString) return ''
  // 如果字符串包含Z或+00:00，说明是UTC时间，需要转换为本地时间
  if (dateString.includes('Z') || dateString.endsWith('+00:00')) {
    return dayjs.utc(dateString).local().format(format)
  }
  // 否则直接解析为本地时间
  return dayjs(dateString).local().format(format)
}
