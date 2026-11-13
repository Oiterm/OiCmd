'use strict';
// 명령어 맞추기: 사용자가 친 명령어(줄임말 포함)가 어느 항목·벤더의 몇째 줄인지 찾고,
// <자리> 에 들어간 값(포트, VLAN, IP, MAC …)을 뽑아서 다른 벤더 형식으로 바꿔 채운다.
//
//   sh int status            → show interfaces status (시스코)
//   sh mac add add 0011.2233.4455 → MAC 을 다른 벤더 형식(00:11:22:33:44:55)으로
//   int gi1/0/5 + sw acc vlan 10 → 포트 번호 5 를 ge-0/0/4, port1.0.5, 1/5, 1/1/5 로

(function () {
  const PH = /<([^<>\n]{1,24})>/g;
  const EAT_REST = new Set(['설명', '문구']); // 여러 단어가 들어갈 수 있는 자리

  // 프롬프트·do 떼고 소문자로
  O.normInput = function (s) {
    let t = String(s || '').replace(/\t/g, ' ').trim();
    t = t.replace(/^(\S+@\S+[>#%]|\S*[#>]|->)\s*/, '');
    t = t.replace(/^do\s+/i, '');
    return t.replace(/\s+/g, ' ').trim();
  };

  // 명령어 한 줄을 조각으로: {lit:'show'} 또는 {re, names} (자리 표시가 섞인 조각)
  function compileLine(line) {
    const toks = line.trim().split(/\s+/).filter(Boolean);
    return toks.map((t) => {
      if (!t.includes('<')) return { lit: t.toLowerCase() };
      const names = [];
      let src = '^', last = 0, m;
      PH.lastIndex = 0;
      while ((m = PH.exec(t))) {
        src += esc(t.slice(last, m.index).toLowerCase());
        src += '(.+?)';
        names.push(m[1]);
        last = m.index + m[0].length;
      }
      src += esc(t.slice(last).toLowerCase()) + '$';
      return { re: new RegExp(src), names, whole: names.length === 1 && t === '<' + names[0] + '>' };
    });
  }
  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  const cache = new Map();
  function compiled(cmd) {
    let c = cache.get(cmd);
    if (!c) {
      c = cmd.split('\n').map((l) => l.trim()).filter(Boolean).map((l) => ({ line: l, toks: compileLine(l) }));
      cache.set(cmd, c);
    }
    return c;
  }

  // 입력 조각들 I 와 명령 조각들 T 를 앞에서부터 맞춘다. 맞으면 점수와 뽑은 값.
  // 글자 그대로인 조각은 줄임말(앞부분) 허용. 입력이 더 짧으면 부분 점수.
  function matchTokens(I, T, raw) {
    // 명령은 글자로 시작해야 한다 (<문구> 처럼 자리 표시만 있는 줄은 맞추지 않음)
    if (!T.length || T[0].lit === undefined) return null;
    if (I.length > T.length) {
      // 끝에 따옴표 이름(설명 등) 이 여러 단어인 경우: 마지막 자리 표시가 나머지를 다 먹게
      const lastT = T[T.length - 1];
      if (!(lastT && lastT.whole && EAT_REST.has(lastT.names[0])) || T.length < 3) return null;
    }
    let score = 0, exact = 0;
    const caps = {};
    for (let i = 0; i < I.length; i++) {
      const t = T[i];
      if (!t) {
        // 마지막 자리 표시가 남은 단어를 먹는다
        const lastT = T[T.length - 1];
        const nm = lastT.names[0];
        caps[nm] = (caps[nm] + ' ' + raw[i]).trim();
        continue;
      }
      const w = I[i];
      if (t.lit !== undefined) {
        if (t.lit === w) { score += 2; exact++; }
        else if (t.lit.startsWith(w) && /^[a-z]/.test(w)) score += 1.5;
        else return null;
      } else {
        const m = w.match(t.re);
        if (!m) return null;
        t.names.forEach((n, k) => { caps[n] = restoreCase(raw[i], m[k + 1], w); });
        score += 1;
      }
    }
    const coverage = I.length / T.length;
    return { score: score * (0.55 + 0.45 * Math.min(1, coverage)) + (I.length >= T.length ? 1.5 : 0), caps, exact, coverage };
  }
  // 정규식은 소문자로 맞췄으니 원래 글자(대소문자) 그대로 돌려준다
  function restoreCase(rawTok, lowPart, lowTok) {
    const i = lowTok.indexOf(lowPart);
    return i >= 0 ? rawTok.slice(i, i + lowPart.length) : lowPart;
  }

  // 입력 전체를 모든 항목·벤더·줄과 맞춰 본다. src 를 주면 그 벤더만.
  O.matchCommand = function (input, src) {
    const text = O.normInput(input);
    if (!text) return [];
    const raw = text.split(' ');
    const I = raw.map((w) => w.toLowerCase());
    const best = new Map(); // entry id → 최고 결과
    for (const e of O.entries()) {
      for (const [vid, x] of Object.entries(e.v)) {
        if (!x.cmd || (src && src !== vid)) continue;
        for (const ln of compiled(x.cmd)) {
          const r = matchTokens(I, ln.toks, raw);
          if (!r) continue;
          const prev = best.get(e.id);
          if (!prev || r.score > prev.score) best.set(e.id, { entry: e, vendor: vid, line: ln.line, ...r });
        }
      }
    }
    return [...best.values()].sort((a, b) => b.score - a.score || b.exact - a.exact);
  };

  // 여러 줄을 붙여 넣은 경우: 줄마다 맞춰 보고 항목별로 점수를 더하고 뽑은 값을 합친다.
  O.matchText = function (text, src) {
    const lines = String(text || '').split(/\r?\n/).map((l) => O.normInput(l)).filter((l) => l && !/^[!#]/.test(l));
    if (!lines.length) return [];
    if (lines.length === 1) return O.matchCommand(lines[0], src).slice(0, 8);
    const agg = new Map();
    for (const l of lines) {
      for (const r of O.matchCommand(l, src).slice(0, 80)) {
        const a = agg.get(r.entry.id);
        if (!a) agg.set(r.entry.id, { ...r, caps: { ...r.caps }, hits: 1, lines: [r.line] });
        else {
          a.score += r.score;
          a.hits++;
          Object.assign(a.caps, r.caps);
          if (!a.lines.includes(r.line)) a.lines.push(r.line);
        }
      }
    }
    return [...agg.values()].sort((a, b) => b.hits - a.hits || b.score - a.score).slice(0, 8);
  };

  // ---------- 값 바꾸기 ----------

  // 포트 이름에서 앞판 번호(1부터)를 뽑는다
  O.portNumber = function (name, vid) {
    const s = String(name || '');
    const m = s.match(/(\d+)\s*$/);
    if (!m) return null;
    let n = parseInt(m[1], 10);
    const looksJunos = /^(ge|xe|et|mge|fe)-\d+\/\d+\/\d+$/i.test(s);
    if (vid === 'j' || looksJunos) n += 1; // 주니퍼는 0부터
    return n;
  };
  O.portName = function (n, vid) {
    const p = (O.user && O.user.settings.ports[vid]) || O.DEFAULT_PORTS[vid];
    return p.prefix + (n - 1 + p.base);
  };

  O.normMac = function (s) {
    const hex = String(s || '').replace(/[^0-9a-f]/gi, '').toLowerCase();
    return hex.length === 12 ? hex : null;
  };
  O.fmtMac = function (hex, vid) {
    if (vid === 'c' || vid === 'a') return hex.slice(0, 4) + '.' + hex.slice(4, 8) + '.' + hex.slice(8);
    return hex.match(/../g).join(':');
  };

  function maskToPrefix(m) {
    const p = String(m).split('.').map(Number);
    if (p.length !== 4 || p.some((x) => !(x >= 0 && x <= 255))) return null;
    const bits = p.map((x) => x.toString(2).padStart(8, '0')).join('');
    if (!/^1*0*$/.test(bits)) return null;
    return String(bits.indexOf('0') === -1 ? 32 : bits.indexOf('0'));
  }
  function prefixToMask(n) {
    n = Number(n);
    if (!(n >= 0 && n <= 32)) return null;
    const bits = '1'.repeat(n).padEnd(32, '0');
    return [0, 8, 16, 24].map((i) => parseInt(bits.slice(i, i + 8), 2)).join('.');
  }
  O.maskToPrefix = maskToPrefix;
  O.prefixToMask = prefixToMask;

  // 뽑은 값(caps, 원래 벤더 src)을 벤더 vid 의 명령어에 채운다. 바꾼 값은 표시용으로 따로 돌려준다.
  O.fillCommand = function (cmd, caps, src, vid) {
    const vals = { ...caps };
    // 와일드카드(0.0.0.255) ↔ 마스크(255.255.255.0)
    const inv = (m) => { const p = String(m).split('.').map(Number); return p.length === 4 && p.every((x) => x >= 0 && x <= 255) ? p.map((x) => 255 - x).join('.') : null; };
    if (vals['와일드카드'] && !vals['마스크']) { const m = inv(vals['와일드카드']); if (m && maskToPrefix(m)) vals['마스크'] = m; }
    if (vals['마스크'] && !vals['와일드카드']) { const w = inv(vals['마스크']); if (w) vals['와일드카드'] = w; }
    if (vals['마스크'] && !vals['프리픽스']) { const p = maskToPrefix(vals['마스크']); if (p) vals['프리픽스'] = p; }
    if (vals['프리픽스'] && !vals['마스크']) { const m = prefixToMask(vals['프리픽스']); if (m) vals['마스크'] = m; }
    if (vals['마스크'] && !vals['와일드카드']) { const w = inv(vals['마스크']); if (w) vals['와일드카드'] = w; }
    // IP/24 처럼 한 덩어리로 들어온 경우
    for (const k of ['IP', '대역']) {
      if (vals[k] && vals[k].includes('/')) {
        const [ip, pre] = vals[k].split('/');
        vals[k] = ip;
        if (!vals['프리픽스']) vals['프리픽스'] = pre;
        if (!vals['마스크']) { const m = prefixToMask(pre); if (m) vals['마스크'] = m; }
      }
    }
    if (vals['마스크'] && !vals['와일드카드']) { const w = inv(vals['마스크']); if (w) vals['와일드카드'] = w; }
    if (!vals['VLAN목록'] && vals['VLAN번호']) vals['VLAN목록'] = vals['VLAN번호'];
    if (!vals['VLAN번호'] && vals['VLAN목록'] && /^\d+$/.test(vals['VLAN목록'])) vals['VLAN번호'] = vals['VLAN목록'];
    const changed = new Set();
    const out = cmd.replace(PH, (all, name) => {
      let v = vals[name];
      if (v == null) return all;
      if ((name === '포트' || name === '받는포트' || name === '업링크포트') && src !== vid) {
        const n = O.portNumber(v, src);
        if (n) { v = O.portName(n, vid); changed.add(name); }
      } else if (name === 'MAC') {
        const hx = O.normMac(v);
        if (hx) { const f = O.fmtMac(hx, vid); if (f !== v) changed.add(name); v = f; }
      }
      return v;
    });
    return { text: out, changed: [...changed] };
  };
})();
