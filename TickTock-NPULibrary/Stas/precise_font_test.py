import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import warnings
import os
from datetime import datetime

# 抑制警告
warnings.filterwarnings('ignore', message='.*missing from font.*')
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

def test_specific_font(font_name):
    """测试特定字体是否能正确显示中文"""
    try:
        # 设置字体
        plt.rcParams['font.sans-serif'] = [font_name]
        
        # 创建测试图
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # 测试文本
        test_text = f"字体测试: {font_name}\n中文显示：你好世界！\n数字符号：2025年9月30日"
        
        ax.text(0.5, 0.5, test_text, fontsize=14, ha='center', va='center',
                bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.3))
        
        ax.set_title(f'字体测试: {font_name}', fontsize=16, weight='bold')
        ax.axis('off')
        
        # 保存测试图
        filename = f"test_font_{font_name.replace(' ', '_').replace('/', '_')}.jpg"
        plt.savefig(filename, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        
        file_size = os.path.getsize(filename) / 1024
        print(f"✅ {font_name} - 测试成功，图片已保存: {filename} ({file_size:.1f} KB)")
        return True, filename
        
    except Exception as e:
        print(f"❌ {font_name} - 测试失败: {e}")
        return False, None

def update_matplotlib_font_cache():
    """更新matplotlib字体缓存"""
    try:
        print("🔄 更新matplotlib字体缓存...")
        fm._rebuild()
        print("✅ 字体缓存更新完成")
    except:
        print("❌ 字体缓存更新失败")

def main():
    print("🎯 精确字体测试工具")
    print("=" * 50)
    
    # 更新字体缓存
    update_matplotlib_font_cache()
    
    # 要测试的字体列表
    fonts_to_test = [
        'Noto Sans CJK SC',
        'Noto Serif CJK SC', 
        'Noto Sans Mono CJK SC',
        'AR PL UKai CN',
        'AR PL UMing CN',
        'Droid Sans Fallback'
    ]
    
    successful_fonts = []
    
    print(f"\n🧪 测试字体显示效果...")
    
    for font_name in fonts_to_test:
        success, filename = test_specific_font(font_name)
        if success:
            successful_fonts.append(font_name)
    
    print(f"\n📊 测试结果:")
    print(f"✅ 成功的字体数量: {len(successful_fonts)}")
    
    if successful_fonts:
        print(f"\n🏆 推荐字体优先级 (Linux):")
        print("font_priority = [")
        for font in successful_fonts:
            print(f"    '{font}',")
        print("    'sans-serif'")
        print("]")
        
        # 推荐最佳字体
        best_font = successful_fonts[0]
        print(f"\n💡 推荐使用: {best_font}")
        
        return successful_fonts
    else:
        print("❌ 没有找到可用的中文字体")
        return []

if __name__ == "__main__":
    successful_fonts = main()
    
    if successful_fonts:
        print(f"\n🎨 请查看生成的测试图片来选择最佳字体效果")