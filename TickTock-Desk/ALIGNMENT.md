# 人脸对齐算法说明

## 🎯 对齐策略

### 算法特点
- **不缩放**：保持人脸原始大小，避免图像质量损失
- **只平移旋转**：通过平移和旋转将人脸关键点对齐到固定位置
- **保持分辨率**：输入输出均为1920*1080

### 对齐过程

1. **检测关键点**：
   - 左眼：`landmarks[33]`
   - 右眼：`landmarks[263]` 
   - 鼻尖：`landmarks[1]`

2. **计算眼睛中心**：
   ```python
   eye_center = (left_eye + right_eye) / 2
   ```

3. **计算旋转角度**：
   ```python
   eye_vector = right_eye - left_eye
   angle = np.degrees(np.arctan2(eye_vector[1], eye_vector[0]))
   ```

4. **定义目标位置**：
   - 眼睛中心固定在：`(960, 432)` - 图像中心水平，40%高度
   - 不进行缩放：`scale = 1.0`

5. **应用变换**：
   ```python
   # 以眼睛中心为旋转点，不缩放
   rotation_matrix = cv2.getRotationMatrix2D(tuple(eye_center), angle, 1.0)
   
   # 平移到目标位置
   tx = target_eye_center[0] - eye_center[0]
   ty = target_eye_center[1] - eye_center[1]
   rotation_matrix[0, 2] += tx
   rotation_matrix[1, 2] += ty
   ```

### 边界处理
- **超出边界**：自动裁切
- **空白区域**：黑色填充
- **保持尺寸**：始终输出1920*1080

### 优势
1. **保持图像质量**：无缩放操作，避免插值导致的质量损失
2. **人脸大小一致**：所有照片中人脸保持原始大小
3. **位置精确对齐**：眼睛中心位置完全一致
4. **适合延时视频**：人脸位置稳定，效果更佳

### 效果对比
- **修改前**：有缩放，可能导致人脸大小不一致
- **修改后**：无缩放，人脸大小保持一致，仅位置和角度对齐