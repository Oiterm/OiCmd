'use strict';
// OiCmd 공통: DOM 만들기, 서버 API, 내 데이터(user.json) 읽기·저장, 복사, 알림.
// 화면에 넣는 글자는 모두 textContent 로만 넣는다 (사용자 명령어에 < > 가 많다).

const O = (window.O = {});

O.h = function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === 'class') el.className = v;
      else if (k === 'dataset') Object.assign(el.dataset, v);
      else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
      else if (k === 'value' || k === 'checked' || k === 'disabled' || k === 'selected' || k === 'hidden') el[k] = v;
      else el.setAttribute(k, v === true ? '' : String(v));
    }
  }
  O.add(el, kids);
  return el;
};
O.add = function (el, kids) {
  for (const k of [kids].flat(Infinity)) {
    if (k == null || k === false || k === '') continue;
    el.append(k instanceof Node ? k : document.createTextNode(String(k)));
  }
  return el;
};
O.clear = (el) => { while (el.firstChild) el.removeChild(el.firstChild); return el; };
const h = O.h;

// ---------------- 서버 ----------------
O.token = '';
(function takeToken() {
  const m = location.hash.match(/(?:^#|&)t=([0-9a-f]{20,})/);
  if (m) {
    O.token = m[1];
    try { sessionStorage.setItem('oicmd.t', O.token); } catch (e) { /* 이번만 */ }
    history.replaceState(null, '', location.pathname + '#/');
  } else {
    try { O.token = sessionStorage.getItem('oicmd.t') || ''; } catch (e) { O.token = ''; }
  }
})();

O.api = async function (method, path, body, raw) {
  const headers = { 'X-OiCmd-Token': O.token };
  let payload;
  if (raw) { payload = body; headers['Content-Type'] = 'application/octet-stream'; }
  else if (body !== undefined) { payload = JSON.stringify(body); headers['Content-Type'] = 'application/json'; }
  let res;
  try {
    res = await fetch(path, { method, headers, body: payload, cache: 'no-store' });
  } catch (e) {
    throw new Error('OiCmd 프로그램에 연결할 수 없습니다. 프로그램이 닫혔으면 다시 실행하세요');
  }
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (e) { data = null; }
  if (!res.ok) throw new Error((data && data.error) || ('오류 ' + res.status));
  return data;
};

// ---------------- 내 데이터 ----------------
// { v, settings:{vendors, autoUpdate, ports}, verified:{'id:v':{at,h}}, overrides:{'id:v':{cmd,note}}, custom:[...], gen:{...} }
O.user = null;
O.DEFAULT_PORTS = {
  c: { prefix: 'GigabitEthernet1/0/', base: 1 },
  j: { prefix: 'ge-0/0/', base: 0 },
  a: { prefix: 'port1.0.', base: 1 },
  o6: { prefix: '1/', base: 1 },
  o8: { prefix: '1/1/', base: 1 },
};
O.loadUser = async function () {
  const u = (await O.api('GET', '/api/user')) || {};
  if (u._warning) { O.toast(u._warning, 'warn'); delete u._warning; }
  u.v = 1;
  u.settings = u.settings && typeof u.settings === 'object' ? u.settings : {};
  if (!Array.isArray(u.settings.vendors)) u.settings.vendors = null; // null = 전부
  if (typeof u.settings.autoUpdate !== 'boolean') u.settings.autoUpdate = true;
  u.settings.ports = Object.assign({}, O.DEFAULT_PORTS, u.settings.ports || {});
  u.verified = u.verified && typeof u.verified === 'object' ? u.verified : {};
  u.overrides = u.overrides && typeof u.overrides === 'object' ? u.overrides : {};
  u.custom = Array.isArray(u.custom) ? u.custom : [];
  u.gen = u.gen && typeof u.gen === 'object' ? u.gen : null;
  O.user = u;
  return u;
};
let saveTimer = null, savePromise = null;
O.saveUser = function (now) {
  clearTimeout(saveTimer);
  const doSave = () => {
    savePromise = O.api('PUT', '/api/user', O.user).catch((e) => O.toast('저장하지 못했습니다: ' + e.message, 'bad'));
    return savePromise;
  };
  if (now) return doSave();
  saveTimer = setTimeout(doSave, 400);
  return Promise.resolve();
};
window.addEventListener('beforeunload', () => { if (saveTimer) { clearTimeout(saveTimer); O.api('PUT', '/api/user', O.user).catch(() => {}); } });

// ---------------- 명령어 데이터 ----------------
O.data = null; // commands.json
O.loadData = async function () {
  const res = await fetch('commands.json', { cache: 'no-store' });
  O.data = await res.json();
  O.vendorById = Object.fromEntries(O.data.vendors.map((v) => [v.id, v]));
  O.catById = Object.fromEntries(O.data.cats.map((c) => [c.id, c]));
};
O.visibleVendors = function () {
  const all = O.data.vendors.map((v) => v.id);
  const sel = O.user.settings.vendors;
  if (!sel) return all;
  const s = all.filter((id) => sel.includes(id));
  return s.length ? s : all;
};

// 기본 명령어 + 내가 고친 것 + 내 명령어를 합친 목록
O.entries = function () {
  const out = [];
  for (const e of O.data.entries) {
    const v = {};
    for (const [vid, x] of Object.entries(e.v)) {
      const ov = O.user.overrides[e.id + ':' + vid];
      v[vid] = ov ? { cmd: ov.cmd || null, note: ov.note || '', mine: true, orig: x } : { cmd: x.cmd, note: x.note || '' };
    }
    out.push({ ...e, v, builtin: true });
  }
  for (const c of O.user.custom) {
    const v = {};
    for (const vd of O.data.vendors) {
      const x = (c.v && c.v[vd.id]) || {};
      v[vd.id] = { cmd: x.cmd || null, note: x.note || '' };
    }
    out.push({ id: c.id, cat: c.cat || 'misc', kind: c.kind || 'show', t: c.t || '(제목 없음)', d: c.d || '', k: c.k || '', v, custom: true });
  }
  return out;
};

// 확인 표시: 명령어 글자가 바뀌면(데이터 업데이트·내가 고침) 다시 '미확인'
O.hash = function (s) {
  let x = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 0x01000193) >>> 0; }
  return x.toString(36);
};
O.isVerified = function (entryId, vid, cmd) {
  const m = O.user.verified[entryId + ':' + vid];
  return !!(m && cmd && m.h === O.hash(cmd));
};
O.setVerified = function (entryId, vid, cmd, on) {
  const k = entryId + ':' + vid;
  if (on && cmd) O.user.verified[k] = { at: new Date().toISOString().slice(0, 10), h: O.hash(cmd) };
  else delete O.user.verified[k];
  O.saveUser();
};

// ---------------- 복사·알림·기타 ----------------
O.copy = async function (text) {
  try {
    await navigator.clipboard.writeText(text);
  } catch (e) {
    const ta = h('textarea', { class: 'offscreen', 'aria-hidden': 'true' });
    ta.value = text;
    document.body.append(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (x) { /* 없음 */ }
    ta.remove();
  }
  O.toast('복사했습니다');
};

let toastBox = null;
O.toast = function (msg, kind) {
  if (!toastBox) { toastBox = h('div', { class: 'toasts', role: 'status', 'aria-live': 'polite' }); document.body.append(toastBox); }
  const t = h('div', { class: 'toast ' + (kind || '') }, msg);
  toastBox.append(t);
  setTimeout(() => t.classList.add('out'), kind === 'bad' ? 5000 : 1800);
  setTimeout(() => t.remove(), kind === 'bad' ? 5400 : 2200);
};

O.download = function (name, text, type) {
  const blob = new Blob([text], { type: type || 'text/plain;charset=utf-8' });
  const a = h('a', { href: URL.createObjectURL(blob), download: name });
  document.body.append(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
};

O.openExternal = async function (url) {
  try {
    const info = O.info || {};
    if (info.can_open) { await O.api('POST', '/api/open', { url }); return; }
  } catch (e) { O.toast(e.message, 'bad'); return; }
  window.open(url, '_blank', 'noopener');
};

O.uid = () => 'u-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 7);

O.kindLabel = { show: '조회', exec: '실행', config: '설정 모드' };

// 명령어 글자에서 <자리> 를 강조해서 그린다 (textContent 만 씀)
O.cmdEl = function (cmd, cls) {
  const pre = h('pre', { class: 'cmd ' + (cls || '') });
  const re = /<[^<>\n]{1,24}>/g;
  let last = 0, m;
  while ((m = re.exec(cmd))) {
    if (m.index > last) pre.append(document.createTextNode(cmd.slice(last, m.index)));
    pre.append(h('span', { class: 'ph' }, m[0]));
    last = m.index + m[0].length;
  }
  if (last < cmd.length) pre.append(document.createTextNode(cmd.slice(last)));
  return pre;
};

// 모달 창
O.modal = function (title, body, actions) {
  const back = h('div', { class: 'modal-back', role: 'presentation' });
  const close = () => { back.remove(); document.removeEventListener('keydown', onKey); };
  const onKey = (e) => { if (e.key === 'Escape') close(); };
  const box = h('div', { class: 'modal', role: 'dialog', 'aria-modal': 'true', 'aria-label': title },
    h('div', { class: 'modal-h' }, h('h2', null, title), h('button', { class: 'ghost icon-btn', type: 'button', 'aria-label': '닫기', onclick: close }, '✕')),
    h('div', { class: 'modal-b' }, body),
    actions ? h('div', { class: 'modal-f' }, actions(close)) : null);
  back.append(box);
  back.addEventListener('mousedown', (e) => { if (e.target === back) close(); });
  document.addEventListener('keydown', onKey);
  document.body.append(back);
  const f = box.querySelector('input, textarea, select');
  if (f) setTimeout(() => f.focus(), 30);
  return close;
};

O.confirm = function (msg, okLabel, danger) {
  return new Promise((resolve) => {
    O.modal('확인', h('p', { class: 'pre-line' }, msg), (close) => [
      h('button', { type: 'button', class: 'ghost', onclick: () => { close(); resolve(false); } }, '취소'),
      h('button', { type: 'button', class: danger ? 'danger' : 'primary', onclick: () => { close(); resolve(true); } }, okLabel || '확인'),
    ]);
  });
};
