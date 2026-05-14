---
name: "patent-garment-classifier"
description: "Classify patent screenshots into detailed garment categories using built-in visual recognition. Invoke when user needs accurate garment classification from patent screenshots without external APIs."
---

# Patent Garment Classifier

This skill analyzes patent screenshots and classifies them into detailed garment categories based on visual features of the clothing depicted in the drawings.

## Classification Dimensions

### Dimension 1: Gender (性别)
| Category | Visual Indicators |
|----------|-------------------|
| men | 宽肩，直筒轮廓，整体比例较大 |
| women | 窄腰，贴身剪裁，整体比例较小 |

### Dimension 2: Garment Type (款式类型)

#### 上衣类 (Tops)
| Category | Visual Indicators |
|----------|-------------------|
| 短袖T | 短袖，圆领或V领，宽松或修身 |
| 七分袖T | 袖长到肘部下方，T恤款式 |
| 长袖T | 长袖，T恤款式 |
| 无袖T | 无袖，T恤款式，肩带较宽 |
| 背心 | 无袖，肩带较细，贴身 |
| Polo衫 | 有领子，前襟有纽扣 |
| 卫衣 | 连帽或圆领，宽松，通常有口袋 |
| 开衫 | 前开襟，有拉链或纽扣 |
| 衬衫 | 有领子，前襟纽扣，正式或休闲 |
| 毛衣 | 针织纹理，圆领或V领 |
| 马甲 | 无袖，前开襟，通常有拉链 |
| 外套 | 长袖，前开襟，较厚材质 |

#### 下装类 (Bottoms)
| Category | Visual Indicators |
|----------|-------------------|
| 中裤 | 裤长到膝盖附近 |
| 长裤 | 裤长到脚踝 |
| 短裤 | 裤长到大腿中部 |
| 运动裤/卫裤 | 宽松，弹性腰头，可能有侧条纹 |
| 紧身裤 | 贴身，高腰，弹性面料 |
| 抓绒紧身长裤 | 紧身，有抓绒纹理 |
| 非抓绒紧身长裤 | 紧身，光滑面料 |
| 战术长裤 | 多口袋，宽松直筒 |
| 软壳裤 | 修身，有弹性，户外风格 |
| 高尔夫长裤 | 修身，正式休闲风格 |
| 运动长裤 | 宽松或修身，运动风格 |
| 雨裤 | 防水材质感，宽松 |

#### 裙装类 (Skirts/Dresses)
| Category | Visual Indicators |
|----------|-------------------|
| 半身裙 | 只覆盖下半身，A字或直筒 |
| 短裙 | 裙长到大腿中部 |
| 中长裙 | 裙长到膝盖附近 |
| 短款连衣裙 | 连体，裙长到大腿 |
| 中长连衣裙 | 连体，裙长到膝盖 |
| 长款连衣裙 | 连体，裙长到小腿或脚踝 |
| 连衣裙 | 连体裙装 |
| 泳裙 | 泳衣款式，裙摆设计 |

#### 套装类 (Sets)
| Category | Visual Indicators |
|----------|-------------------|
| 套装 | 上下装配套展示 |
| 运动套装 | 运动风格上下装 |
| 休闲套装 | 休闲风格上下装 |
| 西装套装 | 正式西装上下装 |
| 皮肤衣套装 | 轻薄材质上下装 |
| 泳衣套装 | 泳衣上下装 |
| 连体泳衣 | 一体式泳衣 |

#### 特殊类 (Special)
| Category | Visual Indicators |
|----------|-------------------|
| 滑雪服 | 厚重，防水，通常连帽 |
| 背带短裤 | 有背带，短裤款式 |
| 背带中长裤 | 有背带，中裤款式 |
| 背带长裤 | 有背带，长裤款式 |
| 短袖开衫 | 短袖，前开襟 |
| 七分袖开衫 | 七分袖，前开襟 |
| 长袖开衫 | 长袖，前开襟 |
| 宽松罩衫 | 宽松，套头款式 |
| 上装 | 通用上衣，无法细分 |
| 下装 | 通用下装，无法细分 |
| 泳衣上装 | 泳衣上半部分 |

## Visual Recognition Rules

### Step 1: Identify Gender
- **Men**: 肩宽较宽，直筒或方形轮廓，整体比例较大
- **Women**: 腰部较窄，更贴身，整体比例较小，曲线轮廓

### Step 2: Identify Garment Type
1. **判断覆盖区域**：
   - 只覆盖上半身 → 上衣类
   - 只覆盖下半身 → 下装类
   - 覆盖全身 → 连衣裙/连体衣/套装

2. **判断袖子长度**：
   - 无袖 → 背心/无袖T/马甲
   - 短袖 → 短袖T/短袖开衫
   - 七分袖 → 七分袖T/七分袖开衫
   - 长袖 → 长袖T/长袖开衫/卫衣/外套

3. **判断款式特征**：
   - 有领子+纽扣 → Polo衫/衬衫
   - 连帽 → 卫衣
   - 前开襟 → 开衫/外套/马甲
   - 针织纹理 → 毛衣
   - 弹性腰头+宽松 → 运动裤
   - 贴身 → 紧身裤

### Step 3: Apply Classification
1. Read the patent screenshot image
2. Focus on the garment drawing at the bottom of the page
3. Determine gender based on silhouette and proportions
4. Determine garment type based on coverage, sleeve length, and style features
5. Assign category combining gender and garment type

## Usage

When invoked:
1. Read all patent screenshots in the screenshots directory
2. For each screenshot, analyze the garment drawing
3. Apply the visual recognition rules above
4. Output classification results as JSON mapping patent numbers to categories
