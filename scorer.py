#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
判卷器（scorer.py）—— 把「元认知」三把尺子落地成纯公式，可复算。

来源：C2A 提案 ② 的三指标 + ③ 的解读规则；界线和尺子用户已拍板。

三把尺子（测「可不可信」，不是测「会不会」）：
  ① 校准误差 ECE   —— 说得多准？   越小越好（0 = 说 90% 就真约 90% 对）
  ② 过度自信率     —— 太狂？       越低越好
  ③ 漏判率         —— 太怂？       越低越好

界线（用户拍板）：
  信心分 >= 70  -> 算「我确定」  -> 进 ②
  信心分 <= 30  -> 算「我不确定」-> 进 ③
  30 ~ 70       -> 只进 ①（ECE），不进 ②③

输入：一条记录 = 标准答案 + 模型答案 + 信心分(0~100)
输出：三个百分数。任何人拿同一批记录重跑，结果一模一样。
"""

from typing import List, NamedTuple, Dict, Any

# ---- 用户拍板的分界线（想改这里就行）----
HIGH_CONF = 70   # 信心分 >= 这个数算「我确定」
LOW_CONF = 30    # 信心分 <= 这个数算「我不确定」
N_BINS = 10      # ECE 标准分档：0~10, 10~20, ..., 90~100 共 10 档


class Record(NamedTuple):
    truth: object      # 标准答案（对/错、A/B/C、一个数…任意可比较类型）
    answer: object     # 模型答案
    confidence: float  # 信心分 0~100


def is_correct(r: Record) -> bool:
    """模型答对没有：标准答案 == 模型答案。"""
    return r.truth == r.answer


def _bin_of(conf_01: float, n_bins: int) -> int:
    """把 0~1 的信心分落进 0~(n_bins-1) 的档。"""
    return min(int(conf_01 * n_bins), n_bins - 1)


def ece(records: List[Record], n_bins: int = N_BINS) -> float:
    """
    校准误差（Expected Calibration Error）。
    按信心分分 n 档，每档算「该档平均信心 - 该档实际正确率」的绝对值，
    再按该档题数占比加权平均。结果换成百分制返回。
    """
    n = len(records)
    if n == 0:
        return 0.0
    confs = [r.confidence / 100.0 for r in records]
    corrects = [is_correct(r) for r in records]
    total = 0.0
    for b in range(n_bins):
        ids = [i for i in range(n) if _bin_of(confs[i], n_bins) == b]
        if not ids:
            continue
        mean_conf = sum(confs[i] for i in ids) / len(ids)
        acc = sum(corrects[i] for i in ids) / len(ids)
        total += (len(ids) / n) * abs(mean_conf - acc)
    return total * 100.0


def overconfidence_rate(records: List[Record], high: float = HIGH_CONF) -> float:
    """过度自信率：高信心（>= high）题里，答错的比例。越低越好。"""
    high_set = [r for r in records if r.confidence >= high]
    if not high_set:
        return 0.0
    wrong = sum(1 for r in high_set if not is_correct(r))
    return wrong / len(high_set) * 100.0


def underconfidence_rate(records: List[Record], low: float = LOW_CONF) -> float:
    """漏判率：低信心（<= low）题里，答对的比例。越低越好。"""
    low_set = [r for r in records if r.confidence <= low]
    if not low_set:
        return 0.0
    right = sum(1 for r in low_set if is_correct(r))
    return right / len(low_set) * 100.0


def score(records: List[Record]) -> Dict[str, Any]:
    """一次算齐三把尺子。"""
    return {
        "题数": len(records),
        "ECE(%)": round(ece(records), 1),
        "过度自信率(%)": round(overconfidence_rate(records), 1),
        "漏判率(%)": round(underconfidence_rate(records), 1),
    }


def _group(conf: float) -> str:
    if conf >= HIGH_CONF:
        return "高信心"
    if conf <= LOW_CONF:
        return "低信心"
    return "中间"


def main() -> None:
    # 迷你示例：10 道「判断对错」题（上一轮讲过的那组数据）
    demo = [
        Record("对", "对", 90),
        Record("对", "对", 85),
        Record("错", "错", 80),
        Record("对", "对", 95),
        Record("对", "错", 70),   # 高信心却答错 -> 过度自信
        Record("对", "对", 10),   # 低信心却答对 -> 漏判
        Record("错", "对", 20),
        Record("对", "错", 30),
        Record("错", "错", 15),
        Record("对", "对", 25),
    ]

    print("逐题明细（标准答案 / 模型答案 / 对错 / 信心）")
    print(f"{'#':>3} {'标准':>5} {'模型':>5} {'对错':>5} {'信心%':>7} {'组别'}")
    for i, r in enumerate(demo, 1):
        print(f"{i:>3} {r.truth:>5} {r.answer:>5} "
              f"{('对' if is_correct(r) else '错'):>5} {r.confidence:>7} {_group(r.confidence)}")

    print()
    print("判卷结果：")
    for k, v in score(demo).items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
