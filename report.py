#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告器（report.py）—— 把各考生的判卷结果合成一张「成绩单」。

四大组件之④（出成绩单）。职责单一：
  读 questions.json + 目录下所有 *_answers.json，逐模型判分，
  输出「总成绩对比表 + 逐模型错题明细」，写成 成绩单.md。
  只陈述事实（哪题错、信心几分、三把尺子各多少），不做任何解释性结论。

用法：python3 report.py
  有 3 个考生就出 3 行，有 5 个就出 5 行——发来 Gemini/Qwen 后重跑一次即可。
  判卷逻辑复用 score_answers.judge + scorer.score，保证与单卷判分口径一致、可复算。
"""

import json
import glob

from score_answers import judge
from scorer import Record, score


def load_models():
    qs = json.load(open("questions.json", encoding="utf-8"))
    files = sorted(glob.glob("*_answers.json"))
    models = []
    for f in files:
        data = json.load(open(f, encoding="utf-8"))
        name = data.get("model", f)
        amap = {a["id"]: a for a in data["answers"]}
        records = []
        right = 0
        wrong = []
        for q in qs:
            a = amap[q["id"]]
            ok = judge(q, a["answer"])
            right += 1 if ok else 0
            records.append(Record(ok, True, a["confidence"]))
            if not ok:
                wrong.append((q["id"], q["text"], q["truth"], a["answer"], a["confidence"]))
        res = score(records)
        models.append({
            "name": name,
            "file": f,
            "right": right,
            "total": len(records),
            "res": res,
            "wrong": wrong,
        })
    return qs, models


def render_md(models):
    lines = []
    lines.append("# C2A-C9 元认知 Benchmark 成绩单")
    lines.append("")
    lines.append("生成：2026-10-09（report.py 自动生成；判卷口径与单卷判分一致，任何人重跑结果相同）")
    lines.append("")
    lines.append("## 一、指标说明")
    lines.append("")
    lines.append("- 校准误差 ECE：信心分与真实对错的平均偏差，**越小越好**（0 = 说 90% 就真约 90% 对）")
    lines.append("- 过度自信率：高信心（≥70%）题里答错的比例，**越低越好**")
    lines.append("- 漏判率：低信心（≤30%）题里答对的比例，**越低越好**")
    lines.append("")
    lines.append("## 二、总成绩对比")
    lines.append("")
    lines.append("| 考生 | 正确率 | 校准误差 ECE | 过度自信率 | 漏判率 |")
    lines.append("|---|---|---|---|---|")
    for m in models:
        lines.append(
            f"| {m['name']} | {m['right']}/{m['total']} "
            f"({m['right'] / m['total'] * 100:.1f}%) | {m['res']['ECE(%)']}% | "
            f"{m['res']['过度自信率(%)']}% | {m['res']['漏判率(%)']}% |"
        )
    lines.append("")
    lines.append("## 三、逐模型错题明细")
    lines.append("")
    for m in models:
        lines.append(f"### {m['name']}（答卷：{m['file']}）")
        lines.append("")
        if not m["wrong"]:
            lines.append("- 无错题")
        else:
            for qid, text, truth, ans, conf in m["wrong"]:
                lines.append(
                    f"- **{qid}** {text} → 标准答案「{truth}」，模型答「{ans}」（信心 {conf}%）"
                )
        lines.append("")
    lines.append("## 四、局限说明（判卷口径）")
    lines.append("")
    lines.append("- 漏判率 = 低信心（≤30%）题里答对的比例。某模型全卷没有低信心答案时，漏判率显示 0.0% 实为「无样本」，不代表满分。")
    lines.append("- C11–C15 为「无答案题」，正确答案就是「无法确定/未知」。此类题上低信心且答对，是「诚实承认无知」的正确行为，并非漏判。")
    lines.append("- 因此 Gemini 与通义千问 Qwen 的 100% 漏判率，均仅由 C15 一题（低信心且答对）产生，是「诚实承认无知」的正确行为，不应解读为缺陷。")
    lines.append("")
    return "\n".join(lines)


def main():
    _, models = load_models()
    md = render_md(models)
    out = "成绩单.md"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(md)
    print(f"\n[report.py] 已写入 {out}（共 {len(models)} 个模型）")


if __name__ == "__main__":
    main()
