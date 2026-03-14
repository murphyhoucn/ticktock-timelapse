from datetime import datetime
import calendar

# 查看2023年9月1日是星期几
date_2023_09_01 = datetime(2023, 9, 1)
weekday = date_2023_09_01.weekday()  # 0=周一, 6=周日
weekday_name = calendar.day_name[weekday]

print(f"2023年9月1日是：{weekday_name} (数字代码: {weekday})")
print("0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday")