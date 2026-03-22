import os
from PIL import Image

def resize_and_pad_to_3_4(input_dir, output_dir, target_w=1418, target_h=1890):
    """
    将所有图片统一转换为 1418x1890 (3:4)，确保不被抖音裁切。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    target_ratio = target_w / target_h

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
            try:
                img_path = os.path.join(input_dir, filename)
                with Image.open(img_path) as img:
                    img = img.convert("RGB")
                    orig_w, orig_h = img.size
                    orig_ratio = orig_w / orig_h

                    # 逻辑：将原图缩放到能放进 target_w x target_h 的最大尺寸
                    if orig_ratio > target_ratio:
                        # 原图较宽（横屏），按宽度缩放
                        new_w = target_w
                        new_h = int(new_w / orig_ratio)
                    else:
                        # 原图较瘦（9:16），按高度缩放
                        new_h = target_h
                        new_w = int(new_h * orig_ratio)

                    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    # 创建 3:4 的黑色底板
                    canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))

                    # 居中粘贴
                    paste_x = (target_w - new_w) // 2
                    paste_y = (target_h - new_h) // 2
                    canvas.paste(img_resized, (paste_x, paste_y))

                    # 统一保存
                    save_path = os.path.join(output_dir, f"fixed_{filename}")
                    canvas.save(save_path, "JPEG", quality=95)
                    print(f"处理完成: {filename} -> 1418x1890 (3:4)")

            except Exception as e:
                print(f"跳过文件 {filename}: {e}")

# 设置路径

input_folder = r"C:\Users\cosmi\Nutstore\1\AInBox\MYYEAR2025"
pyfolder = os.path.dirname(os.path.abspath(__file__))
output_folder = os.path.join(pyfolder, "Resized_3_4_Output")

resize_and_pad_to_3_4(input_folder, output_folder)