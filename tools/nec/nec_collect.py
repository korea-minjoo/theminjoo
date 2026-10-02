"""선관위 공공데이터 수집기 (서버측 실행용).

서비스키는 환경변수 DATA_GO_KR_SERVICE_KEY 또는 실행 시 입력(화면 미표시)으로만 받고, 출력·파일에 남기지 않는다.
범위: 선관위가 제공하는 모든 선거(공통코드 목록 기준)의
  당선인 · 후보자 · 선거공약(후보자/당선인) · 정당정책.
결과: gov/nec/<sgId>.json (선거별 1파일) + gov/nec/index.json. 앱(elec.js)은 이 결과만 싣는다.
이미 받은 선거 파일은 건너뛰므로(이어받기), 일일 호출 한도에 걸리면 다음 날 다시 돌리면 된다.

사용(내 PC): python nec_collect.py  → 키 입력 → 끝나면 nec_result.zip 생성. 옵션 [--only 20260603] [--budget 9000]
"""
import argparse, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta

BASE = "https://apis.data.go.kr/9760000/"
KEY = os.environ.get("DATA_GO_KR_SERVICE_KEY", "")
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nec")
KST = timezone(timedelta(hours=9))
# 선거공약 API가 다루는 선거종류: 1 대통령, 3 시·도지사, 4 구·시·군의 장, 11 교육감
PLEDGE_TYPES = {"1", "3", "4", "11"}

API = {
    "codes": "CommonCodeService/getCommonSgCodeList",
    "parties": "CommonCodeService/getCommonPartyCodeList",
    "winners": "WinnerInfoInqireService2/getWinnerInfoInqire",
    "candidates": "PofelcddInfoInqireService/getPofelcddRegistSttusInfoInqire",
    "pledges": "ElecPrmsInfoInqireService/getCnddtElecPrmsInfoInqire",
    "party_policy": "PartyPlcInfoInqireService/getPartyPlcInfoInqire",
}


class Budget(Exception):
    pass


calls = 0
budget = 9000


def call_page(path, page, **params):
    global calls
    if calls >= budget:
        raise Budget()
    calls += 1
    q = {"pageNo": page, "numOfRows": 100, "resultType": "json", **params}
    url = BASE + path + "?" + urllib.parse.urlencode(q) + "&serviceKey=" + KEY
    err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:  # 키가 담긴 URL은 절대 출력하지 않는다
            body = e.read().decode("utf-8", "replace")[:300].replace(KEY, "***") if KEY else ""
            err = f"HTTP{e.code} {body}".strip()
            if e.code in (401, 403):
                break
        except Exception as e:
            err = type(e).__name__
            time.sleep(2 ** attempt)
    return {"_error": err}


def fetch_all(name, **params):
    """페이지를 끝까지 넘겨 items 전체와 결과코드를 돌려준다."""
    path, items, page, code, total = API[name], [], 1, None, 0
    while True:
        d = call_page(path, page, **params)
        if "_error" in d:
            return {"code": "NETWORK:" + d["_error"], "total": len(items), "items": items}
        hdr = d.get("response", {}).get("header") or d.get("OpenAPI_ServiceResponse", {}).get("cmmMsgHeader", {})
        code = hdr.get("resultCode") or hdr.get("errMsg")
        body = d.get("response", {}).get("body") or {}
        got = (body.get("items") or {}).get("item") or []
        if isinstance(got, dict):
            got = [got]
        items += got
        total = int(body.get("totalCount") or 0)
        if code not in ("INFO-00", "00") or not got or len(items) >= total:
            return {"code": code, "total": total, "items": items}
        page += 1


def collect_election(sg_id, types, parties):
    out = {"sgId": sg_id, "types": {}, "party_policy": {}}
    pledge_ids = set()
    for t in types:
        tc = t["sgTypecode"]
        rec = {"name": t.get("sgName"), "winners": fetch_all("winners", sgId=sg_id, sgTypecode=tc),
               "candidates": fetch_all("candidates", sgId=sg_id, sgTypecode=tc), "pledges": {}}
        if tc in PLEDGE_TYPES:
            people = rec["candidates"]["items"] or rec["winners"]["items"]
            for p in people:
                cid = p.get("huboid") or p.get("cnddtId")
                if cid and cid not in pledge_ids:
                    pledge_ids.add(cid)
                    rec["pledges"][cid] = fetch_all("pledges", sgId=sg_id, sgTypecode=tc, cnddtId=cid)
        out["types"][tc] = rec
    for pn in parties:
        r = fetch_all("party_policy", sgId=sg_id, partyName=pn)
        if r["items"]:
            out["party_policy"][pn] = r
    return out


def main():
    global budget, KEY
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="이 sgId 하나만 수집")
    ap.add_argument("--probe", action="store_true", help="API별 1회씩 호출해 승인·접속 상태만 확인")
    ap.add_argument("--budget", type=int, default=9000, help="이번 실행 최대 호출 수")
    a = ap.parse_args()
    budget = a.budget
    if not KEY:  # 내 PC에서 실행할 때: 화면에 표시되지 않게 입력받는다
        import getpass
        KEY = getpass.getpass("data.go.kr 일반 인증키(Decoding)를 붙여넣고 Enter: ").strip()
    if not KEY:
        sys.exit("인증키가 없습니다.")
    KEY = urllib.parse.quote(KEY, safe="")
    os.makedirs(OUTDIR, exist_ok=True)
    if a.probe:
        sample = {"sgId": "20220601", "sgTypecode": "3"}
        tests = {"codes": {}, "parties": {"sgId": "20220601"}, "winners": sample, "candidates": sample,
                 "pledges": {**sample, "cnddtId": "0"}, "party_policy": {"sgId": "20220601", "partyName": "더불어민주당"}}
        for name, prm in tests.items():
            d = call_page(API[name], 1, **prm)
            if "_error" in d:
                print(f"[{name}] 실패: {d['_error']}")
            else:
                hdr = d.get("response", {}).get("header") or d.get("OpenAPI_ServiceResponse", {}).get("cmmMsgHeader", {})
                print(f"[{name}] 응답: {json.dumps(hdr, ensure_ascii=False)[:200]}")
        return

    codes = fetch_all("codes")
    print("선거코드", codes["code"], codes["total"])
    if not codes["items"]:
        sys.exit("선거코드를 받지 못했습니다(활용신청·키 확인).")
    by_sg = {}
    for c in codes["items"]:
        if c.get("sgTypecode") != "0":  # 0 = 선거 대표코드
            by_sg.setdefault(c["sgId"], []).append(c)
    sg_ids = sorted(by_sg, reverse=True)  # 최근 선거부터
    if a.only:
        sg_ids = [a.only]

    index = {"source": "중앙선거관리위원회, 공공데이터포털(data.go.kr) OpenAPI", "elections": {}}
    idx_path = os.path.join(OUTDIR, "index.json")
    if os.path.exists(idx_path):
        index = json.load(open(idx_path, encoding="utf-8"))
    try:
        for sg in sg_ids:
            fp = os.path.join(OUTDIR, f"{sg}.json")
            if os.path.exists(fp):
                continue
            parties = [p["jdName"] for p in fetch_all("parties", sgId=sg)["items"] if p.get("jdName")]
            data = collect_election(sg, by_sg.get(sg, []), parties)
            data["fetched_at"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
            json.dump(data, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
            summary = {tc: {"name": r["name"], "winners": len(r["winners"]["items"]),
                            "candidates": len(r["candidates"]["items"]), "pledges": len(r["pledges"]),
                            "codes": [r["winners"]["code"], r["candidates"]["code"]]}
                       for tc, r in data["types"].items()}
            index["elections"][sg] = {"fetched_at": data["fetched_at"], "types": summary,
                                      "party_policy": list(data["party_policy"])}
            print(sg, json.dumps(summary, ensure_ascii=False))
    except Budget:
        print(f"호출 한도({budget}) 도달 — 다음 실행 때 이어받습니다.")
    json.dump(index, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("총 호출", calls)
    import shutil
    z = shutil.make_archive(os.path.join(os.path.dirname(OUTDIR), "nec_result"), "zip", OUTDIR)
    print("완료. 이 파일을 프로젝트에 올려 주세요:", z)


if __name__ == "__main__":
    main()
