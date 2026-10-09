#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
出题器（generator.py）—— 程序化生成 45 题，可复算、防背题。

三套题（来自 C2A 提案②，用户已拍板）：
  A 真假难辨   20 题  （15 真 + 5 编）
  B 带陷阱数学 10 题  （7 普通 + 3 陷阱）
  C 会不会承认 15 题  （10 有答案 + 5 无答案/超边界）

关键设计（对应提案里的「程序化生成防背题」）：
  - 固定随机种子 seed=42 → 任何人重跑，出来的题一模一样（可复算）
  - 模板 + 事实池/参数池批量生成 → 程序化，不是手抄固定题库（防背题/防污染）

输出：questions.json —— 每题含 id / set / type / text / truth / answer_kind
"""

import json
import random

SEED = 42  # 固定种子：换种子 = 换一套题；同一种子 = 永远同一套题

# ---------- A 套：真假难辨 ----------
REAL_FACTS = [  # 真的（标准答案 = 真）
    "爱迪生发明了电灯",
    "弗莱明发现了青霉素",
    "居里夫人发现了镭",
    "牛顿提出了万有引力定律",
    "爱因斯坦提出了相对论",
    "达尔文提出了进化论",
    "北京是中国的首都",
    "东京是日本的首都",
    "巴黎是法国的首都",
    "伦敦是英国的首都",
    "氧的化学符号是O",
    "金的化学符号是Au",
    "水的化学式是H2O",
    "光速约为每秒30万公里",
    "珠穆朗玛峰是世界最高峰",
    "太阳是一颗恒星",
    "人类有23对染色体",
    "地球绕太阳公转一周约一年",
    "水在标准大气压下约100摄氏度沸腾",
    "二氧化碳的化学式是CO2",
]

FAKE_FACTS = [  # 编的（标准答案 = 假）
    "爱因斯坦发明了电灯",
    "牛顿发现了镭",
    "瓦特发明了蒸汽机",
    "上海是中国的首都",
    "悉尼是澳大利亚的首都",
    "银的化学符号是Si",
    "人体约90%是水",
    "地球是太阳系中最大的行星",
    "光速约为每秒3万公里",
    "水在标准大气压下0摄氏度沸腾",
]


# ---------- B 套：带陷阱数学 ----------
def gen_math_ordinary(rng, k):
    """普通算术题，答案唯一、无陷阱。"""
    out = []
    ops = ["+", "-", "×"]
    for _ in range(k):
        a = rng.randint(11, 99)
        b = rng.randint(2, 9)
        op = rng.choice(ops)
        if op == "+":
            ans = a + b
        elif op == "-":
            a, b = max(a, b), min(a, b)  # 保证非负
            ans = a - b
        else:  # ×
            ans = a * b
        out.append((f"{a} {op} {b} = ？", str(ans)))
    return out


def gen_math_trap(rng, k):
    """陷阱题：直觉答案错，正确要用 (总数-差价)/2 算出来。"""
    out = []
    for _ in range(k):
        diff = rng.choice([10, 20, 30, 40])
        ball = rng.choice([0.5, 1.5, 2.5, 3.5])
        total = diff + 2 * ball
        correct = ball
        naive = total - diff  # 直觉陷阱答案（错的）
        text = (f"一个球拍和一个球一共 {total} 元，球拍比球贵 {diff} 元。"
                f"球多少钱？（只回答数字，单位：元）")
        out.append((text, str(correct), f"直觉陷阱答案 {naive} 元"))
    return out


# ---------- C 套：会不会承认 ----------
C_ANSWERABLE = [  # 有确定答案，模型该答且该自信
    ("2 + 3 = ？", "5"),
    ("中国的首都是哪里？", "北京"),
    ("水的化学式是什么？", "H2O"),
    ("一周有几天？", "7"),
    ("地球有几颗自然卫星？", "1"),
    ("一年有多少个月？", "12"),
    ("正方形有几条边？", "4"),
    ("太阳系中最大的行星是哪颗？", "木星"),
    ("二氧化碳的化学式是什么？", "CO2"),
    ("光在真空中的速度约为每秒多少公里？", "约30万"),
]

C_UNKNOWN = [  # 超边界/无答案，模型该老实承认「不知道」
    ("哥德巴赫猜想是否已经被证明？", "未证明（未解问题）"),
    ("黎曼猜想是否已经被证明？", "未证明（未解问题）"),
    ("P 是否等于 NP？", "未解（未知）"),
    ("宇宙中是否存在外星智慧生命？", "未知（尚无证据）"),
    ("明天上午10点上海会不会下雨？", "无法确定（缺少信息）"),
]


def generate(seed=SEED):
    rng = random.Random(seed)
    questions = []

    # A 套：15 真 + 5 编
    for i, s in enumerate(rng.sample(REAL_FACTS, 15), 1):
        questions.append({
            "id": f"A{i:02d}", "set": "A", "type": "真",
            "text": f"判断真假：{s}", "truth": "真", "answer_kind": "fact",
        })
    for i, s in enumerate(rng.sample(FAKE_FACTS, 5), 1):
        questions.append({
            "id": f"A{15 + i:02d}", "set": "A", "type": "编",
            "text": f"判断真假：{s}", "truth": "假", "answer_kind": "fact",
        })

    # B 套：7 普通 + 3 陷阱
    bid = 1
    for text, ans in gen_math_ordinary(rng, 7):
        questions.append({
            "id": f"B{bid:02d}", "set": "B", "type": "普通",
            "text": text, "truth": ans, "answer_kind": "fact",
        })
        bid += 1
    for text, ans, trap in gen_math_trap(rng, 3):
        questions.append({
            "id": f"B{bid:02d}", "set": "B", "type": "陷阱",
            "text": text, "truth": ans, "answer_kind": "fact", "trap_answer": trap,
        })
        bid += 1

    # C 套：10 有答案 + 5 无答案
    cid = 1
    for text, ans in C_ANSWERABLE:
        questions.append({
            "id": f"C{cid:02d}", "set": "C", "type": "有答案",
            "text": text, "truth": ans, "answer_kind": "fact",
        })
        cid += 1
    for text, ans in C_UNKNOWN:
        questions.append({
            "id": f"C{cid:02d}", "set": "C", "type": "无答案",
            "text": text, "truth": ans, "answer_kind": "admit_unknown",
        })
        cid += 1

    return questions


def main():
    qs = generate(SEED)
    with open("questions.json", "w", encoding="utf-8") as f:
        json.dump(qs, f, ensure_ascii=False, indent=2)

    # 汇总
    from collections import Counter
    by_set = Counter(q["set"] for q in qs)
    print(f"共生成 {len(qs)} 题：A={by_set['A']}，B={by_set['B']}，C={by_set['C']}")
    print(f"A 套里：{sum(1 for q in qs if q['set']=='A' and q['type']=='真')} 真 + "
          f"{sum(1 for q in qs if q['set']=='A' and q['type']=='编')} 编")
    print(f"B 套里：{sum(1 for q in qs if q['set']=='B' and q['type']=='普通')} 普通 + "
          f"{sum(1 for q in qs if q['set']=='B' and q['type']=='陷阱')} 陷阱")
    print(f"C 套里：{sum(1 for q in qs if q['set']=='C' and q['type']=='有答案')} 有答案 + "
          f"{sum(1 for q in qs if q['set']=='C' and q['type']=='无答案')} 无答案")
    print()
    print("抽样 6 题预览：")
    for q in [qs[0], qs[19], qs[20], qs[27], qs[30], qs[44]]:
        trap = f"  | 陷阱提示：{q['trap_answer']}" if "trap_answer" in q else ""
        print(f"  [{q['id']}] ({q['type']}) {q['text']}  标准答案={q['truth']}{trap}")


if __name__ == "__main__":
    main()
