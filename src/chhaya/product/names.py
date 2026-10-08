"""Display names for patients. They are pseudonyms: neither dataset holds a name (rule 7: say so on screen).

Every patient of a cohort gets a different surname from that cohort's list, in an order fixed by a hash of the
dataset's own identifier, so a rebuild gives the same names. The honorific follows the sex the dataset records
and is left out where none is recorded. The synthetic demo patient is "Mrs. R." and no real patient can be.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping

SURNAMES: dict[str, tuple[str, ...]] = {
    "shanghai": (
        "Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Wu", "Zhou",
        "Xu", "Sun", "Ma", "Zhu", "Hu", "Guo", "He", "Gao", "Lin", "Luo",
        "Zheng", "Liang", "Xie", "Song", "Tang", "Han", "Feng", "Deng", "Cao", "Peng",
        "Zeng", "Xiao", "Tian", "Dong", "Pan", "Yuan", "Cai", "Jiang", "Yu", "Du",
        "Ye", "Cheng", "Wei", "Su", "Lu", "Ding", "Ren", "Shen", "Yao", "Lyu",
        "Fu", "Zhong", "Cui", "Tan", "Liao", "Fan", "Wan", "Qin", "Shi", "Jia",
        "Xia", "Fang", "Bai", "Zou", "Meng", "Xiong", "Qiu", "Jin", "Hao", "Kong",
        "Xue", "Lei", "Duan", "Hou", "Long", "Tao", "Mao", "Gu", "Lai", "Wen",
        "Qian", "Niu", "Hong", "Gong", "Shao", "Yan", "Dai", "Mo", "Kang", "Yin",
        "Qi", "Pang", "Geng", "Zhuang", "Nie", "Zuo", "Bao", "Ji", "Xing", "Ruan",
        "Ke", "Ou", "Shu", "Min",
    ),
    "cgmacros": (
        "Rivera", "Brooks", "Nguyen", "Carter", "Patel", "Johnson", "Williams", "Brown", "Davis", "Miller",
        "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson",
        "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Walker", "Hall", "Allen", "Young",
        "Hernandez", "King", "Wright", "Lopez", "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez",
        "Nelson", "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards",
        "Collins", "Stewart", "Sanchez", "Morris", "Rogers", "Reed", "Cook", "Morgan", "Bell", "Murphy",
    ),
}  # fmt: skip
HONORIFIC = {"M": "Mr.", "F": "Ms."}


def pseudonyms(patient_ids: Iterable[str], dataset: str, sex: Mapping[str, str | None]) -> dict[str, str]:
    """A display name for every patient of one cohort. Pass the whole cohort, so names do not move between builds."""
    if dataset not in SURNAMES:
        raise ValueError(f"no names for cohort {dataset!r}; known: {sorted(SURNAMES)}")
    names = SURNAMES[dataset]
    ids = sorted(set(patient_ids), key=lambda pid: hashlib.sha256(pid.encode()).hexdigest())
    if len(ids) > len(names):
        raise ValueError(f"{len(ids)} patients and only {len(names)} names for cohort {dataset!r}")
    out = {}
    for pid, surname in zip(ids, names, strict=False):
        title = HONORIFIC.get(str(sex.get(pid) or "").strip().upper()[:1])
        out[pid] = f"{title} {surname}" if title else surname
    return out
