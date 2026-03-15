"""
图片拼接程序
将Me文件夹下的自拍照片拼接成一张大图
"""
import os
from PIL import Image
import time
# 配置参数
IMAGE_FOLDER = "Me"  # 图片文件夹
timestamp = time.strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = f"mosaic_output-{timestamp}.jpg"  # 输出文件名
WHITE_BORDER = 30  # 白边宽度（像素）

# 网格配置：70张图片，10行7列（竖向排列）
ROWS = 10  # 行数
COLS = 7   # 列数

# 输出图像尺寸控制
# 控制单个图片缩放比例：1=原尺寸, 2=1/2, 3=1/3, 4=1/4, 5=1/5...
# 数值越大，输出图像越小，文件大小越小
OUTPUT_SCALE = 8  # 缩放倍数（原图尺寸除以此值）

def get_all_images(folder):
    """获取文件夹中所有jpg图片"""
    images = []
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith('.jpg'):
            images.append(os.path.join(folder, filename))
    return images

def resize_image(img, target_width, target_height):
    """调整图片大小并保持宽高比，裁剪多余部分"""
    # 计算缩放比例
    width_ratio = target_width / img.width
    height_ratio = target_height / img.height
    
    # 使用较大的比例以确保覆盖目标区域
    scale_ratio = max(width_ratio, height_ratio)
    
    # 缩放图片
    new_width = int(img.width * scale_ratio)
    new_height = int(img.height * scale_ratio)
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 居中裁剪
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height
    
    return img_resized.crop((left, top, right, bottom))

def create_mosaic():
    """创建拼接图"""
    # 获取所有图片
    image_paths = get_all_images(IMAGE_FOLDER)
    total_images = len(image_paths)
    
    print(f"找到 {total_images} 张图片")
    print(f"拼接配置: {ROWS}行 × {COLS}列")
    
    if total_images < ROWS * COLS:
        print(f"警告: 图片数量不足 ({total_images} < {ROWS * COLS})")
        return
    
    # 读取第一张图片获取原始尺寸
    first_img = Image.open(image_paths[0])
    original_width, original_height = first_img.size
    first_img.close()
    
    print(f"原始图片尺寸: {original_width} × {original_height}")
    
    # 计算单个图片在拼接图中的尺寸（根据OUTPUT_SCALE缩放）
    cell_width = original_width // OUTPUT_SCALE
    cell_height = original_height // OUTPUT_SCALE
    
    print(f"缩放比例: 1/{OUTPUT_SCALE}")
    print(f"拼接单元尺寸: {cell_width} × {cell_height}")
    
    # 计算最终拼接图尺寸
    # 总宽度 = 左边界 + (单元宽度 + 间隔) * 列数 - 间隔 + 右边界
    total_width = WHITE_BORDER + (cell_width + WHITE_BORDER) * COLS
    total_height = WHITE_BORDER + (cell_height + WHITE_BORDER) * ROWS
    
    print(f"输出图片尺寸: {total_width} × {total_height}")
    print(f"高宽比: {total_height / total_width:.2f}:1")
    
    # 创建白色背景的大图
    mosaic = Image.new('RGB', (total_width, total_height), 'white')
    
    # 逐个处理图片
    print("\n开始拼接...")
    for idx, img_path in enumerate(image_paths[:ROWS * COLS]):
        # 计算当前图片在网格中的位置
        row = idx // COLS
        col = idx % COLS
        
        # 读取并调整图片大小
        img = Image.open(img_path)
        img_resized = resize_image(img, cell_width, cell_height)
        
        # 计算粘贴位置
        x = WHITE_BORDER + col * (cell_width + WHITE_BORDER)
        y = WHITE_BORDER + row * (cell_height + WHITE_BORDER)
        
        # 粘贴到拼接图
        mosaic.paste(img_resized, (x, y))
        
        img.close()
        
        # 显示进度
        if (idx + 1) % 10 == 0 or idx == ROWS * COLS - 1:
            print(f"进度: {idx + 1}/{ROWS * COLS}")
    
    # 保存结果
    print(f"\n正在保存到 {OUTPUT_FILE}...")
    mosaic.save(OUTPUT_FILE, quality=95, optimize=True)
    
    print(f"✓ 拼接完成！")
    print(f"输出文件: {OUTPUT_FILE}")
    print(f"文件大小: {os.path.getsize(OUTPUT_FILE) / (1024 * 1024):.2f} MB")

if __name__ == "__main__":
    create_mosaic()
