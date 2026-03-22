#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NPU-Everyday 完整统计分析工具
整合Markdown报告和PNG图表生成功能
"""

import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
import calendar
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import warnings

# 抑制字体相关警告
warnings.filterwarnings('ignore', message='.*missing from font.*')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

if os.name == 'nt':  # Windows
    font_priority = [
        'SimHei',              # 黑体
        'Microsoft YaHei',      # 微软雅黑
        'SimSun',              # 宋体
        'AR PL UKai CN',       # 文鼎楷体
        'AR PL UMing CN',      # 文鼎明体
        'sans-serif'
    ]
    system_name = "Windows"
else:  # Linux - 使用实际检测到的字体
    font_priority = [
        'Noto Sans CJK JP',        # Google Noto字体 ✅ 已验证支持中文
        'Noto Serif CJK JP',       # Google Noto衬线字体 ✅ 已验证支持中文
        'AR PL UKai CN',           # 文鼎楷体 ✅ 已验证支持中文
        'AR PL UMing CN',          # 文鼎明体 ✅ 已验证支持中文
        'Droid Sans Fallback',     # Android字体
        'sans-serif'
    ]
    system_name = "Linux"

# 设置字体
plt.rcParams['font.sans-serif'] = font_priority
plt.rcParams['axes.unicode_minus'] = False

current_font = plt.rcParams['font.sans-serif'][0]
# 定义跨平台字体变量，用于绘图
CHINESE_FONT = font_priority[0]  # 使用第一个可用的中文字体
print(f"当前使用的字体: {current_font} ({system_name})")
print(f"绘图使用字体: {CHINESE_FONT}")

class NPUPhotoAnalyzer:
    """NPU照片统计分析器"""
    
    def __init__(self, base_directory):
        """
        初始化分析器
        
        Args:
            base_directory (str): NPU-Everyday目录路径
        """
        self.base_directory = base_directory
        self.photo_stats = defaultdict(int)  # key: 'YYYY-MM-DD', value: count
        
    def scan_all_photos(self):
        """
        扫描基础目录下所有子文件夹中的照片
        返回按日期分组的照片统计
        """
        if not os.path.exists(self.base_directory):
            print(f"错误：目录 {self.base_directory} 不存在")
            return False
        
        print(f"正在扫描目录：{self.base_directory}")
        folder_count = 0
        total_photos = 0
        
        # 遍历所有子文件夹
        for item in os.listdir(self.base_directory):
            item_path = os.path.join(self.base_directory, item)
            
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
                                
                                self.photo_stats[date_key] += 1
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
        print(f"  📅 拍照天数：{len(self.photo_stats)}")
        
        return len(self.photo_stats) > 0
    
    def validate_date_handling(self):
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
    
    def generate_github_style_commit_markdown(self, start_date, end_date):
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
            elif date_key in self.photo_stats:
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
    
    def generate_statistics_markdown(self, start_date, end_date):
        """
        生成统计信息的Markdown内容
        """
        markdown_content = []
        
        # 总体统计
        total_days = (end_date - start_date).days + 1
        photo_days = len(self.photo_stats)
        total_photos = sum(self.photo_stats.values())
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
    
    def generate_yearly_statistics_markdown(self, start_date, end_date):
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
            
            if date_key in self.photo_stats:
                yearly_stats[year]['total_photos'] += self.photo_stats[date_key]
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
    
    def generate_monthly_chart_markdown(self, start_date, end_date):
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
            if date_key in self.photo_stats:
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
    
    def generate_github_style_commit_png(self, start_date, end_date, output_dir):
        """
        生成GitHub风格的提交图PNG
        """
        # 找到开始日期是星期几 (0=周一, 6=周日)
        start_weekday = start_date.weekday()
        
        # 调整开始日期到周一
        adjusted_start = start_date - timedelta(days=start_weekday)
        
        # 生成周数据矩阵
        weeks_data = []
        current_week = [0] * 7  # 周一到周日
        current_date = adjusted_start
        
        while current_date <= end_date + timedelta(days=6):  # 确保包含最后一周
            weekday = current_date.weekday()  # 0=周一, 6=周日
            date_str = current_date.strftime("%Y-%m-%d")
            
            # 判断这一天的状态
            if current_date < start_date or current_date > end_date:
                current_week[weekday] = -1  # 超出范围
            elif date_str in self.photo_stats:
                current_week[weekday] = min(self.photo_stats[date_str], 4)  # 限制最大值为4
            else:
                current_week[weekday] = 0  # 没有拍照
            
            # 如果是周日或者是最后一天，完成这一周
            if weekday == 6 or current_date == end_date + timedelta(days=6):
                weeks_data.append(current_week[:])
                current_week = [0] * 7
            
            current_date += timedelta(days=1)
        
        # 创建颜色映射
        colors = {
            -1: '#ebedf0',  # 超出范围 - 浅灰色
            0: '#ebedf0',   # 没有拍照 - 浅灰色
            1: '#9be9a8',   # 1张照片 - 浅绿色
            2: '#40c463',   # 2张照片 - 中绿色
            3: '#30a14e',   # 3张照片 - 深绿色
            4: '#216e39'    # 4张及以上 - 最深绿色
        }
        
        # 设置图片大小和参数
        weeks_count = len(weeks_data)
        cell_size = 12
        cell_gap = 2
        
        fig_width = weeks_count * (cell_size + cell_gap) / 80  # 转换为英寸
        fig_height = 7 * (cell_size + cell_gap) / 80 + 2  # 7行 + 标题空间
        
        fig, ax = plt.subplots(figsize=(max(fig_width, 16), fig_height))
        
        # 绘制网格
        for week_idx, week_data in enumerate(weeks_data):
            x_offset = week_idx * (cell_size + cell_gap)
            for day_idx, value in enumerate(week_data):
                y_offset = (6 - day_idx) * (cell_size + cell_gap)  # 从上到下：周一到周日
                
                # 绘制方块
                rect = patches.Rectangle(
                    (x_offset, y_offset), 
                    cell_size, 
                    cell_size,
                    linewidth=1,
                    edgecolor='white',
                    facecolor=colors[value]
                )
                ax.add_patch(rect)
        
        # 添加星期标签
        weekday_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        for i, label in enumerate(weekday_labels):
            ax.text(-30, (6 - i) * (cell_size + cell_gap) + cell_size/2, label, 
                    ha='right', va='center', fontsize=10, fontfamily=CHINESE_FONT)
        
        # 添加月份标签
        current_month = None
        
        for week_idx, week_data in enumerate(weeks_data):
            # 计算这一周的第一天日期
            week_start = adjusted_start + timedelta(weeks=week_idx)
            if week_start.month != current_month and week_start >= start_date:
                current_month = week_start.month
                month_label = f"{week_start.year}年{week_start.month:02d}月"
                x_pos = week_idx * (cell_size + cell_gap)
                ax.text(x_pos, 7 * (cell_size + cell_gap) + 5, month_label, 
                        ha='left', va='bottom', fontsize=9, fontfamily=CHINESE_FONT, rotation=45)
        
        # 设置坐标轴
        ax.set_xlim(-50, weeks_count * (cell_size + cell_gap))
        ax.set_ylim(-10, 7 * (cell_size + cell_gap) + 30)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # 添加标题和统计信息
        total_days = (end_date - start_date).days + 1
        photo_days = len([d for d in self.photo_stats.keys() 
                         if start_date <= datetime.strptime(d, "%Y-%m-%d") <= end_date])
        no_photo_days = total_days - photo_days
        total_photos = sum([v for k, v in self.photo_stats.items() 
                           if start_date <= datetime.strptime(k, "%Y-%m-%d") <= end_date])
        photo_rate = (photo_days / total_days) * 100 if total_days > 0 else 0
        avg_photos = total_photos / photo_days if photo_days > 0 else 0
        
        title = f"NPU每日记录\n"
        title += f"统计期间: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n"
        title += f"总天数: {total_days} | 拍照天数: {photo_days} | 未拍天数: {no_photo_days} | "
        title += f"总照片: {total_photos}张 | 拍照率: {photo_rate:.1f}%"
        
        plt.suptitle(title, fontsize=14, fontfamily=CHINESE_FONT, y=0.95)
        
        # 添加图例
        legend_elements = [
            patches.Rectangle((0, 0), 1, 1, facecolor=colors[0], label='No Photos'),
            patches.Rectangle((0, 0), 1, 1, facecolor=colors[1], label='1 Photo'),
            patches.Rectangle((0, 0), 1, 1, facecolor=colors[2], label='2 Photos'),
            patches.Rectangle((0, 0), 1, 1, facecolor=colors[3], label='3 Photos'),
            patches.Rectangle((0, 0), 1, 1, facecolor=colors[4], label='4+ Photos')
        ]
        
        # 创建图例，使用英文避免字体问题
        legend = ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1), 
                           fontsize=10, frameon=True, fancybox=True, shadow=True)
        
        plt.tight_layout()
        
        # 保存PNG文件
        output_path = os.path.join(output_dir, "NPU_Photo_Commit_Chart.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()  # 关闭图形以释放内存
        
        return output_path
    
    def generate_complete_reports(self, start_date_str="2023-09-01", end_date_str="2026-04-30", output_dir=None):
        """
        生成完整的统计报告（Markdown + PNG）
        
        Args:
            start_date_str (str): 开始日期，格式 'YYYY-MM-DD'
            end_date_str (str): 结束日期，格式 'YYYY-MM-DD'
            output_dir (str): 输出目录，默认为脚本所在目录
            
        Returns:
            dict: 包含生成文件路径的字典
        """
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 验证日期格式
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        except ValueError as e:
            print(f"❌ 日期格式错误：{e}")
            return None
        
        if start_date > end_date:
            print("❌ 开始日期不能晚于结束日期")
            return None
        
        print("=" * 80)
        print("📸 NPU-Everyday 完整统计报告生成器")
        print(f"📅 统计期间：{start_date_str} - {end_date_str}")
        print("=" * 80)
        
        # 扫描照片
        if not self.scan_all_photos():
            print("❌ 没有找到任何照片文件")
            return None
        
        # 验证日期处理
        self.validate_date_handling()
        
        # 生成Markdown报告
        print("\n📝 生成Markdown报告...")
        
        markdown_content = []
        markdown_content.extend(self.generate_github_style_commit_markdown(start_date, end_date))
        markdown_content.extend(self.generate_statistics_markdown(start_date, end_date))
        markdown_content.extend(self.generate_yearly_statistics_markdown(start_date, end_date))
        markdown_content.extend(self.generate_monthly_chart_markdown(start_date, end_date))
        
        # 保存Markdown文件
        markdown_filename = "NPU_Photo_Statistics_Report.md"
        markdown_path = os.path.join(output_dir, markdown_filename)
        
        try:
            markdown_text = '\n'.join(markdown_content)
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            print(f"✅ Markdown报告已生成：{markdown_path}")
        except Exception as e:
            print(f"❌ 生成Markdown文件时出错：{e}")
            return None
        
        # 生成PNG图表
        print("\n🎨 生成PNG图表...")
        
        try:
            png_path = self.generate_github_style_commit_png(start_date, end_date, output_dir)
            print(f"✅ PNG图表已生成：{png_path}")
        except Exception as e:
            print(f"❌ 生成PNG图表时出错：{e}")
            png_path = None
        
        # 显示统计摘要
        total_days = (end_date - start_date).days + 1
        photo_days = len([d for d in self.photo_stats.keys() 
                         if start_date <= datetime.strptime(d, "%Y-%m-%d") <= end_date])
        total_photos = sum([v for k, v in self.photo_stats.items() 
                           if start_date <= datetime.strptime(k, "%Y-%m-%d") <= end_date])
        photo_rate = (photo_days / total_days) * 100 if total_days > 0 else 0
        
        print(f"\n📊 统计摘要：")
        print(f"📅 统计了 {total_days} 天的数据")
        print(f"✅ 其中 {photo_days} 天有拍照 ({photo_rate:.1f}%)")
        print(f"📸 总共 {total_photos} 张照片")
        
        return {
            'markdown_path': markdown_path,
            'png_path': png_path,
            'stats': {
                'total_days': total_days,
                'photo_days': photo_days,
                'total_photos': total_photos,
                'photo_rate': photo_rate
            }
        }


def generate_npu_statistics_reports(base_directory, start_date="2023-09-01", end_date="2026-04-30", output_dir=None):
    """
    生成NPU照片统计报告的便捷函数
    
    Args:
        base_directory (str): NPU-Everyday目录路径
        start_date (str): 开始日期，格式 'YYYY-MM-DD'
        end_date (str): 结束日期，格式 'YYYY-MM-DD'
        output_dir (str): 输出目录，默认为当前目录
        
    Returns:
        dict: 包含生成文件路径和统计信息的字典
    """
    analyzer = NPUPhotoAnalyzer(base_directory)
    return analyzer.generate_complete_reports(start_date, end_date, output_dir)


def main():
    """主函数 - 示例用法"""
    base_directory = r"../NPU-Everyday"  # 请根据实际情况修改路径
    
    print("🚀 启动NPU照片统计分析...")
    
    # 生成完整报告
    results = generate_npu_statistics_reports(
        base_directory=base_directory,
        start_date="2023-09-01",
        end_date="2026-04-30"
    )
    
    if results:
        print(f"\n🎉 报告生成完成！")
        print(f"📄 Markdown报告：{results['markdown_path']}")
        if results['png_path']:
            print(f"🖼️ PNG图表：{results['png_path']}")
        print(f"📊 统计信息：{results['stats']}")
    else:
        print("❌ 报告生成失败")


if __name__ == "__main__":
    main()