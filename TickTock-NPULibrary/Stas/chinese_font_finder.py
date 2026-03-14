from matplotlib import pyplot as plt
import matplotlib
import matplotlib.font_manager as fm

# 获取所有字体
all_fonts = sorted([f.name for f in matplotlib.font_manager.fontManager.ttflist])

# 中文相关字体关键词
chinese_keywords = [
    'CJK', 'CN', 'Chinese', 'Han', 'Ming', 'Kai', 'Hei', 
    'AR PL', 'WenQuanYi', 'Noto', 'Source', 'SimHei', 
    'SimSun', 'Microsoft', 'YaHei', 'Fallback', 'Droid'
]

print("🔍 系统中所有字体:")
print("=" * 50)
for i, font in enumerate(all_fonts, 1):
    print(f"{i:3d}. {font}")

print("\n🎯 可能支持中文的字体:")
print("=" * 50)
chinese_fonts = []
for font in all_fonts:
    if any(keyword in font for keyword in chinese_keywords):
        chinese_fonts.append(font)
        print(f"✅ {font}")

# 去重并显示
unique_chinese_fonts = list(set(chinese_fonts))
print(f"\n📊 去重后的中文字体 (共 {len(unique_chinese_fonts)} 个):")
print("=" * 50)
for i, font in enumerate(unique_chinese_fonts, 1):
    print(f"{i}. {font}")

# 测试每个中文字体是否真的支持中文
print(f"\n🧪 测试中文字体渲染效果:")
print("=" * 50)

def test_font_chinese_support(font_name):
    """测试字体是否真的支持中文"""
    try:
        # 设置字体
        plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
        
        # 创建简单的测试
        fig, ax = plt.subplots(figsize=(6, 2))
        ax.text(0.5, 0.5, '中文测试', fontsize=14, ha='center', va='center')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        # 保存测试图片
        test_filename = f"test_{font_name.replace(' ', '_').replace('/', '_')}.jpg"
        plt.savefig(test_filename, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return True, test_filename
    except Exception as e:
        return False, str(e)

# 重点测试几个最有希望的字体
priority_fonts = ['AR PL UKai CN', 'AR PL UMing CN', 'Droid Sans Fallback', 'Noto Sans CJK JP']
available_priority_fonts = [f for f in priority_fonts if f in unique_chinese_fonts]

print("🔥 重点测试的字体:")
for font in available_priority_fonts:
    success, result = test_font_chinese_support(font)
    if success:
        print(f"✅ {font} - 测试成功，图片已保存: {result}")
    else:
        print(f"❌ {font} - 测试失败: {result}")

print(f"\n💡 建议使用的中文字体优先级:")
print("1. AR PL UKai CN (文鼎楷体)")
print("2. AR PL UMing CN (文鼎明体)")
print("3. Droid Sans Fallback (Android字体)")
print("4. Noto Sans CJK JP (Google Noto字体)")