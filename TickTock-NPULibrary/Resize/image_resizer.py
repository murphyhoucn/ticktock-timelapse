import os
import sys
from PIL import Image
import argparse
from pathlib import Path

def resize_image(input_path, output_path, target_size=(4096, 3072)):
    """
    将图片放缩到目标尺寸
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径
        target_size: 目标尺寸 (width, height)
    """
    try:
        with Image.open(input_path) as img:
            # 获取原始尺寸
            original_size = img.size
            print(f"原始尺寸: {original_size[0]}x{original_size[1]}")
            
            # 如果已经是目标尺寸，直接复制
            if original_size == target_size:
                img.save(output_path, quality=100, optimize=True)
                print(f"✅ 尺寸已符合要求，直接复制")
                return True
            
            # 使用高质量重采样方法进行放缩
            resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
            
            # 保存放缩后的图片
            resized_img.save(output_path, quality=100, optimize=True)
            print(f"✅ 放缩完成: {original_size[0]}x{original_size[1]} → {target_size[0]}x{target_size[1]}")
            return True
            
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        return False

def process_directory(input_dir, output_dir, target_size=(4096, 3072)):
    """
    批量处理目录中的所有图片
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
        target_size: 目标尺寸 (width, height)
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"❌ 输入目录不存在: {input_dir}")
        return
    
    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    
    # 统计信息
    total_images = 0
    processed_images = 0
    failed_images = 0
    huawei_count = 0  # 3648*2736
    vivo_count = 0   # 4096*3072
    other_count = 0
    
    print(f"📁 输入目录: {input_dir}")
    print(f"📁 输出目录: {output_dir}")
    print(f"🎯 目标尺寸: {target_size[0]}x{target_size[1]}")
    print("=" * 60)
    
    # 收集所有图片文件并按时间顺序排序
    image_files = []
    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            image_files.append(file_path)
    
    # 按时间顺序排序：先按文件夹，再按文件名
    image_files = sorted(image_files, key=lambda x: (str(x.parent), x.name))
    
    print(f"📋 找到 {len(image_files)} 个图片文件（按时间顺序排列）")
    
    # 显示前几个文件以验证顺序
    if len(image_files) > 0:
        print("📂 文件处理顺序预览:")
        for i, file_path in enumerate(image_files[:3]):
            rel_path = file_path.relative_to(input_path)
            print(f"   {i+1}. {rel_path}")
        if len(image_files) > 3:
            print(f"   ... 还有 {len(image_files)-3} 个文件")
    print("=" * 60)
    
    # 遍历排序后的图片文件
    for file_path in image_files:
        total_images += 1
        
        # 构建输出文件路径，保持相对目录结构
        relative_path = file_path.relative_to(input_path)
        output_file = output_path / relative_path
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📸 处理第 {total_images} 个图片:")
        print(f"   文件: {relative_path}")
        
        # 检查原始尺寸并分类
        try:
            with Image.open(file_path) as img:
                size = img.size
                if size == (3648, 2736):
                    huawei_count += 1
                    print(f"   设备: HUAWEI P30 Pro")
                elif size == (4096, 3072):
                    vivo_count += 1
                    print(f"   设备: vivo X100 Pro")
                else:
                    other_count += 1
                    print(f"   设备: 其他 ({size[0]}x{size[1]})")
        except:
            pass
        
        # 处理图片
        if resize_image(str(file_path), str(output_file), target_size):
            processed_images += 1
        else:
            failed_images += 1
    
    # 输出统计结果
    print("\n" + "=" * 60)
    print("📊 处理统计:")
    print(f"   总图片数: {total_images}")
    print(f"   成功处理: {processed_images}")
    print(f"   处理失败: {failed_images}")
    print(f"   HUAWEI P30 Pro (3648×2736): {huawei_count}")
    print(f"   vivo X100 Pro (4096×3072): {vivo_count}")
    print(f"   其他尺寸: {other_count}")
    print("✅ 批量处理完成!")

def main():
    parser = argparse.ArgumentParser(description='NPU照片统一尺寸放缩工具')
    parser.add_argument('input_dir', help='输入目录路径')
    parser.add_argument('output_dir', help='输出目录路径')
    parser.add_argument('--width', type=int, default=4096, help='目标宽度 (默认: 4096)')
    parser.add_argument('--height', type=int, default=3072, help='目标高度 (默认: 3072)')
    parser.add_argument('--single', help='处理单个文件')
    
    args = parser.parse_args()
    
    target_size = (args.width, args.height)
    
    print("🖼️  NPU照片统一尺寸放缩工具")
    print("=" * 60)
    
    if args.single:
        # 单文件处理模式
        print(f"🎯 单文件处理模式")
        if resize_image(args.single, args.output_dir, target_size):
            print("✅ 单文件处理完成!")
        else:
            print("❌ 单文件处理失败!")
    else:
        # 批量处理模式
        print(f"📁 批量处理模式")
        process_directory(args.input_dir, args.output_dir, target_size)

if __name__ == "__main__":
    main()