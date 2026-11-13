// 화면 JS(명령어 맞추기·값 바꾸기·설정 만들기) 시험. 저장소 맨 위에서: node tools/jstest/run.js
'use strict';
const fs = require('fs');
const path = require('path');
const assert = require('assert');
global.window = global;
global.location = { hash: '', pathname: '/' };
global.history = { replaceState() {} };
global.sessionStorage = { getItem() { return ''; }, setItem() {} };
global.document = { addEventListener() {}, createElement() { return {}; } };
global.addEventListener = () => {};
const ui = path.join(__dirname, '..', '..', 'internal', 'server', 'ui');
for (const f of ['core.js', 'match.js', 'gen.js']) (0, eval)(fs.readFileSync(path.join(ui, 'js', f), 'utf8'));
const O = global.O;
O.data = JSON.parse(fs.readFileSync(path.join(ui, 'commands.json'), 'utf8'));
O.vendorById = Object.fromEntries(O.data.vendors.map((v) => [v.id, v]));
O.user = { settings: { ports: O.DEFAULT_PORTS }, overrides: {}, custom: [], verified: {} };

let n = 0;
function t(name, fn) { fn(); n++; }
const top = (s, src) => O.matchText(s, src)[0];
const fill = (r, vid) => O.fillCommand(r.entry.v[vid].cmd, r.caps, r.vendor, vid).text;

t('줄임말', () => {
  assert.strictEqual(top('sh int status').entry.id, 'intf-status');
  assert.strictEqual(top('sh run').entry.id, 'show-run');
  assert.strictEqual(top('Switch# sh ip int br').entry.id, 'ip-brief');
  assert.strictEqual(top('conf t').entry.id, 'enter-config');
  assert.strictEqual(top('wr').entry.id, 'save');
});
t('다른 벤더 명령으로', () => {
  const r = top('show ethernet-switching table');
  assert.strictEqual(r.entry.id, 'mac-table');
  assert.strictEqual(r.vendor, 'j');
  assert.strictEqual(fill(r, 'o8'), 'show mac-learning');
});
t('포트 번호 바꾸기', () => {
  const r = top('interface gi1/0/5\nswitchport access vlan 10');
  assert.strictEqual(r.entry.id, 'vlan-access');
  assert.ok(fill(r, 'j').startsWith('set interfaces ge-0/0/4 '));
  assert.strictEqual(fill(r, 'o6'), 'vlan 10 port default 1/5');
  assert.strictEqual(fill(r, 'o8'), 'vlan 10 members port 1/1/5 untagged');
  assert.ok(fill(r, 'a').startsWith('interface port1.0.5'));
  const j = top('show interfaces ge-0/0/4 extensive');
  assert.strictEqual(fill(j, 'c'), 'show interfaces GigabitEthernet1/0/5');
});
t('MAC 형식', () => {
  const r = top('show mac address-table address 0011.2233.4455');
  assert.strictEqual(r.entry.id, 'mac-find');
  assert.strictEqual(fill(r, 'o8'), 'show mac-learning mac-address 00:11:22:33:44:55');
});
t('마스크 ↔ 프리픽스', () => {
  const r = top('ip address 10.0.10.2 255.255.255.0');
  assert.ok(fill(r, 'a').includes('ip address 10.0.10.2/24'));
});
t('자리 표시만 있는 줄은 맞추지 않음', () => {
  const r = O.matchText('sh int status');
  assert.ok(!r.some((x) => x.entry.id === 'banner'));
});
t('설정 만들기', () => {
  const g = { hostname: 'SW1', vlans: [{ id: '10', name: 'OFFICE' }], ports: [{ ports: '1-4', mode: 'access', vlan: '10' }, { ports: '24', mode: 'trunk', allowed: '10' }],
    lags: [{ id: '1', ports: '25-26', allowed: '10' }], mgmtVlan: '10', mgmtIp: '10.0.10.2/24', gateway: '10.0.10.1' };
  const c = O.generate(g, 'c');
  assert.deepStrictEqual(c.errors, []);
  assert.ok(c.text.includes('interface range GigabitEthernet1/0/1 - 4'));
  assert.ok(c.text.includes('ip address 10.0.10.2 255.255.255.0'));
  assert.ok(O.generate(g, 'j').text.includes('member-range ge-0/0/0 to ge-0/0/3'));
  assert.ok(O.generate(g, 'a').text.includes('interface port1.0.1-1.0.4'));
  assert.ok(O.generate(g, 'o6').text.includes('vlan 10 port default 1/1-4'));
  assert.ok(O.generate(g, 'o8').text.includes('vlan 10 members port 1/1/1-4 untagged'));
  assert.ok(O.generate(g, 'o8').text.includes('linkagg lacp agg 1 size 2 actor admin-key 1'));
  const bad = O.generate({ vlans: [{ id: '5000' }], ports: [{ ports: '1-3', mode: 'access', vlan: '10' }, { ports: '3', mode: 'trunk', allowed: '10' }] }, 'c');
  assert.ok(bad.errors.length >= 2);
});
console.log(`JS 시험 ${n}개 통과`);
