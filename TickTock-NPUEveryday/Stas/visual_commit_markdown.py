import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
import calendar

def scan_all_photos_in_directory(base_directory):
    """
    扫描基础目录下所有子文件夹中的照片
    返回按日期分组的照片统计
    """
    photo_stats = defaultdict(int)  # key: 'YYYY-MM-DD', value: count
    
    if not os.path.exists(base_directory):
        print(f"错误：目录 {base_directory} 不存在")
        return photo_stats
    
    print(f"正在扫描目录：{base_directory}")
    folder_count = 0
    total_photos = 0
    
    # 遍历所有子文件夹
    for item in os.listdir(base_directory):
        item_path = os.path.join(base_directory, item)
        
        # 只处理文件夹
        if os.path.isdir(item_path):
            folder_count += 1
            folder_photos = 0
            
            # 扫描文件夹中的照片
            try:
                for filename in os.listdir(item_path):
                    if filename.startswith("IMG_") and filename.endswith(".jpg"):
                        try:
                            # 从文件名提取日期：IMG_20230901_114129.jpg
                            date_str = filename[4:12]  # 20230901
                            date_obj = datetime.strptime(date_str, "%Y%m%d")
                            date_key = date_obj.strftime("%Y-%m-%d")
                            
                            photo_stats[date_key] += 1
                            folder_photos += 1
                            total_photos += 1
                            
                        except ValueError:
                            # 如果日期解析失败，跳过这个文件
                            continue
                            
            except PermissionError:
                print(f"警告：无法访问文件夹 {item_path}")
                continue
            
            if folder_photos > 0:
                print(f"  📁 {item}: {folder_photos} 张照片")
    
    print(f"\n扫描完成：")
    print(f"  📁 总文件夹数：{folder_count}")
    print(f"  📸 总照片数：{total_photos}")
    print(f"  📅 拍照天数：{len(photo_stats)}")
    
    return photo_stats

def generate_date_range(start_date, end_date):
    """
    生成指定日期范围内的所有日期
    """
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates

def validate_date_handling():
    """
    验证日期处理的正确性，特别是月份天数和闰年
    """
    print("\n🔍 验证日期处理...")
    
    test_cases = [
        (2023, 2),  # 2023年2月 - 平年，28天
        (2024, 2),  # 2024年2月 - 闰年，29天
        (2025, 2),  # 2025年2月 - 平年，28天
        (2023, 4),  # 2023年4月 - 30天
        (2023, 12), # 2023年12月 - 31天
    ]
    
    for year, month in test_cases:
        days_in_month = calendar.monthrange(year, month)[1]
        is_leap = calendar.isleap(year)
        
        print(f"  {year}年{month:02d}月：{days_in_month}天", end="")
        if month == 2:
            print(f" ({'闰年' if is_leap else '平年'})", end="")
        print()
    
    print("✅ 日期处理验证完成")



def generate_github_style_commit_markdown(photo_stats, start_date, end_date):
    """
    生成GitHub风格的commit图表Markdown内容
    """
    markdown_content = []
    
    # 标题和基本信息
    markdown_content.append("# 📊 NPU每日拍照记录 - GitHub风格提交图")
    markdown_content.append("")
    
    # 找到开始日期所在周的周一
    start_weekday = start_date.weekday()  # 0=周一, 6=周日
    actual_start = start_date - timedelta(days=start_weekday)
    
    markdown_content.append(f"**图表范围：** {actual_start.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    markdown_content.append(f"**开始日期：** {start_date.strftime('%Y-%m-%d')} ({['周一','周二','周三','周四','周五','周六','周日'][start_weekday]})")
    markdown_content.append("")
    
    # 图例
    markdown_content.append("## 📋 图例")
    markdown_content.append("- ✅ 有拍照")
    markdown_content.append("- ❌ 未拍照") 
    markdown_content.append("- ⬜ 统计范围外")
    markdown_content.append("")
    
    # 提交图表
    markdown_content.append("## 📅 拍照提交图")
    markdown_content.append("")
    markdown_content.append("```")
    markdown_content.append("       周一 周二 周三 周四 周五 周六 周日")
    markdown_content.append("     ────────────────────────────────")
    
    current_date = actual_start
    week_count = 0
    
    while current_date <= end_date:
        # 每周开始时添加年月信息
        if current_date.weekday() == 0:  # 周一
            week_count += 1
            year_month = current_date.strftime("%y.%m")
            line = f"{year_month} │"
        
        # 判断当前日期的状态
        date_key = current_date.strftime("%Y-%m-%d")
        
        if current_date < start_date or current_date > end_date:
            symbol = "⬜"
        elif date_key in photo_stats:
            symbol = "✅"
        else:
            symbol = "❌"
        
        line += f" {symbol} "
        
        # 如果是周日，添加到markdown内容并换行
        if current_date.weekday() == 6:
            markdown_content.append(line)
        
        current_date += timedelta(days=1)
    
    # 如果最后一行不完整，也要添加
    if current_date.weekday() != 0:
        markdown_content.append(line)
    
    markdown_content.append("```")
    markdown_content.append("")
    
    return markdown_content

def generate_statistics_markdown(photo_stats, start_date, end_date):
    """
    生成统计信息的Markdown内容
    """
    markdown_content = []
    
    # 总体统计
    total_days = (end_date - start_date).days + 1
    photo_days = len(photo_stats)
    total_photos = sum(photo_stats.values())
    no_photo_days = total_days - photo_days
    photo_rate = (photo_days / total_days) * 100
    avg_photos_per_day = total_photos / photo_days if photo_days > 0 else 0
    
    markdown_content.append("## 📊 统计汇总")
    markdown_content.append("")
    markdown_content.append("| 项目 | 数值 |")
    markdown_content.append("|------|------|")
    markdown_content.append(f"| 📅 统计期间 | {start_date.strftime('%Y年%m月%d日')} - {end_date.strftime('%Y年%m月%d日')} |")
    markdown_content.append(f"| 📈 总天数 | {total_days} 天 |")
    markdown_content.append(f"| ✅ 拍照天数 | {photo_days} 天 |")
    markdown_content.append(f"| ❌ 未拍天数 | {no_photo_days} 天 |")
    markdown_content.append(f"| 📸 总照片数 | {total_photos} 张 |")
    markdown_content.append(f"| 📊 拍照率 | {photo_rate:.1f}% |")
    markdown_content.append(f"| 📷 平均每拍照日 | {avg_photos_per_day:.1f} 张 |")
    markdown_content.append("")
    
    return markdown_content

def generate_yearly_statistics_markdown(photo_stats, start_date, end_date):
    """
    生成年度统计的Markdown内容
    """
    markdown_content = []
    markdown_content.append("## 📊 年度统计报告")
    markdown_content.append("")
    
    # 按年份分组统计
    yearly_stats = defaultdict(lambda: {'total_photos': 0, 'photo_days': 0, 'total_days': 0})
    
    current_date = start_date
    while current_date <= end_date:
        year = current_date.year
        date_key = current_date.strftime("%Y-%m-%d")
        
        yearly_stats[year]['total_days'] += 1
        
        if date_key in photo_stats:
            yearly_stats[year]['total_photos'] += photo_stats[date_key]
            yearly_stats[year]['photo_days'] += 1
        
        current_date += timedelta(days=1)
    
    # 生成年度统计表格
    markdown_content.append("| 年份 | 总天数 | 拍照天数 | 未拍天数 | 总照片数 | 拍照率 |")
    markdown_content.append("|------|--------|----------|----------|----------|--------|")
    
    for year in sorted(yearly_stats.keys()):
        stats = yearly_stats[year]
        photo_rate = (stats['photo_days'] / stats['total_days']) * 100 if stats['total_days'] > 0 else 0
        is_leap = calendar.isleap(year)
        year_label = f"{year}年{'(闰年)' if is_leap else '(平年)'}"
        
        markdown_content.append(f"| {year_label} | {stats['total_days']} 天 | {stats['photo_days']} 天 | {stats['total_days'] - stats['photo_days']} 天 | {stats['total_photos']} 张 | {photo_rate:.1f}% |")
    
    markdown_content.append("")
    return markdown_content

def generate_monthly_chart_markdown(photo_stats, start_date, end_date):
    """
    生成按月图表的Markdown内容
    """
    markdown_content = []
    markdown_content.append("## 📅 按月拍照情况")
    markdown_content.append("")
    
    current_date = start_date
    current_year_month = None
    day_count = 0
    line = ""
    
    while current_date <= end_date:
        year_month = current_date.strftime("%Y年%m月")
        date_key = current_date.strftime("%Y-%m-%d")
        
        # 如果是新的月份
        if year_month != current_year_month:
            # 先关闭上一个月份的代码块
            if current_year_month is not None:
                # 如果有未完成的行，先输出
                if line.strip():
                    week_start = max(1, day_count - len(line.strip().split()) + 1)
                    week_end = day_count
                    markdown_content.append(f"{week_start:2d}-{week_end:2d}日: {line.strip()}")
                markdown_content.append("```")
                markdown_content.append("")  # 月份之间空一行
            
            # 开始新的月份
            markdown_content.append(f"### {year_month}")
            markdown_content.append("")
            markdown_content.append("```")
            current_year_month = year_month
            day_count = 0
            line = ""
        
        day_count += 1
        
        # 添加当天数据
        if date_key in photo_stats:
            symbol = "✅"
        else:
            symbol = "❌"
        
        line += f"{symbol} "
        
        # 每7天一行或月末
        days_in_current_month = calendar.monthrange(current_date.year, current_date.month)[1]
        if day_count % 7 == 0 or day_count == days_in_current_month:
            week_start = max(1, day_count - 6)
            week_end = day_count
            markdown_content.append(f"{week_start:2d}-{week_end:2d}日: {line.strip()}")
            line = ""
        
        current_date += timedelta(days=1)
    
    # 关闭最后一个月份的代码块
    if line.strip():
        week_start = max(1, day_count - len(line.strip().split()) + 1)
        week_end = day_count
        markdown_content.append(f"{week_start:2d}-{week_end:2d}日: {line.strip()}")
    
    markdown_content.append("```")
    markdown_content.append("")
    
    return markdown_content



def main():
    """
    主函数
    """
    print("=" * 80)
    print("📸 NPU-Everyday 全量照片统计系统")
    print("📅 统计期间：2023.09.01 - 2026.04.01")
    print("=" * 80)
    
    # 获取 NPU-Everyday 目录路径
    # base_directory = input("\n请输入 NPU-Everyday 目录路径: ").strip()

    base_directory = r"D:\DevProj\TickTock-NPUEveryday\NPU-Everyday"

    # 去除可能的引号
    if base_directory.startswith('"') and base_directory.endswith('"'):
        base_directory = base_directory[1:-1]
    
    if not base_directory:
        print("❌ 请输入有效的目录路径")
        return
    
    # 定义统计日期范围
    start_date = datetime(2023, 9, 1)
    end_date = datetime(2026, 4, 30)
    
    print(f"开始统计时间范围：{start_date.strftime('%Y年%m月%d日')} - {end_date.strftime('%Y年%m月%d日')}")
    
    # 扫描所有照片
    print("\n🔍 开始扫描照片...")
    photo_stats = scan_all_photos_in_directory(base_directory)
    
    if not photo_stats:
        print("❌ 没有找到任何照片文件")
        return
    
    # 验证日期处理
    validate_date_handling()
    
    # 生成Markdown文件
    print("\n📝 生成Markdown报告...")
    
    # 构建完整的Markdown内容
    markdown_content = []
    
    # 添加各部分内容
    markdown_content.extend(generate_github_style_commit_markdown(photo_stats, start_date, end_date))
    markdown_content.extend(generate_statistics_markdown(photo_stats, start_date, end_date))
    markdown_content.extend(generate_yearly_statistics_markdown(photo_stats, start_date, end_date))
    markdown_content.extend(generate_monthly_chart_markdown(photo_stats, start_date, end_date))
    
    # 写入Markdown文件
    output_filename = "NPU_Photo_Statistics_Report.md"
    output_path = os.path.join(os.path.dirname(__file__), output_filename)
    
    try:
        markdown_text = '\n'.join(markdown_content)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)
        
        print(f"✅ Markdown报告已生成：{output_path}")
        print(f"📄 文件大小：{len(markdown_text)} 字符")
        
    except Exception as e:
        print(f"❌ 生成Markdown文件时出错：{e}")
        return
    
    # 显示简要统计信息
    total_days = (end_date - start_date).days + 1
    photo_days = len(photo_stats)
    total_photos = sum(photo_stats.values())
    photo_rate = (photo_days / total_days) * 100
    
    print(f"\n📊 生成报告完成！")
    print(f"� 统计了 {total_days} 天的数据")
    print(f"✅ 其中 {photo_days} 天有拍照 ({photo_rate:.1f}%)")
    print(f"📸 总共 {total_photos} 张照片")
    print(f"� 详细信息请查看生成的Markdown文件")

if __name__ == "__main__":
    main()