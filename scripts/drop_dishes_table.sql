-- 删除 dishes 表迁移脚本
-- 说明：dishes 表已废弃，菜品数据现存储在 menu_items 表中
-- 执行前请确认：1) 无业务依赖 dishes 表  2) 已备份重要数据（如需要）

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `dishes`;

SET FOREIGN_KEY_CHECKS = 1;
