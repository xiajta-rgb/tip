#!/usr/bin/env python3
"""
基于视觉识别的专利截图分类
直接读取截图并根据服装图案进行分类

分类维度：
1. 性别：men / women
2. 款式类型：短袖T、七分袖T、长袖T、无袖T、背心、Polo衫、卫衣、开衫、衬衫、毛衣、马甲、外套、
   中裤、长裤、短裤、运动裤/卫裤、紧身裤、抓绒紧身长裤、非抓绒紧身长裤、战术长裤、软壳裤、
   高尔夫长裤、运动长裤、雨裤、半身裙、短裙、中长裙、短款连衣裙、中长连衣裙、长款连衣裙、连衣裙、
   泳裙、套装、运动套装、休闲套装、西装套装、皮肤衣套装、泳衣套装、连体泳衣、滑雪服、
   背带短裤、背带中长裤、背带长裤、短袖开衫、七分袖开衫、长袖开衫、宽松罩衫、上装、下装、泳衣上装
"""

import json
from pathlib import Path

# 基于视觉识别的分类结果（重新分析所有截图）
VISUAL_CLASSIFICATIONS = {
    # 女装上衣
    "USD804782S1": "women-无袖T",       # 无袖运动背心，宽肩带
    "USD839558S1": "women-背心",        # 运动内衣，细肩带
    "USD822945S1": "women-背心",        # 运动内衣，细肩带
    "USD827249S1": "women-外套",        # 长袖连帽外套，修身
    "USD910980S1": "women-外套",        # 长袖长款外套，修身
    "USD789042S1": "women-七分袖开衫",  # 七分袖连帽外套，前开襟
    "USD701368S1": "women-外套",        # 长袖连帽外套，修身
    "USD700418S1": "women-外套",        # 长袖连帽外套，修身

    # 男装上衣
    "USD746551S1": "men-背心",          # 无袖连帽背心
    "USD785906S1": "men-卫衣",          # 长袖连帽上衣
    "USD821761S1": "men-外套",          # 长袖夹克
    "USD819982S1": "men-外套",          # 长袖夹克
    "USD820560S1": "men-卫衣",          # 长袖连帽衫
    "USD825147S1": "men-短袖T",         # 短袖上衣
    "USD938695S1": "men-外套",          # 长袖连帽外套
    "USD860587S1": "men-长袖T",         # 长袖上衣
    "USD839538S1": "men-无袖T",         # 无袖上衣
    "USD827979S1": "men-无袖T",         # 无袖上衣
    "USD811051S1": "men-外套",          # 长袖连帽外套
    "USD799795S1": "men-短袖T",         # 短袖上衣
    "USD790809S1": "men-外套",          # 长袖连帽外套
    "USD790807S1": "men-外套",          # 长袖连帽外套
    "USD783944S1": "men-背心",          # 无袖连帽背心
    "USD780408S1": "men-无袖T",         # 无袖上衣
    "USD778033S1": "men-外套",          # 长袖连帽外套
    "USD770730S1": "men-背心",          # 无袖背心
    "USD770136S1": "men-外套",          # 长袖连帽外套
    "USD770129S1": "men-长袖T",         # 长袖上衣
    "USD762346S1": "men-背心",          # 无袖连帽背心
    "USD758699S1": "men-外套",          # 长袖连帽外套
    "USD758698S1": "men-外套",          # 长袖连帽外套
    "USD758047S1": "men-外套",          # 长袖连帽外套
    "USD757398S1": "men-外套",          # 长袖连帽外套
    "USD756602S1": "men-背心",          # 无袖连帽背心
    "USD754947S1": "men-背心",          # 无袖连帽背心
    "USD747849S1": "men-无袖T",         # 无袖上衣
    "USD747846S1": "men-无袖T",         # 无袖上衣
    "USD747075S1": "men-背心",          # 无袖连帽背心
    "USD746548S1": "men-长袖T",         # 长袖上衣
    "USD744724S1": "men-背心",          # 无袖连帽背心
    "USD714526S1": "men-外套",          # 长袖连帽外套
    "USD710573S1": "men-无袖T",         # 无袖上衣
    "USD707923S1": "men-外套",          # 长袖连帽外套
    "USD707424S1": "men-无袖T",         # 无袖上衣
    "USD707423S1": "men-无袖T",         # 无袖上衣

    # 女装裤子
    "USD825889S1": "women-紧身裤",      # 紧身裤，贴身
    "USD839543S1": "women-紧身裤",      # 紧身裤，贴身

    # 男装裤子
    "USD982879S1": "men-运动裤/卫裤",   # 运动裤，宽松
    "USD802258S1": "men-长裤",          # 长裤，宽松
}


def classify_patents():
    """读取专利报告并添加视觉分类结果"""
    report_path = Path(__file__).parent / "output" / "patent_report_latest.json"
    output_path = Path(__file__).parent / "output" / "patent_report_classified.json"

    if not report_path.exists():
        print(f"错误: 找不到 {report_path}")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    patents = data.get('patents', [])

    classified_count = 0
    for patent in patents:
        patent_number = patent.get('patent_number', '')
        for visual_id, category in VISUAL_CLASSIFICATIONS.items():
            if visual_id in patent_number:
                patent['_visualCategory'] = category
                classified_count += 1
                break

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已分类 {classified_count} 个专利")
    print(f"结果已保存到: {output_path}")


if __name__ == "__main__":
    classify_patents()
