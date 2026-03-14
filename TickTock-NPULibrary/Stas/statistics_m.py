import os
import re
from collections import defaultdict
from datetime import datetime, timedelta

def extract_year_month_from_folder(folder_path):
    """
    从文件夹名称中提取年月信息
    支持格式：YYYY.MM, YYYY-MM, YYYY_MM 等
    """
    folder_name = os.path.basename(folder_path)
    
    # 匹配 YYYY.MM, YYYY-MM, YYYY_MM 格式
    patterns = [
        r'(\d{4})[.\-_](\d{1,2})',  # 2025.06, 2025-06, 2025_06
        r'(\d{4})(\d{2})',          # 202506
    ]
    
    for pattern in patterns:
        match = re.search(pattern, folder_name)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            if 1 <= month <= 12:
                return year, month
    
    return None, None

def get_photo_statistics(folder_path, year=None, month=None, auto_detect=True):
    """
    统计照片文件夹中的拍照情况
    
    Args:
        folder_path: 照片文件夹路径
        year: 指定年份，如果为None则根据auto_detect决定是否自动检测
        month: 指定月份，如果为None则根据auto_detect决定是否自动检测
        auto_detect: 是否自动从文件夹名称提取年月
    """
    if not os.path.exists(folder_path):
        print(f"错误：文件夹 {folder_path} 不存在")
        return
    
    # 自动检测年月（如果启用且未手动指定）
    if auto_detect and year is None and month is None:
        detected_year, detected_month = extract_year_month_from_folder(folder_path)
        if detected_year and detected_month:
            year, month = detected_year, detected_month
            print(f"🔍 自动检测到年月：{year}年{month}月")
    
    # 统计每天的照片数量
    day_count = defaultdict(int)
    all_dates = set()
    
    # 遍历文件夹，统计每天的照片数量
    for filename in os.listdir(folder_path):
        if filename.startswith("IMG_") and filename.endswith(".jpg"):
            try:
                date_str = filename[4:12]  # 20250601
                date_obj = datetime.strptime(date_str, "%Y%m%d")
                
                # 如果指定了年份和月份，只统计该月
                if year is not None and month is not None:
                    if date_obj.year == year and date_obj.month == month:
                        day_count[date_obj.day] += 1
                        all_dates.add(date_obj)
                # 如果只指定了年份，统计整年
                elif year is not None and month is None:
                    if date_obj.year == year:
                        key = f"{date_obj.month:02d}-{date_obj.day:02d}"
                        day_count[key] += 1
                        all_dates.add(date_obj)
                # 如果都没指定，统计所有
                else:
                    key = f"{date_obj.year}-{date_obj.month:02d}-{date_obj.day:02d}"
                    day_count[key] += 1
                    all_dates.add(date_obj)
            except Exception as e:
                print(f"警告：无法解析文件名 {filename}: {e}")
                continue
    
    # 输出统计结果
    if year is not None and month is not None:
        # 统计指定月份
        print(f"\n{year}年{month}月拍照统计")
        print(f"文件夹：{folder_path}")
        print("-" * 50)
        
        # 获取该月的天数
        first_day = datetime(year, month, 1)
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        days_in_month = (next_month - first_day).days
        
        total_photos = 0
        photo_days = 0
        
        for day in range(1, days_in_month + 1):
            count = day_count.get(day, 0)
            if count == 0:
                print(f"{day:02d}日：未拍照")
            else:
                print(f"{day:02d}日：{count} 张照片")
                total_photos += count
                photo_days += 1
        
        print("-" * 50)
        print(f"统计汇总：")
        print(f"   总照片数：{total_photos} 张")
        print(f"   拍照天数：{photo_days} 天")
        print(f"   未拍天数：{days_in_month - photo_days} 天")
        print(f"   拍照率：{photo_days/days_in_month*100:.1f}%")
        
    else:
        # 统计所有日期
        print(f"\n照片统计")
        print(f"文件夹：{folder_path}")
        print("-" * 50)
        
        sorted_dates = sorted(all_dates)
        total_photos = sum(day_count.values())
        
        for date_obj in sorted_dates:
            if year is not None:
                key = f"{date_obj.month:02d}-{date_obj.day:02d}"
                date_str = f"{date_obj.month:02d}月{date_obj.day:02d}日"
            else:
                key = f"{date_obj.year}-{date_obj.month:02d}-{date_obj.day:02d}"
                date_str = f"{date_obj.year}年{date_obj.month:02d}月{date_obj.day:02d}日"
            
            count = day_count[key]
            print(f"{date_str}：{count} 张照片")
        
        print("-" * 50)
        print(f"统计汇总：")
        print(f"   总照片数：{total_photos} 张")
        print(f"   拍照天数：{len(sorted_dates)} 天")

def main():
    """
    主函数 - 交互式照片统计工具
    """
    print("=" * 60)
    print("照片拍摄统计工具")
    print("=" * 60)
    print("输入照片文件夹路径进行统计，输入 'q' 退出")
    print("支持自动检测文件夹名中的年月信息 (如: 2023.10)")
    
    while True:
        folder_path = input("\n请输入照片文件夹路径 (或输入 q 退出): ").strip()
        
        # 检查退出条件
        if folder_path.lower() == 'q':
            print("\n再见！")
            break
        
        # 去除可能的引号
        if folder_path.startswith('"') and folder_path.endswith('"'):
            folder_path = folder_path[1:-1]
        
        if not folder_path:
            print("请输入有效的文件夹路径")
            continue
        
        # 直接执行统计，自动检测年月
        get_photo_statistics(folder_path, auto_detect=True)

if __name__ == "__main__":
    main()