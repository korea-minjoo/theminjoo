"""gov/nec/<sgId>.json(선관위 원자료) → 앱용 압축 파일 out/nec.json(색인) + out/nec_<sgId>.json.
후보자 정보는 선관위 공개 항목만 옮기고, 순위·평가 항목은 만들지 않는다."""
import json, os, glob, re
B = os.path.dirname(os.path.abspath(__file__))
SRC, OUT = os.path.join(B, "nec"), os.path.join(B, "nec_out")
os.makedirs(OUT, exist_ok=True)
NAMES = {"20260603": ("제9회 전국동시지방선거", "2026.6.3"), "20250603": ("제21대 대통령선거", "2025.6.3"),
         "20240410": ("제22대 국회의원선거", "2024.4.10"), "20220601": ("제8회 전국동시지방선거", "2022.6.1"),
         "20220309": ("제20대 대통령선거", "2022.3.9"), "20200415": ("제21대 국회의원선거", "2020.4.15"),
         "20180613": ("제7회 전국동시지방선거", "2018.6.13"), "20170509": ("제19대 대통령선거", "2017.5.9"),
         "20160413": ("제20대 국회의원선거", "2016.4.13")}
TNAME = {"1": "대통령", "2": "국회의원(지역구)", "7": "국회의원(비례)", "3": "시·도지사", "4": "구·시·군의 장",
         "11": "교육감", "5": "시·도의원", "6": "구·시·군의원", "8": "광역의원(비례)", "9": "기초의원(비례)"}
ORDER = ["1", "3", "4", "11", "2", "7", "5", "6", "8", "9"]
CAND_TYPES = {"1", "2", "3", "4", "7", "11"}  # 후보자 목록까지 싣는 선거(지방의원은 인원만)


def pledges(item, name_key="prms"):
    n = int(item.get("prmsCnt") or 0)
    out = []
    for i in range(1, max(n, 10) + 1):
        t = (item.get(f"prmsTitle{i}") or "").strip()
        if t:
            out.append([(item.get(f"prmsRealmName{i}") or "").strip(), t, (item.get(f"prmmCont{i}") or "").strip()])
    return out


index = {"source": "중앙선거관리위원회 공공데이터(data.go.kr OpenAPI: 당선인·후보자·선거공약·정당정책 정보)", "elections": []}
for f in sorted(glob.glob(os.path.join(SRC, "20*.json")), reverse=True):
    d = json.load(open(f, encoding="utf-8"))
    sg = d["sgId"]
    nm, dt = NAMES.get(sg, (sg, sg))
    e = {"sg": sg, "name": nm, "date": dt, "fetched": d.get("fetched_at"), "types": [], "parties": []}
    o = {"sg": sg, "w": {}, "c": {}, "p": {}, "pp": {}}
    for tc in ORDER:
        if tc not in d["types"]:
            continue
        r = d["types"][tc]
        W = r["winners"]["items"]; C = r["candidates"]["items"]
        if not W and not C:
            continue
        o["w"][tc] = [[w.get("huboid"), w.get("sdName") or "", w.get("sggName") or "", w.get("wiwName") or "",
                       w.get("jdName") or "", w.get("name") or "", w.get("giho") or "", w.get("dugyul") or "",
                       w.get("job") or ""] for w in W]
        if tc in CAND_TYPES and C:
            o["c"][tc] = [[c.get("huboid"), c.get("sdName") or "", c.get("sggName") or "", c.get("wiwName") or "",
                           c.get("jdName") or "", c.get("name") or "", c.get("giho") or "", c.get("status") or ""] for c in C]
        for cid, pr in r["pledges"].items():
            if pr["items"]:
                ps = pledges(pr["items"][0])
                if ps:
                    o["p"][cid] = ps
        e["types"].append({"tc": tc, "name": TNAME.get(tc, r["name"]), "nW": len(W), "nC": len(C)})
    for pn, r in d["party_policy"].items():
        ps = pledges(r["items"][0]) if r["items"] else []
        if ps:
            o["pp"][pn] = ps
    e["parties"] = sorted(o["pp"])
    e["nP"] = len(o["p"])
    index["elections"].append(e)
    json.dump(o, open(os.path.join(OUT, f"nec_{sg}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(index, open(os.path.join(OUT, "nec.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
for fn in sorted(os.listdir(OUT)):
    print(fn, os.path.getsize(os.path.join(OUT, fn)) // 1024, "KB")
