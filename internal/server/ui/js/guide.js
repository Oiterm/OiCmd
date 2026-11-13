'use strict';
// 따라하기(작업 순서): 자리(<이름>) 모으기·값 채우기. 화면은 app.js 의 guidePage.

(function () {
  const PH = /<([^<>\n]{1,24})>/g;
  const PORTS = ['포트', '업링크포트', '포트1', '포트2', '받는포트'];

  // 벤더 하나의 단계·확인·되돌리기에서 자리 이름을 나온 순서대로
  O.guidePlaceholders = function (gv) {
    const seen = [];
    for (const part of ['steps', 'check', 'undo']) {
      for (const st of gv[part] || []) {
        for (const m of st.c.matchAll(PH)) if (!seen.includes(m[1])) seen.push(m[1]);
      }
    }
    return seen;
  };

  // 넣은 값으로 바꾸기. 비어 있는 자리는 그대로 둔다(화면에서 강조)
  O.guideFill = function (cmd, vals) {
    return cmd.replace(PH, (all, name) => {
      const x = vals && typeof vals[name] === 'string' ? vals[name].trim() : '';
      return x || all;
    });
  };

  // 입력칸 예시: 포트 계열은 벤더 형식으로
  O.guideHint = function (name, vid) {
    if (PORTS.includes(name)) {
      const p = (O.user && O.user.settings.ports && O.user.settings.ports[vid]) || O.DEFAULT_PORTS[vid];
      const n = name === '포트2' ? 2 : name === '업링크포트' ? 24 : name === '받는포트' ? 23 : 1;
      return p.prefix + (p.base === 0 ? n - 1 : n);
    }
    return (O.data.hints || {})[name] || '';
  };

  // 사전 항목 id → 그 항목을 쓰는 따라하기 목록
  O.guidesForEntry = function (id) {
    if (!O._g4e) {
      O._g4e = {};
      for (const g of O.data.guides || []) for (const r of g.rel || []) (O._g4e[r] = O._g4e[r] || []).push(g);
    }
    return O._g4e[id] || [];
  };

  // 찾기: 제목·설명·검색어·명령어
  O.searchGuides = function (q, vids) {
    const list = O.data.guides || [];
    const toks = q.trim().toLowerCase().split(/\s+/).filter(Boolean);
    if (!toks.length) return list.slice();
    const out = [];
    for (const g of list) {
      const cmds = [];
      for (const vid of vids) {
        const x = g.v[vid];
        if (x && x.steps) for (const st of x.steps) if (!st.auto) cmds.push(st.c);
      }
      const head = (g.t + ' ' + g.k + ' ' + ((O.catById[g.cat] || {}).name || '')).toLowerCase();
      const hay = head + ' ' + (g.d + ' ' + cmds.join(' ')).toLowerCase();
      if (!toks.every((t) => hay.includes(t))) continue;
      out.push({ g, rank: toks.filter((t) => head.includes(t)).length });
    }
    return out.sort((a, b) => b.rank - a.rank).map((x) => x.g);
  };
})();
