import sys
import pandas as pd

sys.argv
print('args', sys.argv)

month = int(sys.argv[1])

df = pd.DataFrame({"day": [1, 2], "num_passengers": [3, 4]})
df['month'] = month
print(df.head())

df.to_parquet(f"output_{month}.parquet")

print(f"hello month={month}")