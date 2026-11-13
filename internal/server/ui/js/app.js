'use strict';
// OiCmd 화면: 명령어 사전 / 명령어 변환 / 설정 만들기 / 내 명령어 / 설정

(function () {
  const { h, clear } = O;
  const ROUTES = [
    ['', '명령어 사전', 'book'],
    ['convert', '명령어 변환', 'swap'],
    ['gen', '설정 만들기', 'wand'],
    ['mine', '내 명령어', 'star'],
    ['settings', '설정', 'gear'],
  ];
  const ICONS = {
    book: 'M4 4h6a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H4zM20 4h-6a3 3 0 0 0-3 3v13a2 2 0 0 1 2-2h7z',
    swap: 'M7 7h13l-4-4M17 17H4l4 4',
    wand: 'M4 20 15 9M14 4v3M20 10h-3M18.5 5.5l-2 2M9 4.5 10 6M19.5 14.5 18 13.5',
    star: 'M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8L3.5 9.7l5.9-.9z',
    gear: 'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM19.4 13a7.5 7.5 0 0 0 0-2l2-1.6-2-3.4-2.4 1a7.6 7.6 0 0 0-1.7-1L15 3.5h-4l-.4 2.5a7.6 7.6 0 0 0-1.7 1l-2.4-1-2 3.4L6.6 11a7.5 7.5 0 0 0 0 2l-2 1.6 2 3.4 2.4-1a7.6 7.6 0 0 0 1.7 1l.4 2.5h4l.4-2.5a7.6 7.6 0 0 0 1.7-1l2.4 1 2-3.4z',
    copy: 'M9 9h10v11H9zM5 15V4h10',
    edit: 'M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4',
  };
  const NS = 'http://www.w3.org/2000/svg';
  O.icon = function (name, size) {
    const s = document.createElementNS(NS, 'svg');
    s.setAttribute('viewBox', '0 0 24 24');
    s.setAttribute('width', size || 18);
    s.setAttribute('height', size || 18);
    s.setAttribute('aria-hidden', 'true');
    s.setAttribute('class', 'ico');
    const p = document.createElementNS(NS, 'path');
    p.setAttribute('d', ICONS[name]);
    s.append(p);
    return s;
  };

  let main, titleEl, toolsEl;

  async function start() {
    const app = document.getElementById('app');
    try {
      O.info = await O.api('GET', '/api/info');
      await Promise.all([O.loadData(), O.loadUser()]);
    } catch (e) {
      clear(app).append(h('div', { class: 'fatal' }, h('h1', null, 'OiCmd'), h('p', null, e.message)));
      return;
    }
    const nav = h('nav', { class: 'nav', 'aria-label': '메뉴' }, ROUTES.map(([r, label, ic]) =>
      h('a', { href: '#/' + r, dataset: { r } }, O.icon(ic, 20), h('span', null, label))));
    titleEl = h('h1');
    toolsEl = h('div', { class: 'top-tools' });
    main = h('main', { class: 'page', id: 'page' });
    clear(app).append(
      h('aside', { class: 'rail' },
        h('div', { class: 'brand' }, h('b', null, 'Oi'), 'Cmd'),
        nav,
        h('div', { class: 'rail-foot' }, 'v' + O.info.version)),
      h('div', { class: 'main' }, h('header', { class: 'top' }, titleEl, toolsEl), main));
    window.addEventListener('hashchange', route);
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        const f = document.querySelector('[data-focus]');
        if (f) f.focus(); else location.hash = '#/';
      }
    });
    route();
  }

  function route() {
    const r = (location.hash.replace(/^#\/?/, '').split('?')[0]) || '';
    const page = { '': dictPage, convert: convertPage, gen: genPage, mine: minePage, settings: settingsPage }[r] || dictPage;
    for (const a of document.querySelectorAll('.nav a')) a.classList.toggle('on', a.dataset.r === r);
    clear(main);
    clear(toolsEl);
    main.scrollTop = 0;
    page();
  }
  O.rerender = route;

  function setTitle(t) { titleEl.textContent = t; document.title = t + ' · OiCmd'; }

  // ---------------- 벤더 고르기 (사전·변환 위쪽) ----------------
  function vendorChips(onChange) {
    const box = h('div', { class: 'vchips', role: 'group', 'aria-label': '보여 줄 벤더' });
    const draw = () => {
      clear(box);
      const vis = O.visibleVendors();
      for (const v of O.data.vendors) {
        const on = vis.includes(v.id);
        box.append(h('button', { type: 'button', class: 'vchip ' + (on ? 'on' : ''), 'aria-pressed': String(on), title: v.os,
          onclick: () => {
            let next = O.visibleVendors().slice();
            if (on) { if (next.length === 1) return O.toast('하나는 보여야 합니다'); next = next.filter((x) => x !== v.id); }
            else next.push(v.id);
            O.user.settings.vendors = O.data.vendors.map((x) => x.id).filter((id) => next.includes(id));
            O.saveUser();
            draw();
            onChange();
          } }, v.name));
      }
    };
    draw();
    return box;
  }

  // ---------------- 명령어 카드 ----------------
  // opts.fill: {caps, src} 변환 결과로 값 채우기, opts.matchVendor: 입력과 맞은 벤더
  function entryCard(e, opts = {}) {
    const vis = O.visibleVendors();
    const grid = h('div', { class: 'vgrid' });
    for (const vid of vis) grid.append(vendorCell(e, vid, opts));
    const cat = O.catById[e.cat];
    return h('article', { class: 'card' + (e.custom ? ' custom' : ''), id: 'e-' + e.id },
      h('div', { class: 'card-h' },
        h('h3', null, e.t),
        h('span', { class: 'kind k-' + e.kind }, O.kindLabel[e.kind] || e.kind),
        opts.showCat && cat ? h('span', { class: 'catname' }, cat.name) : null,
        e.custom ? h('span', { class: 'badge mine' }, '내 명령어') : null,
        h('span', { class: 'grow' }),
        e.custom ? h('button', { type: 'button', class: 'ghost sm', onclick: () => editCustom(e.id) }, '고치기') : null),
      e.d ? h('p', { class: 'desc' }, e.d) : null,
      grid);
  }

  function vendorCell(e, vid, opts) {
    const v = O.vendorById[vid];
    const x = e.v[vid] || { cmd: null, note: '' };
    let text = x.cmd;
    let changed = [];
    if (text && opts.fill) {
      const r = O.fillCommand(text, opts.fill.caps, opts.fill.src, vid);
      text = r.text;
      changed = r.changed;
    }
    const verified = x.cmd ? O.isVerified(e.id, vid, x.cmd) : false;
    const cell = h('section', { class: 'vcell' + (opts.matchVendor === vid ? ' hit' : '') + (x.cmd ? '' : ' none'), 'aria-label': v.name });
    const head = h('div', { class: 'vcell-h' }, h('b', null, v.name), h('span', { class: 'os' }, v.os));
    if (x.mine) head.append(h('span', { class: 'badge mine', title: '기본 명령어를 내가 고친 것' }, '내가 고침'));
    if (x.cmd && !e.custom) {
      const vb = h('button', { type: 'button', class: 'vbadge ' + (verified ? 'ok' : ''), 'aria-pressed': String(verified),
        title: verified ? `확인됨 (${(O.user.verified[e.id + ':' + vid] || {}).at || ''}) — 누르면 미확인으로` : '실제 장비에서 쳐 봤으면 눌러서 확인됨으로 표시',
        onclick: () => {
          O.setVerified(e.id, vid, x.cmd, !verified);
          cell.replaceWith(vendorCell(e, vid, opts));
        } }, verified ? '✓ 확인됨' : '미확인');
      head.append(h('span', { class: 'grow' }), vb);
    }
    cell.append(head);
    if (x.cmd) {
      cell.append(O.cmdEl(text));
      if (changed.length) cell.append(h('div', { class: 'note conv' }, changed.includes('포트') || changed.includes('받는포트') ? '포트 이름을 이 벤더 형식으로 바꿔 넣었습니다' : 'MAC 형식을 이 벤더에 맞게 바꿔 넣었습니다'));
      if (x.note) cell.append(h('div', { class: 'note' }, x.note));
      if (e.kind === 'config') cell.append(h('div', { class: 'mode' }, v.config ? '설정 모드: ' + v.config : '설정 모드 없이 바로 입력'));
      cell.append(h('div', { class: 'vcell-a' },
        h('button', { type: 'button', class: 'ghost sm', onclick: () => O.copy(text) }, O.icon('copy', 14), '복사'),
        !e.custom ? h('button', { type: 'button', class: 'ghost sm', onclick: () => editOverride(e, vid) }, O.icon('edit', 14), '고치기') : null));
    } else {
      cell.append(h('div', { class: 'na' }, '해당 명령 없음'));
      if (x.note) cell.append(h('div', { class: 'note' }, x.note));
      if (!e.custom) cell.append(h('div', { class: 'vcell-a' }, h('button', { type: 'button', class: 'ghost sm', onclick: () => editOverride(e, vid) }, O.icon('edit', 14), '내 명령어 넣기')));
    }
    return cell;
  }

  // 기본 명령어를 내 것으로 고치기
  function editOverride(e, vid) {
    const v = O.vendorById[vid];
    const key = e.id + ':' + vid;
    const orig = (O.data.entries.find((x) => x.id === e.id) || { v: {} }).v[vid] || {};
    const cur = O.user.overrides[key] || { cmd: orig.cmd || '', note: orig.note || '' };
    const ta = h('textarea', { rows: 5, class: 'mono', spellcheck: 'false', 'aria-label': '명령어' });
    ta.value = cur.cmd || '';
    const note = h('input', { type: 'text', maxlength: 300, 'aria-label': '메모' });
    note.value = cur.note || '';
    O.modal(`${e.t} — ${v.name}`, h('div', { class: 'form1' },
      h('p', { class: 'muted small' }, '고친 내용은 이 PC 에만 저장되고, 기본 데이터가 업데이트돼도 내 것이 먼저 보입니다. 바꿀 값은 <포트> 처럼 꺾쇠로 두면 변환·검색에서 자리로 인식합니다.'),
      h('label', null, '명령어 (여러 줄 가능)'), ta,
      h('label', null, '메모'), note,
      orig.cmd ? h('details', { class: 'orig' }, h('summary', null, '원래 명령어'), O.cmdEl(orig.cmd)) : null),
    (close) => [
      O.user.overrides[key] ? h('button', { type: 'button', class: 'ghost', onclick: () => {
        delete O.user.overrides[key]; O.saveUser(); close(); O.rerender(); O.toast('원래대로 돌렸습니다');
      } }, '원래대로') : null,
      h('span', { class: 'grow' }),
      h('button', { type: 'button', class: 'ghost', onclick: close }, '취소'),
      h('button', { type: 'button', class: 'primary', onclick: () => {
        const cmd = ta.value.replace(/\r/g, '').replace(/\s+$/g, '');
        if (cmd === (orig.cmd || '') && note.value.trim() === (orig.note || '')) delete O.user.overrides[key];
        else O.user.overrides[key] = { cmd: cmd || null, note: note.value.trim() };
        O.saveUser(); close(); O.rerender(); O.toast('저장했습니다');
      } }, '저장'),
    ]);
  }

  // ---------------- 명령어 사전 ----------------
  const dictState = { q: '', cat: '' };

  function searchEntries(q, cat) {
    const all = O.entries().filter((e) => !cat || e.cat === cat);
    const query = q.trim().toLowerCase();
    if (!query) return all.map((e) => ({ e, rank: 0 }));
    const toks = query.split(/\s+/);
    const vis = O.visibleVendors();
    const abbrev = /[a-z]/.test(query) ? new Map(O.matchCommand(query).filter((r) => r.score >= 2).map((r) => [r.entry.id, r])) : new Map();
    const out = [];
    for (const e of all) {
      const catName = (O.catById[e.cat] || {}).name || '';
      const hay = [e.t, e.d, e.k, catName, ...vis.map((v) => (e.v[v].cmd || '') + ' ' + (e.v[v].note || ''))].join(' ').toLowerCase();
      const sub = toks.every((t) => hay.includes(t));
      const ab = abbrev.get(e.id);
      if (!sub && !ab) continue;
      let rank = sub ? 1 : 0;
      if (e.t.toLowerCase().includes(query)) rank += 3;
      if (ab) rank += 2 + ab.coverage;
      out.push({ e, rank, ab });
    }
    return out.sort((a, b) => b.rank - a.rank);
  }

  function dictPage() {
    setTitle('명령어 사전');
    const results = h('div', { class: 'results' });
    const q = h('input', { type: 'search', class: 'big-search', placeholder: '하는 일이나 명령어로 찾기 — 예: 맥 주소, 트렁크, sh int status, show vlans', 'aria-label': '찾기', dataset: { focus: '1' } });
    q.value = dictState.q;
    const cats = h('div', { class: 'cats', role: 'group', 'aria-label': '분야' });
    const drawCats = () => {
      clear(cats);
      const counts = {};
      for (const e of O.entries()) counts[e.cat] = (counts[e.cat] || 0) + 1;
      const btn = (id, label, n) => h('button', { type: 'button', class: 'cat ' + (dictState.cat === id ? 'on' : ''), 'aria-pressed': String(dictState.cat === id),
        onclick: () => { dictState.cat = dictState.cat === id && id ? '' : id; drawCats(); draw(); } }, label, n != null ? h('span', { class: 'n' }, String(n)) : null);
      cats.append(btn('', '전체', null));
      for (const c of O.data.cats) if (counts[c.id]) cats.append(btn(c.id, c.name, counts[c.id]));
    };
    let t;
    q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => { dictState.q = q.value; draw(); }, 120); });
    toolsEl.append(vendorChips(() => draw()));

    function draw() {
      clear(results);
      const list = searchEntries(dictState.q, dictState.cat);
      if (!list.length) {
        results.append(h('div', { class: 'empty' }, '찾는 명령어가 없습니다. ', h('a', { href: '#/mine' }, '내 명령어'), '에 직접 넣어 둘 수 있습니다.'));
        return;
      }
      if (dictState.q.trim()) {
        results.append(h('div', { class: 'count' }, `${list.length}개 찾음`));
        for (const r of list) results.append(entryCard(r.e, { showCat: true, matchVendor: r.ab && r.ab.vendor }));
        return;
      }
      for (const c of O.data.cats) {
        const items = list.filter((r) => r.e.cat === c.id);
        if (!items.length) continue;
        results.append(h('h2', { class: 'sec', id: 'cat-' + c.id }, c.name, h('span', { class: 'n' }, String(items.length))));
        for (const r of items) results.append(entryCard(r.e));
      }
    }
    main.append(h('div', { class: 'dict-top' }, q, cats), results);
    drawCats();
    draw();
    setTimeout(() => q.focus(), 0);
  }

  // ---------------- 명령어 변환 ----------------
  const convState = { text: '', src: '' };
  const EXAMPLES = ['sh int status', 'switchport access vlan 10', 'show mac address-table address 0011.2233.4455',
    'show ethernet-switching table', 'vlan 20 members port 1/1/24 tagged', 'show lldp remote-system', 'wr'];

  function convertPage() {
    setTitle('명령어 변환');
    const ta = h('textarea', { rows: 3, class: 'mono conv-in', spellcheck: 'false', placeholder: '아는 명령어를 넣으세요 (어느 벤더든, 줄임말도 됨). 여러 줄도 됩니다.\n예: sh mac add add 0011.2233.4455', 'aria-label': '변환할 명령어', dataset: { focus: '1' } });
    ta.value = convState.text;
    const src = h('select', { 'aria-label': '입력한 명령어의 벤더' }, h('option', { value: '' }, '벤더 자동으로 찾기'),
      O.data.vendors.map((v) => h('option', { value: v.id }, v.name + ' 명령어')));
    src.value = convState.src;
    const out = h('div', { class: 'results' });
    const ex = h('div', { class: 'examples' }, h('span', { class: 'muted small' }, '예시:'), EXAMPLES.map((x) =>
      h('button', { type: 'button', class: 'chip', onclick: () => { ta.value = x; convState.text = x; draw(); ta.focus(); } }, x)));
    let t;
    ta.addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => { convState.text = ta.value; draw(); }, 150); });
    src.addEventListener('change', () => { convState.src = src.value; draw(); });
    toolsEl.append(vendorChips(() => draw()));

    function draw() {
      clear(out);
      const text = convState.text.trim();
      if (!text) {
        out.append(h('div', { class: 'help' },
          h('p', null, '명령어를 넣으면 같은 일을 하는 다른 벤더 명령어를 보여 줍니다.'),
          h('ul', null,
            h('li', null, '줄임말을 알아봅니다: sh run, sh int status, conf t, wr …'),
            h('li', null, '포트·VLAN·IP·MAC 값을 넣으면 다른 벤더 형식으로 바꿔 채웁니다 (Gi1/0/5 → ge-0/0/4 → port1.0.5 → 1/5 → 1/1/5).'),
            h('li', null, '프롬프트(Switch#, ->, user@sw>)를 같이 붙여 넣어도 됩니다.'))));
        return;
      }
      const res = O.matchText(text, convState.src).filter((r) => r.score >= 1.5);
      if (!res.length) {
        out.append(h('div', { class: 'empty' }, '알아본 명령어가 없습니다. 오타가 없는지, 위에서 벤더를 골라 보세요. 자주 쓰는 명령이면 ',
          h('a', { href: '#/mine' }, '내 명령어'), '에 넣어 두세요.'));
        return;
      }
      res.forEach((r, i) => {
        const v = O.vendorById[r.vendor];
        const caps = Object.entries(r.caps).filter(([, x]) => x);
        const info = h('div', { class: 'conv-info' + (i === 0 ? ' best' : '') },
          h('span', null, i === 0 ? '가장 가까운 것: ' : ''),
          h('b', null, v.name), ' 의 ', h('code', null, (r.lines || [r.line]).join(' / ')),
          caps.length ? h('span', { class: 'caps' }, '  값: ', caps.map(([k, x]) => h('span', { class: 'cap' }, k + ' = ' + x))) : null);
        out.append(info, entryCard(r.entry, { showCat: true, matchVendor: r.vendor, fill: { caps: r.caps, src: r.vendor } }));
      });
    }
    main.append(h('div', { class: 'conv-top' }, ta, h('div', { class: 'conv-row' }, src, h('span', { class: 'grow' }), ex)), out);
    draw();
    setTimeout(() => ta.focus(), 0);
  }

  // ---------------- 설정 만들기 ----------------
  const GEN_DEFAULT = () => ({ hostname: '', l3: false, tz: true, vlans: [{ id: '', name: '' }], ports: [{ ports: '', mode: 'access', vlan: '', allowed: '', native: '', desc: '' }],
    lags: [], mgmtVlan: '', mgmtIp: '', gateway: '', ntp: '', syslog: '', community: '', ssh: true, user: 'admin', vendor: 'c' });
  const GEN_SAMPLE = () => ({ hostname: 'SW-3F-01', l3: false, tz: true,
    vlans: [{ id: '10', name: 'OFFICE' }, { id: '20', name: 'CCTV' }, { id: '99', name: 'MGMT' }],
    ports: [{ ports: '1-20', mode: 'access', vlan: '10', allowed: '', native: '', desc: 'PC' },
      { ports: '21-22', mode: 'access', vlan: '20', allowed: '', native: '', desc: 'CCTV' },
      { ports: '24', mode: 'trunk', vlan: '', allowed: '10,20,99', native: '', desc: 'UPLINK-CORE' }],
    lags: [{ id: '1', ports: '25-26', allowed: '10,20,99', desc: 'TO-CORE' }],
    mgmtVlan: '99', mgmtIp: '10.0.99.13/24', gateway: '10.0.99.1', ntp: '10.0.99.5', syslog: '10.0.99.5', community: 'oi-read', ssh: true, user: 'admin', vendor: 'c' });

  function genPage() {
    setTitle('설정 만들기');
    if (!O.user.gen) O.user.gen = GEN_DEFAULT();
    const g = O.user.gen;
    for (const k of ['vlans', 'ports', 'lags']) if (!Array.isArray(g[k])) g[k] = [];
    const vis = O.visibleVendors();
    if (!vis.includes(g.vendor)) g.vendor = vis[0];

    const form = h('div', { class: 'gen-form' });
    const outBox = h('div', { class: 'gen-out' });
    const changed = () => { O.saveUser(); drawOut(); };

    const field = (label, key, attrs = {}) => {
      const inp = h('input', { type: 'text', ...attrs, 'aria-label': label });
      inp.value = g[key] || '';
      inp.addEventListener('input', () => { g[key] = inp.value; changed(); });
      return h('label', { class: 'f' }, h('span', null, label), inp);
    };
    const check = (label, key, hint) => {
      const c = h('input', { type: 'checkbox', checked: !!g[key] });
      c.addEventListener('change', () => { g[key] = c.checked; changed(); });
      return h('label', { class: 'chk', title: hint || '' }, c, label);
    };
    // 줄이 여러 개인 표 (VLAN, 포트, LACP)
    const rows = (key, cols, blank, addLabel) => {
      const box = h('div', { class: 'rows' });
      const draw = () => {
        clear(box);
        box.append(h('div', { class: 'row head' }, cols.map((c) => h('span', { class: 'c-' + c.w }, c.label)), h('span', { class: 'c-x' })));
        g[key].forEach((r, i) => {
          const row = h('div', { class: 'row' });
          for (const c of cols) {
            let el;
            if (c.type === 'mode') {
              el = h('select', { 'aria-label': c.label }, h('option', { value: 'access' }, 'access'), h('option', { value: 'trunk' }, 'trunk'));
              el.value = r[c.key] || 'access';
              el.addEventListener('change', () => { r[c.key] = el.value; draw(); changed(); });
            } else {
              const dis = c.only && (r.mode || 'access') !== c.only;
              el = h('input', { type: 'text', placeholder: dis ? '—' : c.ph || '', disabled: dis, 'aria-label': c.label, class: c.mono ? 'mono' : '' });
              el.value = dis ? '' : r[c.key] || '';
              el.addEventListener('input', () => { r[c.key] = el.value; changed(); });
            }
            row.append(h('span', { class: 'c-' + c.w }, el));
          }
          row.append(h('span', { class: 'c-x' }, h('button', { type: 'button', class: 'ghost icon-btn', 'aria-label': '이 줄 지우기', onclick: () => { g[key].splice(i, 1); draw(); changed(); } }, '✕')));
          box.append(row);
        });
        box.append(h('button', { type: 'button', class: 'ghost sm add', onclick: () => { g[key].push(blank()); draw(); changed(); const ins = box.querySelectorAll('.row:last-of-type input'); if (ins[0]) ins[0].focus(); } }, '+ ' + addLabel));
      };
      draw();
      return box;
    };

    const drawForm = () => {
      clear(form).append(
        h('div', { class: 'gen-actions' },
          h('button', { type: 'button', class: 'ghost sm', onclick: () => { O.user.gen = Object.assign(GEN_SAMPLE(), { vendor: g.vendor }); O.saveUser(); O.rerender(); } }, '예시 넣기'),
          h('button', { type: 'button', class: 'ghost sm', onclick: async () => { if (await O.confirm('입력한 내용을 모두 지울까요?', '지우기', true)) { O.user.gen = GEN_DEFAULT(); O.saveUser(); O.rerender(); } } }, '모두 지우기')),
        h('fieldset', null, h('legend', null, '기본'),
          h('div', { class: 'grid2' }, field('장비 이름', 'hostname', { placeholder: 'SW-3F-01', maxlength: 63 }),
            h('div', { class: 'chks' }, check('L3 스위치 (라우팅 사용)', 'l3', '게이트웨이를 기본 경로로 넣습니다'), check('시간대 한국(KST)', 'tz')))),
        h('fieldset', null, h('legend', null, 'VLAN'),
          rows('vlans', [{ key: 'id', label: '번호', w: 's', ph: '10' }, { key: 'name', label: '이름', w: 'm', ph: 'OFFICE' }], () => ({ id: '', name: '' }), 'VLAN 추가')),
        h('fieldset', null, h('legend', null, '포트'),
          h('p', { class: 'muted small' }, '포트는 앞판 번호로 넣습니다 (예: 1-20, 24). 벤더별 포트 이름 앞부분은 [설정]에서 바꿉니다.'),
          rows('ports', [
            { key: 'ports', label: '포트', w: 's', ph: '1-20', mono: true },
            { key: 'mode', label: '종류', w: 'mode', type: 'mode' },
            { key: 'vlan', label: 'VLAN', w: 's', ph: '10', only: 'access' },
            { key: 'allowed', label: '허용 VLAN', w: 'm', ph: '10,20,30', only: 'trunk', mono: true },
            { key: 'native', label: 'native', w: 's', ph: '', only: 'trunk' },
            { key: 'desc', label: '설명', w: 'm', ph: 'PC' }],
          () => ({ ports: '', mode: 'access', vlan: '', allowed: '', native: '', desc: '' }), '포트 줄 추가')),
        h('fieldset', null, h('legend', null, '포트 묶기 (LACP, 트렁크)'),
          rows('lags', [
            { key: 'id', label: '번호', w: 's', ph: '1' },
            { key: 'ports', label: '포트', w: 's', ph: '25-26', mono: true },
            { key: 'allowed', label: '허용 VLAN', w: 'm', ph: '10,20', mono: true },
            { key: 'desc', label: '설명', w: 'm', ph: 'TO-CORE' }],
          () => ({ id: String((g.lags.length || 0) + 1), ports: '', allowed: '', desc: '' }), 'LACP 추가')),
        h('fieldset', null, h('legend', null, '관리 IP'),
          h('div', { class: 'grid3' }, field('관리 VLAN', 'mgmtVlan', { placeholder: '99' }), field('관리 IP', 'mgmtIp', { placeholder: '10.0.99.13/24', class: 'mono' }), field('게이트웨이', 'gateway', { placeholder: '10.0.99.1', class: 'mono' }))),
        h('fieldset', null, h('legend', null, '관리 서비스'),
          h('div', { class: 'grid3' }, field('NTP 서버', 'ntp', { placeholder: '10.0.99.5', class: 'mono' }), field('로그 서버 (syslog)', 'syslog', { placeholder: 'OiLog 서버 IP', class: 'mono' }),
            field('SNMP 읽기 커뮤니티', 'community', { placeholder: 'public 은 쓰지 마세요', maxlength: 32 })),
          h('div', { class: 'grid3' }, h('div', { class: 'chks' }, check('SSH 켜고 관리자 계정 만들기', 'ssh')), field('관리자 계정 이름', 'user', { placeholder: 'admin', maxlength: 32 }))));
    };

    const tabs = h('div', { class: 'tabs', role: 'tablist' });
    const outPre = h('div');
    function drawOut() {
      clear(tabs);
      for (const vid of O.visibleVendors()) {
        const v = O.vendorById[vid];
        tabs.append(h('button', { type: 'button', role: 'tab', class: 'tab ' + (g.vendor === vid ? 'on' : ''), 'aria-selected': String(g.vendor === vid),
          onclick: () => { g.vendor = vid; O.saveUser(); drawOut(); } }, v.name));
      }
      clear(outPre);
      const r = O.generate(g, g.vendor);
      if (r.errors.length) {
        outPre.append(h('div', { class: 'errs' }, h('b', null, '고칠 곳'), h('ul', null, r.errors.map((x) => h('li', null, x)))));
        return;
      }
      const v = O.vendorById[g.vendor];
      outPre.append(
        h('div', { class: 'out-a' },
          h('button', { type: 'button', class: 'primary sm', onclick: () => O.copy(r.text) }, O.icon('copy', 14), '복사'),
          h('button', { type: 'button', class: 'ghost sm', onclick: () => O.download(`${g.hostname || 'switch'}-${g.vendor}.txt`, r.text.replace(/\n/g, '\r\n') + '\r\n') }, '파일로 저장'),
          h('span', { class: 'grow' }), h('span', { class: 'muted small' }, `${r.text.split('\n').length}줄`)),
        O.cmdEl(r.text, 'gen-text'),
        r.notes.length ? h('ul', { class: 'gen-notes' }, r.notes.map((n) => h('li', null, n))) : null,
        h('p', { class: 'muted small' }, `넣기 전에 꼭 읽어 보세요. 랩(PNETLab)이나 콘솔로 붙은 장비에서 먼저 시험하는 것을 권합니다. ${v.name} 저장: ${v.save}`));
    }
    outBox.append(h('div', { class: 'out-h' }, h('b', null, '만들어진 설정'), tabs), outPre);
    drawForm();
    drawOut();
    main.append(h('div', { class: 'gen' }, form, outBox));
  }

  // ---------------- 내 명령어 ----------------
  function editCustom(id) {
    const isNew = !id;
    const src = isNew ? { id: O.uid(), cat: 'misc', kind: 'show', t: '', d: '', k: '', v: {} } : JSON.parse(JSON.stringify(O.user.custom.find((c) => c.id === id)));
    if (!src) return;
    const t = h('input', { type: 'text', maxlength: 80, placeholder: '예: 포트 보안 위반 풀기', 'aria-label': '제목' }); t.value = src.t || '';
    const cat = h('select', { 'aria-label': '분야' }, O.data.cats.map((c) => h('option', { value: c.id }, c.name))); cat.value = src.cat || 'misc';
    const kind = h('select', { 'aria-label': '종류' }, Object.entries(O.kindLabel).map(([k, l]) => h('option', { value: k }, l))); kind.value = src.kind || 'show';
    const d = h('input', { type: 'text', maxlength: 300, placeholder: '언제 쓰는지 (선택)', 'aria-label': '설명' }); d.value = src.d || '';
    const k = h('input', { type: 'text', maxlength: 200, placeholder: '찾을 때 쓸 말 (선택): err-disable 에러 풀기', 'aria-label': '검색어' }); k.value = src.k || '';
    const vfields = {};
    const vbox = h('div', { class: 'vedit' });
    for (const v of O.data.vendors) {
      const x = (src.v && src.v[v.id]) || {};
      const ta = h('textarea', { rows: 3, class: 'mono', spellcheck: 'false', placeholder: `${v.name} 명령어 (없으면 비워 두기). 바꿀 값은 <포트> 처럼`, 'aria-label': v.name + ' 명령어' }); ta.value = x.cmd || '';
      const note = h('input', { type: 'text', maxlength: 300, placeholder: '메모', 'aria-label': v.name + ' 메모' }); note.value = x.note || '';
      vfields[v.id] = { ta, note };
      vbox.append(h('div', { class: 'vedit-r' }, h('b', null, v.name), ta, note));
    }
    O.modal(isNew ? '내 명령어 추가' : '내 명령어 고치기', h('div', { class: 'form1' },
      h('label', null, '제목'), t,
      h('div', { class: 'grid2' }, h('label', { class: 'f' }, h('span', null, '분야'), cat), h('label', { class: 'f' }, h('span', null, '종류'), kind)),
      h('label', null, '설명'), d, h('label', null, '검색어'), k,
      h('label', null, '벤더별 명령어'), vbox),
    (close) => [
      !isNew ? h('button', { type: 'button', class: 'danger', onclick: async () => {
        if (!(await O.confirm(`"${src.t}" 을(를) 지울까요?`, '지우기', true))) return;
        O.user.custom = O.user.custom.filter((c) => c.id !== src.id); O.saveUser(); close(); O.rerender();
      } }, '지우기') : null,
      h('span', { class: 'grow' }),
      h('button', { type: 'button', class: 'ghost', onclick: close }, '취소'),
      h('button', { type: 'button', class: 'primary', onclick: () => {
        if (!t.value.trim()) { O.toast('제목을 넣으세요', 'bad'); t.focus(); return; }
        const v = {};
        let any = false;
        for (const [vid, f] of Object.entries(vfields)) {
          const cmd = f.ta.value.replace(/\r/g, '').replace(/\s+$/g, '');
          if (cmd || f.note.value.trim()) v[vid] = { cmd: cmd || null, note: f.note.value.trim() };
          if (cmd) any = true;
        }
        if (!any) { O.toast('명령어를 하나 이상 넣으세요', 'bad'); return; }
        const now = new Date().toISOString();
        const item = { id: src.id, cat: cat.value, kind: kind.value, t: t.value.trim(), d: d.value.trim(), k: k.value.trim(), v, created: src.created || now, updated: now };
        const i = O.user.custom.findIndex((c) => c.id === src.id);
        if (i >= 0) O.user.custom[i] = item; else O.user.custom.push(item);
        O.saveUser(); close(); O.rerender(); O.toast('저장했습니다');
      } }, '저장'),
    ]);
  }

  function exportData() {
    const d = new Date();
    const stamp = d.getFullYear() + String(d.getMonth() + 1).padStart(2, '0') + String(d.getDate()).padStart(2, '0');
    O.download(`oicmd-내데이터-${stamp}.json`, JSON.stringify({ ...O.user, exported: d.toISOString(), product: 'OiCmd' }, null, 1), 'application/json');
  }
  function importData() {
    const f = h('input', { type: 'file', accept: '.json,application/json', class: 'offscreen' });
    f.addEventListener('change', async () => {
      const file = f.files[0];
      f.remove();
      if (!file) return;
      if (file.size > 4 << 20) return O.toast('파일이 너무 큽니다', 'bad');
      let d;
      try { d = JSON.parse(await file.text()); } catch (e) { return O.toast('OiCmd 내보내기 파일이 아닙니다', 'bad'); }
      if (!d || typeof d !== 'object' || d.product !== 'OiCmd') return O.toast('OiCmd 내보내기 파일이 아닙니다', 'bad');
      const cust = Array.isArray(d.custom) ? d.custom.filter((c) => c && typeof c === 'object' && typeof c.id === 'string' && typeof c.t === 'string') : [];
      const ov = d.overrides && typeof d.overrides === 'object' ? d.overrides : {};
      const ver = d.verified && typeof d.verified === 'object' ? d.verified : {};
      if (!(await O.confirm(`가져올 내용: 내 명령어 ${cust.length}개, 고친 기본 명령어 ${Object.keys(ov).length}개, 확인 표시 ${Object.keys(ver).length}개\n\n같은 것은 가져온 파일 것으로 바꾸고, 나머지는 그대로 둡니다.`, '가져오기'))) return;
      for (const c of cust) {
        const i = O.user.custom.findIndex((x) => x.id === c.id);
        if (i >= 0) O.user.custom[i] = c; else O.user.custom.push(c);
      }
      Object.assign(O.user.overrides, ov);
      Object.assign(O.user.verified, ver);
      await O.saveUser(true);
      O.toast('가져왔습니다');
      O.rerender();
    });
    document.body.append(f);
    f.click();
  }

  function minePage() {
    setTitle('내 명령어');
    toolsEl.append(
      h('button', { type: 'button', class: 'ghost sm', onclick: exportData, title: '내 명령어·고친 것·확인 표시·설정을 파일로' }, '내보내기'),
      h('button', { type: 'button', class: 'ghost sm', onclick: importData }, '가져오기'),
      h('button', { type: 'button', class: 'primary sm', onclick: () => editCustom(null) }, '+ 새 명령어'));
    const mine = O.entries().filter((e) => e.custom);
    main.append(h('p', { class: 'muted' }, '현장에서 자주 쓰는 명령어를 넣어 두면 사전·검색·변환에 같이 나옵니다. 이 PC 에 저장되고, 다른 PC 로는 [내보내기] 파일로 옮깁니다.'));
    if (!mine.length) main.append(h('div', { class: 'empty' }, '아직 넣은 명령어가 없습니다. 오른쪽 위 [+ 새 명령어]로 넣으세요.'));
    for (const e of mine) main.append(entryCard(e, { showCat: true }));

    const ovs = Object.entries(O.user.overrides);
    main.append(h('h2', { class: 'sec' }, '내가 고친 기본 명령어', h('span', { class: 'n' }, String(ovs.length))));
    if (!ovs.length) main.append(h('p', { class: 'muted small' }, '사전에서 명령어의 [고치기]로 바꾼 것이 여기 모입니다.'));
    else {
      const tb = h('table', { class: 't' }, h('thead', null, h('tr', null, ['항목', '벤더', '내 명령어', ''].map((x) => h('th', null, x)))));
      const body = h('tbody');
      for (const [key, x] of ovs) {
        const [id, vid] = key.split(':');
        const e = O.data.entries.find((y) => y.id === id);
        body.append(h('tr', null, h('td', null, e ? h('a', { href: '#/', onclick: (ev) => { ev.preventDefault(); dictState.q = e.t; dictState.cat = ''; location.hash = '#/'; O.rerender(); } }, e.t) : id),
          h('td', null, (O.vendorById[vid] || {}).name || vid), h('td', null, x.cmd ? O.cmdEl(x.cmd, 'small') : h('span', { class: 'muted' }, '(없음)')),
          h('td', null, h('button', { type: 'button', class: 'ghost sm', onclick: () => { delete O.user.overrides[key]; O.saveUser(); O.rerender(); } }, '원래대로'))));
      }
      tb.append(body);
      main.append(tb);
    }
    const nver = Object.keys(O.user.verified).length;
    const total = O.data.entries.reduce((n, e) => n + Object.values(e.v).filter((x) => x.cmd).length, 0);
    main.append(h('h2', { class: 'sec' }, '확인한 기본 명령어', h('span', { class: 'n' }, `${nver} / ${total}`)),
      h('p', { class: 'muted small' }, '실제 장비(또는 PNETLab)에서 쳐 보고 [미확인]을 눌러 [✓ 확인됨]으로 바꾼 개수입니다. 명령어가 바뀌면 다시 미확인이 됩니다.'));
  }

  // ---------------- 설정 ----------------
  function settingsPage() {
    setTitle('설정');
    const s = O.user.settings;

    // 포트 이름
    const ports = h('div', { class: 'ports-set' });
    for (const v of O.data.vendors) {
      const p = s.ports[v.id] || O.DEFAULT_PORTS[v.id];
      const pre = h('input', { type: 'text', class: 'mono', maxlength: 40, 'aria-label': v.name + ' 포트 이름 앞부분' }); pre.value = p.prefix;
      const base = h('select', { 'aria-label': v.name + ' 번호 시작' }, h('option', { value: '1' }, '1번 포트 = 1'), h('option', { value: '0' }, '1번 포트 = 0'));
      base.value = String(p.base);
      const ex = h('code', null);
      const upd = () => {
        s.ports[v.id] = { prefix: pre.value, base: +base.value };
        ex.textContent = `1번 → ${O.portName(1, v.id)}, 24번 → ${O.portName(24, v.id)}`;
        O.saveUser();
      };
      pre.addEventListener('input', upd); base.addEventListener('change', upd);
      upd();
      ports.append(h('div', { class: 'prow' }, h('b', null, v.name), pre, base, ex));
    }

    // 업데이트
    const upBox = h('div', { class: 'upd' });
    const auto = h('input', { type: 'checkbox', checked: s.autoUpdate });
    auto.addEventListener('change', () => { s.autoUpdate = auto.checked; O.saveUser(); });
    async function drawUpdate(st) {
      clear(upBox);
      if (!st) {
        try { st = await O.api('GET', '/api/update'); } catch (e) { upBox.append(h('p', { class: 'bad' }, e.message)); return; }
      }
      const a = st.available;
      upBox.append(h('p', null, '지금 버전: ', h('b', null, st.current || O.info.version),
        st.last_check ? h('span', { class: 'muted small' }, '  (마지막 확인 ' + new Date(st.last_check * 1000).toLocaleString('ko-KR') + ')') : null));
      if (st.error) upBox.append(h('p', { class: 'bad small' }, st.error));
      if (st.phase === 'download' || st.phase === 'launch') upBox.append(h('p', null, st.phase_msg || '진행 중…'));
      if (st.phase === 'done') upBox.append(h('p', { class: 'ok' }, st.phase_msg));
      if (st.phase === 'error') upBox.append(h('p', { class: 'bad small' }, st.phase_msg));
      if (a) {
        upBox.append(h('div', { class: 'newver' }, h('b', null, `새 버전 ${a.version}`), a.notes ? h('pre', { class: 'notes' }, a.notes) : null,
          st.installable ? h('button', { type: 'button', class: 'primary', onclick: async () => {
            try { await O.api('POST', '/api/update/install'); O.toast('받는 중… 끝나면 프로그램이 다시 열립니다'); poll(); } catch (e) { O.toast(e.message, 'bad'); }
          } }, '받아서 설치') : h('p', { class: 'muted small' }, st.plan_note || '')));
      } else if (st.last_check && !st.error) upBox.append(h('p', { class: 'ok' }, '최신 버전입니다'));
      const pkg = h('input', { type: 'file', accept: '.zip', class: 'offscreen' });
      pkg.addEventListener('change', async () => {
        const f = pkg.files[0];
        if (!f) return;
        try { const r = await O.api('POST', '/api/update/package', await f.arrayBuffer(), true); O.toast(`${r.version} 설치를 시작합니다`); poll(); }
        catch (e) { O.toast(e.message, 'bad'); }
      });
      upBox.append(h('div', { class: 'btns' },
        h('button', { type: 'button', class: 'ghost', onclick: async (ev) => {
          ev.target.disabled = true; ev.target.textContent = '확인 중…';
          try { drawUpdate(await O.api('POST', '/api/update/check')); } catch (e) { O.toast(e.message, 'bad'); drawUpdate(); }
        } }, '지금 확인'),
        h('button', { type: 'button', class: 'ghost', title: '인터넷이 안 되는 PC: 릴리즈의 OiCmd-update-버전.zip', onclick: () => pkg.click() }, '업데이트 파일로 설치'),
        h('button', { type: 'button', class: 'ghost', onclick: () => O.openExternal(st.page || 'https://github.com/Oiterm/OiCmd/releases/latest') }, '다운로드 페이지'),
        pkg));
    }
    let pollT;
    function poll() {
      clearTimeout(pollT);
      pollT = setTimeout(async () => {
        if (!document.body.contains(upBox)) return;
        try { const st = await O.api('GET', '/api/update'); drawUpdate(st); if (st.phase === 'download' || st.phase === 'launch') poll(); } catch (e) { /* 프로그램이 닫히는 중 */ }
      }, 1200);
    }
    drawUpdate();

    const docs = h('ul', { class: 'docs' }, O.data.vendors.map((v) => h('li', null, h('b', null, v.name + ' '), h('span', { class: 'muted small' }, v.os + ' '),
      h('button', { type: 'button', class: 'linkish', onclick: () => O.openExternal(v.doc) }, '공식 문서'))));

    main.append(
      h('section', { class: 'panel' }, h('h2', null, '포트 이름'),
        h('p', { class: 'muted small' }, '설정 만들기와 명령어 변환에서 앞판 포트 번호를 이 형식으로 바꿉니다. 스택 2번이면 시스코 GigabitEthernet2/0/, 얼라이드 port2.0. 처럼 바꾸세요.'),
        ports,
        h('button', { type: 'button', class: 'ghost sm', onclick: () => { s.ports = Object.assign({}, O.DEFAULT_PORTS); O.saveUser(); O.rerender(); } }, '기본값으로')),
      h('section', { class: 'panel' }, h('h2', null, '업데이트'),
        h('label', { class: 'chk' }, auto, '새 버전 자동 확인 (시작할 때, 하루 한 번)'), upBox),
      h('section', { class: 'panel' }, h('h2', null, '내 데이터'),
        h('p', null, '저장 위치: ', h('code', null, O.info.data_dir), h('span', { class: 'muted small' }, ' (user.json, 바로 전 내용은 user.json.bak)')),
        h('div', { class: 'btns' }, h('button', { type: 'button', class: 'ghost', onclick: exportData }, '내보내기'), h('button', { type: 'button', class: 'ghost', onclick: importData }, '가져오기'))),
      h('section', { class: 'panel' }, h('h2', null, '명령어 데이터에 대해'),
        h('p', null, `기본 명령어 ${O.data.entries.length}개 항목은 각 벤더 공식 문서를 기준으로 넣었지만, 장비 모델·OS 버전에 따라 다를 수 있습니다. 실제 장비나 랩에서 쳐 보고 [✓ 확인됨]으로 표시해 두세요. 틀린 것은 [고치기]로 바로잡으면 이 PC 에서는 내 것이 먼저 보입니다.`),
        docs),
      h('section', { class: 'panel' }, h('h2', null, '프로그램 정보'),
        h('p', null, `OiCmd ${O.info.version} — 네트워크 장비 명령어 사전 (시스코 · 주니퍼 · 얼라이드 · 알카텔)`),
        h('p', { class: 'small' }, h('a', { href: 'THIRD_PARTY_LICENSES.txt', target: '_blank', rel: 'noopener' }, '오픈소스 라이선스'), ' · ',
          h('button', { type: 'button', class: 'linkish', onclick: () => O.openExternal('https://github.com/Oiterm/OiCmd') }, 'GitHub'))));
  }

  start();
})();
