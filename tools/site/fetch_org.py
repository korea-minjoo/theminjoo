"""당 홈페이지 '사람들'(조직도) 페이지 수집. 공개 페이지만 받아 원문 HTML과 텍스트를 저장한다."""
import re, html, json, time, urllib.request, pathlib
OUT = pathlib.Path(__file__).parent / "org"; OUT.mkdir(exist_ok=True)
BASE = "https://theminjoo.kr/main/sub/introduce/team.php"
UA = {"User-Agent": "Mozilla/5.0 (compatible; theminjoo-org-fetch/1.0)"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "ignore")
def text(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    s = re.sub(r"<(br|/p|/li|/div|/tr|/h\d|/dt|/dd)[^>]*>", "\n", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return "\n".join(l.strip() for l in re.sub(r"[ \t]+", " ", s).splitlines() if l.strip())
pages = {"team": BASE}
for c in range(1, 8): pages[f"class{c}"] = f"{BASE}?class={c}"
meta = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pages": {}}
for k, u in pages.items():
    try:
        h = get(u); (OUT / f"{k}.html").write_text(h, encoding="utf-8")
        t = text(h); (OUT / f"{k}.txt").write_text(t, encoding="utf-8")
        meta["pages"][k] = {"url": u, "ok": True, "chars": len(t)}
    except Exception as e:
        meta["pages"][k] = {"url": u, "ok": False, "error": str(e)[:200]}
    time.sleep(1)
(OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(meta, ensure_ascii=False))
