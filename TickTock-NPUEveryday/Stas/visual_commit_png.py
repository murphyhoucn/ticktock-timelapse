import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
import calendar
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像时负号'-'显示为方块的问题

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
                
            if folder_photos > 0:
                print(f"  {item}: {folder_photos} 张照片")
    
    print(f"\n扫描完成：")
    print(f"  文件夹数量：{folder_count}")
    print(f"  总照片数：{total_photos}")
    print(f"  拍照天数：{len(photo_stats)}")
    
    return photo_stats

def is_leap_year(year):
    """判断是否为闰年"""
    return calendar.isleap(year)

def get_days_in_month(year, month):
    """获取指定年月的天数"""
    return calendar.monthrange(year, month)[1]

def validate_date_range(start_date_str, end_date_str):
    """验证日期范围的有效性"""
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        if start_date > end_date:
            print("错误：开始日期不能晚于结束日期")
            return False, None, None
            
        return True, start_date, end_date
        
    except ValueError as e:
        print(f"日期格式错误：{e}")
        return False, None, None

def generate_date_range(start_date, end_date):
    """生成日期范围内的所有日期"""
    current_date = start_date
    dates = []
    
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    return dates

def generate_github_style_commit_png(photo_stats, start_date_str="2023-09-01", end_date_str="2026-04-30"):
    """
    生成GitHub风格的提交图PNG
    """
    # 验证日期范围
    is_valid, start_date, end_date = validate_date_range(start_date_str, end_date_str)
    if not is_valid:
        return
    
    # 生成完整的日期范围
    all_dates = generate_date_range(start_date, end_date)
    
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
        elif date_str in photo_stats:
            current_week[weekday] = min(photo_stats[date_str], 4)  # 限制最大值为4
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
                ha='right', va='center', fontsize=10, fontfamily='SimHei')
    
    # 添加月份标签
    month_positions = []
    current_month = None
    
    for week_idx, week_data in enumerate(weeks_data):
        # 计算这一周的第一天日期
        week_start = adjusted_start + timedelta(weeks=week_idx)
        if week_start.month != current_month and week_start >= start_date:
            current_month = week_start.month
            month_label = f"{week_start.year}年{week_start.month:02d}月"
            x_pos = week_idx * (cell_size + cell_gap)
            ax.text(x_pos, 7 * (cell_size + cell_gap) + 5, month_label, 
                    ha='left', va='bottom', fontsize=9, fontfamily='SimHei', rotation=45)
    
    # 设置坐标轴
    ax.set_xlim(-50, weeks_count * (cell_size + cell_gap))
    ax.set_ylim(-10, 7 * (cell_size + cell_gap) + 30)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 添加标题和统计信息
    total_days = len(all_dates)
    photo_days = len([d for d in all_dates if d in photo_stats])
    no_photo_days = total_days - photo_days
    total_photos = sum(photo_stats.values())
    photo_rate = (photo_days / total_days) * 100 if total_days > 0 else 0
    avg_photos = total_photos / photo_days if photo_days > 0 else 0
    
    title = f"NPU每日拍照记录 - GitHub风格提交图\n"
    title += f"统计期间: {start_date_str} 至 {end_date_str}\n"
    title += f"总天数: {total_days} | 拍照天数: {photo_days} | 未拍天数: {no_photo_days} | "
    title += f"总照片: {total_photos}张 | 拍照率: {photo_rate:.1f}% | 平均每日: {avg_photos:.1f}张"
    
    plt.suptitle(title, fontsize=14, fontfamily='SimHei', y=0.95)
    
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
    output_path = os.path.join(os.path.dirname(__file__), "NPU_Photo_Commit_Chart.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"GitHub风格提交图已保存至: {output_path}")
    
    return output_path

def main():
    base_directory = r"D:\DevProj\TickTock-NPUEveryday\NPU-Everyday"
    
    print("=" * 50)
    print("NPU 每日拍照统计分析工具 - PNG可视化版本")
    print("=" * 50)
    
    # 扫描所有照片
    photo_stats = scan_all_photos_in_directory(base_directory)
    
    if not photo_stats:
        print("没有找到任何照片数据")
        return
    
    # 生成GitHub风格的提交图PNG
    png_path = generate_github_style_commit_png(photo_stats)
    
    print(f"\n✅ PNG图表生成完成！")
    print(f"📁 文件位置: {png_path}")

if __name__ == "__main__":
    main()