"""당 홈페이지 '사람들'(조직도) 페이지 수집. 공개 페이지만 받아 원문 HTML과 텍스트를 저장한다."""
import re, html, json, time, urllib.request, pathlib
OUT = pathlib.Path(__file__).parent / "org"; OUT.mkdir(exist_ok=True)
BASE = "https://theminjoo.kr/main/sub/introduce/team.php"
import http.cookiejar
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,*/*;q=0.8", "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.5", "Referer": "https://theminjoo.kr/"}
JAR = http.cookiejar.CookieJar()
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR), NoRedir)
CHAIN = []
def get(url, hops=8):
    # 리다이렉트를 직접 따라가며(쿠키 유지) 경로를 기록한다. 같은 주소로 되돌아오면 한 번 더 시도 후 중단.
    seen = []
    for _ in range(hops):
        req = urllib.request.Request(url, headers=UA)
        try:
            with OP.open(req, timeout=60) as r:
                return r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                loc = e.headers.get("Location", ""); seen.append((e.code, loc)); CHAIN.append((url, e.code, loc, dict(e.headers).get("Set-Cookie", "")[:80]))
                url = urllib.parse.urljoin(url, loc)
                if seen.count((e.code, loc)) > 2: raise RuntimeError("redirect loop: " + str(seen))
                continue
            raise
    raise RuntimeError("too many redirects: " + str(seen))
import urllib.parse, urllib.error
def text(s):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
    s = re.sub(r"<(br|/p|/li|/div|/tr|/h\d|/dt|/dd)[^>]*>", "\n", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return "\n".join(l.strip() for l in re.sub(r"[ \t]+", " ", s).splitlines() if l.strip())
pages = {"team": BASE, "team_www": BASE.replace("https://theminjoo.kr", "https://www.theminjoo.kr"), "home": "https://theminjoo.kr/"}
for c in range(1, 8): pages[f"class{c}"] = f"{BASE}?class={c}"
meta = {"redirects": None, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pages": {}}
for k, u in pages.items():
    try:
        h = get(u); (OUT / f"{k}.html").write_text(h, encoding="utf-8")
        t = text(h); (OUT / f"{k}.txt").write_text(t, encoding="utf-8")
        meta["pages"][k] = {"url": u, "ok": True, "chars": len(t)}
    except Exception as e:
        meta["pages"][k] = {"url": u, "ok": False, "error": str(e)[:200]}
    time.sleep(1)
meta["redirects"] = CHAIN
(OUT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(meta, ensure_ascii=False))
