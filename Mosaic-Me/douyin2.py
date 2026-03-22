import os
from PIL import Image

def pad_vertical_for_max_width(input_dir, output_dir, target_ratio=21/9):
    """
    通过在上下填充黑色像素，将图片比例拉长到 9:21。
    确保抖音在填满高度时，不会裁切左右宽度。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            try:
                img_path = os.path.join(input_dir, filename)
                with Image.open(img_path) as img:
                    # 保留原图模式（RGB/RGBA等），不强制转换
                    orig_mode = img.mode
                    orig_w, orig_h = img.size
                    
                    # 计算为了达到 target_ratio，目标高度应该是多少
                    # 比例 = 高 / 宽，所以 高 = 宽 * target_ratio
                    target_h = int(orig_w * target_ratio)
                    
                    if target_h < orig_h:
                        # 如果原图已经比目标比例还长，则不做处理（防止缩短图片）
                        target_h = orig_h
                        target_w = orig_w
                    else:
                        target_w = orig_w

                    # 创建超长黑色画布（使用原图相同的模式）
                    if orig_mode == 'RGBA' or orig_mode == 'LA':
                        canvas = Image.new(orig_mode, (target_w, target_h), (0, 0, 0, 255))
                    else:
                        # RGB 或其他模式
                        if orig_mode != 'RGB':
                            img = img.convert('RGB')
                            orig_mode = 'RGB'
                        canvas = Image.new(orig_mode, (target_w, target_h), (0, 0, 0))

                    # 将原图居中粘贴（上下留黑边）
                    paste_y = (target_h - orig_h) // 2
                    canvas.paste(img, (0, paste_y))

                    # 统一使用PNG格式无损保存
                    base_name = os.path.splitext(filename)[0]
                    save_path = os.path.join(output_dir, f"full_width_{base_name}.png")
                    
                    # 确保转换为RGB或RGBA模式
                    if canvas.mode not in ['RGB', 'RGBA']:
                        canvas = canvas.convert('RGB')
                    
                    canvas.save(save_path, "PNG", optimize=False)
                    print(f"处理完成: {filename} -> {target_w}x{target_h} (PNG无损)")

            except Exception as e:
                print(f"跳过 {filename}: {e}")

# 设置路径
input_folder = r"C:\Users\cosmi\Nutstore\1\AInBox\MYYEAR2025"
pyfolder = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(pyfolder, "Douyin-Size")

# 建议比例设为 2.2 (约 9:20) 或 2.33 (约 9:21)，适配全面屏
pad_vertical_for_max_width(input_folder, output_folder, target_ratio=2.3)