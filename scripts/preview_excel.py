import pandas as pd

# 读取 Excel 文件
df = pd.read_excel('26年1月商品入库价格表.xlsx')

print("=" * 80)
print("文件名: 26年1月商品入库价格表.xlsx")
print("=" * 80)
print(f"\n总行数: {len(df)}")
print(f"\n列名: {list(df.columns)}")
print("\n" + "=" * 80)
print("\n前10行数据预览:")
print(df.head(10).to_string())
print("\n" + "=" * 80)
print("\n数据类型:")
print(df.dtypes)
print("\n" + "=" * 80)
print("\n缺失值统计:")
print(df.isnull().sum())
print("\n" + "=" * 80)
