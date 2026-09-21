"""
使用 openpyxl 直接读取 Excel 文件（如果已安装）
"""
try:
    from openpyxl import load_workbook

    # 加载 Excel 文件
    wb = load_workbook('26年1月商品入库价格表.xlsx', data_only=True)
    ws = wb.active

    print("=" * 80)
    print("文件名: 26年1月商品入库价格表.xlsx")
    print("=" * 80)
    print(f"\n工作表名称: {ws.title}")
    print(f"总行数: {ws.max_row}")
    print(f"总列数: {ws.max_column}")

    # 获取表头
    print("\n表头列名:")
    for col in range(1, ws.max_column + 1):
        cell_value = ws.cell(1, col).value
        print(f"  列 {col}: {cell_value}")

    # 显示前15行数据
    print("\n" + "=" * 80)
    print("\n前15行数据:")
    for row in range(1, min(16, ws.max_row + 1)):
        print(f"\n第 {row} 行:")
        for col in range(1, min(ws.max_column + 1, 10)):  # 最多显示10列
            cell_value = ws.cell(row, col).value
            print(f"  列{col}: {cell_value}")

    wb.close()

except ImportError:
    print("错误: openpyxl 未安装")
    print("请运行: pip install openpyxl")
except Exception as e:
    print(f"错误: {e}")
