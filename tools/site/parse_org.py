"""org/team.txt(수집 결과)에서 중앙당 직책·이름 목록을 뽑아 org/org_central.json으로 저장."""
import re, json, pathlib, time
D = pathlib.Path(__file__).parent / "org"
L = (D / "team.txt").read_text(encoding="utf-8").splitlines()
i = [k for k, l in enumerate(L) if l.startswith("목록 :")][0] + 1
j = [k for k, l in enumerate(L) if k > i and l == "상임고문"][0]
T = re.compile(r"^[가-힣\s]{0,20}(대표|최고위원|총장|부총장|의장|부의장|대변인|부대표|위원장|실장|단장|원장)(\([가-힣]+\))?$")
skip = {"유튜브", "페이스북", "인스타그램", "네이버블로그", "트위터", "카카오스토리", "국회"}
out = []; k = i
while k < j:
    t = L[k]
    if T.match(t) and k + 1 < j and re.fullmatch(r"[가-힣]{2,4}", L[k + 1]) and L[k + 1] not in skip and not T.match(L[k + 1]):
        out.append([t, L[k + 1]]); k += 2
    else: k += 1
meta = json.loads((D / "meta.json").read_text(encoding="utf-8"))
(D / "org_central.json").write_text(json.dumps({"source": "https://theminjoo.kr/main/sub/introduce/team.php", "fetched_at": meta["fetched_at"], "section": "중앙당", "items": out}, ensure_ascii=False, indent=0), encoding="utf-8")
print(len(out))
