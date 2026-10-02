// ── 선거 정보 (중앙선관위 공공데이터: 당선인·후보자·선거공약·정당정책) ──
// 원자료는 GitHub Actions에서 서비스키로 수집(키는 저장소 비밀값, 앱에는 없음) → nec_export.py로 압축한 nec.json·nec_<선거ID>.json을 지원 파일로 싣는다.
// 원칙: 선관위가 공개한 항목만 그대로 보여 주고 순위·비교·평가는 하지 않는다. 정렬은 선거구(지역)·기호 순.
let NECI=null,NECIP=null;const NECD={},NECDP={};
function loadNecIndex(){if(!NECIP)NECIP=fetch('nec.json').then(r=>{if(!r.ok)throw 0;return r.json()}).then(j=>{NECI=j;rerenderKeepScroll()}).catch(()=>{NECI={err:1};rerenderKeepScroll()});return NECIP}
function loadNec(sg){if(!NECDP[sg])NECDP[sg]=fetch('nec_'+sg+'.json').then(r=>{if(!r.ok)throw 0;return r.json()}).then(j=>{NECD[sg]=j;rerenderKeepScroll()}).catch(()=>{NECD[sg]={err:1};rerenderKeepScroll()});return NECDP[sg]}
const EL={sg:'',tc:'',sd:'',more:0,cand:false};
const necPlace=r=>[...new Set([r[1],r[2],r[3]].filter(Boolean))].join(' ');
function necSort(a,b){return (a[1]+a[2]+a[3]).localeCompare(b[1]+b[2]+b[3],'ko')||(+a[6]||99)-(+b[6]||99)}
function elecView(){
  if(!NECI){loadNecIndex();return '<p class="note">선거 데이터를 불러오는 중…</p>'}
  if(NECI.err)return '<div class="card"><span class="pill apply">불러오기 실패</span><span class="meta">선거 데이터 파일(nec.json)을 읽지 못했어요. 잠시 뒤 다시 열어 주세요.</span></div>';
  const E=NECI.elections;if(!EL.sg)EL.sg=E[0].sg;const e=E.find(x=>x.sg===EL.sg)||E[0];
  if(!EL.tc||!e.types.some(t=>t.tc===EL.tc))EL.tc=e.types[0].tc;
  const t=e.types.find(x=>x.tc===EL.tc);
  let h=`<div class="sec">선거 고르기</div><div class="pills" role="group" aria-label="선거">${E.map(x=>`<button class="pill ${x.sg===e.sg?'':'done'}" data-elsg="${x.sg}" aria-pressed="${x.sg===e.sg}">${esc(x.name)} · ${x.date}</button>`).join('')}</div>
  <div class="sec">${esc(e.name)} (${e.date})</div><div class="pills" role="group" aria-label="선거 종류">${e.types.map(x=>`<button class="pill ${x.tc===EL.tc?'':'done'}" data-eltc="${x.tc}" aria-pressed="${x.tc===EL.tc}">${esc(x.name)} ${x.nW}</button>`).join('')}</div>`;
  const D=NECD[e.sg];
  if(!D){loadNec(e.sg);return h+'<p class="note">이 선거의 자료를 불러오는 중…</p>'}
  if(D.err)return h+'<p class="note">이 선거의 자료 파일을 읽지 못했어요.</p>';
  const W=(D.w[EL.tc]||[]).slice().sort(necSort),C=(D.c[EL.tc]||[]).slice().sort(necSort);
  const sds=[...new Set(W.map(r=>r[1]))].filter(s=>s&&s!=='전국');
  if(EL.sd&&!sds.includes(EL.sd))EL.sd='';
  if(sds.length>1)h+=`<div class="pills" role="group" aria-label="시도" style="margin-top:8px"><button class="pill ${EL.sd?'done':''}" data-elsd="">전체</button>${sds.map(s=>`<button class="pill ${EL.sd===s?'':'done'}" data-elsd="${esc(s)}">${esc(s.replace(/특별자치|특별|광역/g,'').replace(/(시|도)$/,''))}</button>`).join('')}</div>`;
  const list=(EL.cand?C:W).filter(r=>!EL.sd||r[1]===EL.sd),lim=50*(EL.more+1);
  h+=`<div class="sec">${EL.cand?'후보자':'당선인'} ${list.length}명${EL.sd?' · '+esc(EL.sd):''}</div>`;
  if(C.length)h+=`<div class="row"><button class="btn ghost" data-elcand="${EL.cand?'0':'1'}">${EL.cand?'당선인 보기':'후보자 전체 보기 ('+C.length+'명)'}</button></div>`;
  else if(t.nC)h+=`<p class="note">후보자 ${t.nC}명은 인원만 집계했어요(목록은 선관위 선거통계시스템에서 확인).</p>`;
  else h+=`<p class="note">이 선거의 후보자 목록은 선관위 API에서 받지 못했어요(당선인만 표시).</p>`;
  h+=`<div class="list">${list.slice(0,lim).map(r=>{const pl=D.p[r[0]];const st=EL.cand&&r[7]&&r[7]!=='등록'?`<span class="pill done">${esc(r[7])}</span>`:'';
    const inner=`<span class="pills"><span class="pill">${esc(r[4]||'무소속')}</span>${r[6]?`<span class="pill done">기호 ${esc(r[6])}</span>`:''}${st}${pl?'<span class="pill apply">공약 '+pl.length+'</span>':''}</span><b>${esc(r[5])}</b><span class="meta"><span>${esc(necPlace(r))}</span>${!EL.cand&&r[7]?`<span>득표율 ${esc(r[7])}%</span>`:''}${!EL.cand&&r[8]?`<span>${esc(r[8])}</span>`:''}</span>`;
    return pl?`<button class="item" data-open="necp:${e.sg}|${r[0]}">${inner}</button>`:`<div class="item" style="cursor:default">${inner}</div>`}).join('')}</div>`;
  if(list.length>lim)h+=`<div class="row"><button class="btn ghost" data-elmore="1">더 보기 (${list.length-lim}명 남음)</button></div>`;
  if(e.parties.length)h+=`<div class="sec">정당정책 (선관위 제출본, ${e.parties.length}개 정당)</div><div class="list">${e.parties.map(p=>`<button class="item" data-open="necpp:${e.sg}|${esc(p)}"><span class="pill">정당정책</span><b>${esc(p)}</b><span class="meta"><span>${D.pp[p]?D.pp[p].length+'개 분야':''}</span></span></button>`).join('')}</div>`;
  h+=`<p class="note">출처: ${esc(NECI.source)}. 수집 ${esc(e.fetched||'')}. 선관위 공개 항목만 그대로 옮겼고 순위·비교·평가는 하지 않습니다. 정렬은 지역·기호 순입니다. 선거공약은 선관위가 공개한 범위(대체로 당선인)만 있습니다. 선거기간에는 이 화면 문구도 법무 검토 뒤 게시합니다.</p>
  <div class="row"><a class="btn ghost" href="https://info.nec.go.kr/" target="_blank" rel="noopener">선거통계시스템 ↗</a><a class="btn ghost" href="https://policy.nec.go.kr/" target="_blank" rel="noopener">정책·공약마당 ↗</a></div>`;
  return h}
function necPledgeHTML(ps){return `<div class="list">${ps.map((p,i)=>`<details class="card"><summary><span class="pill">${esc(p[0]||'공약 '+(i+1))}</span> <b>${esc(p[1])}</b></summary><div style="white-space:pre-wrap;margin-top:8px;font-size:14px;line-height:1.6">${esc(p[2])}</div></details>`).join('')}</div>`}
function necPersonView(id){const[sg,cid]=id.split('|');const D=NECD[sg];if(!D||D.err){loadNec(sg);return '<p class="note">불러오는 중…</p>'}
  let r=null;for(const k in D.w){r=D.w[k].find(x=>x[0]===cid);if(r)break}if(!r)for(const k in D.c){r=D.c[k].find(x=>x[0]===cid);if(r)break}
  const e=NECI.elections.find(x=>x.sg===sg);const ps=D.p[cid]||[];
  return `<div class="card"><span class="pills"><span class="pill">${esc(r?r[4]||'무소속':'')}</span></span><h3>${esc(r?r[5]:'')}</h3><p class="meta">${esc(e?e.name:'')} · ${esc(r?necPlace(r):'')}</p></div><div class="sec">선거공약 ${ps.length}개</div>${necPledgeHTML(ps)}<p class="note">출처: 중앙선거관리위원회 선거공약 정보(data.go.kr), 원문 그대로. 수집 ${esc(e?e.fetched:'')}.</p>`}
function necPartyView(id){const i=id.indexOf('|'),sg=id.slice(0,i),p=id.slice(i+1);const D=NECD[sg];if(!D||D.err){loadNec(sg);return '<p class="note">불러오는 중…</p>'}
  const e=NECI.elections.find(x=>x.sg===sg);const ps=D.pp[p]||[];
  return `<div class="card"><h3>${esc(p)}</h3><p class="meta">${esc(e?e.name:'')} 정당정책 · ${ps.length}개 분야</p></div>${necPledgeHTML(ps)}<p class="note">출처: 중앙선거관리위원회 정당정책 정보(data.go.kr), 정당이 선관위에 낸 원문 그대로. 수집 ${esc(e?e.fetched:'')}.</p>`}
