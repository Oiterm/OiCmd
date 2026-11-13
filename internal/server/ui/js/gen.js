'use strict';
// 설정 만들기: 입력한 VLAN·포트·LACP·관리 IP 등으로 벤더별 설정문을 만든다.
// 출력에는 주석을 넣지 않는다 (AOS 는 주석 줄을 명령으로 받아 에러가 남). 주의할 점은 notes 로 따로 돌려준다.

(function () {
  // "1-4,8, 10-12" → [1,2,3,4,8,10,11,12]
  O.parseList = function (s, max) {
    const out = new Set();
    for (const part of String(s || '').split(/[,\s]+/).filter(Boolean)) {
      const m = part.match(/^(\d+)(?:-(\d+))?$/);
      if (!m) throw new Error(`"${part}" 를 알아볼 수 없습니다 (예: 1-4,8)`);
      const a = +m[1], b = m[2] ? +m[2] : a;
      if (a < 1 || b < a || b > (max || 4094)) throw new Error(`"${part}" 범위가 잘못됐습니다`);
      if (b - a > 4094) throw new Error('범위가 너무 큽니다');
      for (let i = a; i <= b; i++) out.add(i);
    }
    return [...out].sort((x, y) => x - y);
  };
  // [1,2,3,5] → [[1,3],[5,5]]
  function runs(list) {
    const r = [];
    for (const n of list) {
      const last = r[r.length - 1];
      if (last && n === last[1] + 1) last[1] = n; else r.push([n, n]);
    }
    return r;
  }
  const listStr = (list) => runs(list).map(([a, b]) => (a === b ? String(a) : a + '-' + b)).join(',');

  function port(vid, n) { return O.portName(n, vid); }
  function portIdx(vid, n) { const p = O.user.settings.ports[vid]; return n - 1 + p.base; }

  // 벤더별 포트 범위 이름
  function cRange(r) { // 시스코 interface range
    return r.map(([a, b]) => (a === b ? port('c', a) : `${port('c', a)} - ${portIdx('c', b)}`)).join(' , ');
  }
  function aRange(r) { // AW+ port1.0.1-1.0.4,port1.0.8
    return r.map(([a, b]) => (a === b ? port('a', a) : `${port('a', a)}-${port('a', b).replace(/^port/i, '')}`)).join(',');
  }
  function aosRange(vid, [a, b]) { return a === b ? port(vid, a) : `${port(vid, a)}-${portIdx(vid, b)}`; }

  function ipMask(s) {
    const m = String(s || '').trim().match(/^(\d{1,3}(?:\.\d{1,3}){3})(?:\/(\d{1,2})|\s+(\d{1,3}(?:\.\d{1,3}){3}))?$/);
    if (!m) return null;
    if (m[1].split('.').some((x) => +x > 255)) return null;
    let prefix = m[2] || (m[3] ? O.maskToPrefix(m[3]) : null);
    if (prefix == null) return null;
    const mask = O.prefixToMask(prefix);
    if (!mask) return null;
    return { ip: m[1], prefix: String(prefix), mask };
  }
  O.ipMask = ipMask;
  const isIP = (s) => /^\d{1,3}(\.\d{1,3}){3}$/.test(String(s || '').trim()) && s.split('.').every((x) => +x <= 255);

  const junosName = (v) => (v.name || 'VLAN' + v.id).replace(/[^A-Za-z0-9_.-]/g, '_').slice(0, 63) || 'VLAN' + v.id;
  const quote = (s) => String(s || '').replace(/"/g, "'");

  // 입력 검사 + 정리. 문제가 있으면 errors 에 넣는다.
  O.genModel = function (g) {
    const errors = [];
    const vlans = [];
    const seen = new Set();
    for (const v of g.vlans || []) {
      if (!String(v.id || '').trim()) continue;
      const id = +v.id;
      if (!(id >= 1 && id <= 4094)) { errors.push(`VLAN 번호 ${v.id}: 1~4094 사이여야 합니다`); continue; }
      if (seen.has(id)) { errors.push(`VLAN ${id}: 두 번 들어 있습니다`); continue; }
      seen.add(id);
      vlans.push({ id, name: String(v.name || '').trim().slice(0, 32) });
    }
    const vName = (id) => (vlans.find((v) => v.id === id) || { id, name: '' });
    const groups = [];
    const used = new Map();
    const usePorts = (list, what) => {
      for (const n of list) {
        if (used.has(n)) errors.push(`${n}번 포트가 두 곳(${used.get(n)}, ${what})에 들어 있습니다`);
        else used.set(n, what);
      }
    };
    (g.ports || []).forEach((p, i) => {
      if (!String(p.ports || '').trim()) return;
      let list;
      try { list = O.parseList(p.ports, 512); } catch (e) { errors.push(`포트 ${i + 1}번째 줄: ${e.message}`); return; }
      const mode = p.mode === 'trunk' ? 'trunk' : 'access';
      const what = `포트 ${i + 1}번째 줄`;
      usePorts(list, what);
      if (mode === 'access') {
        const vid = +p.vlan;
        if (!(vid >= 1 && vid <= 4094)) { errors.push(`${what}: VLAN 을 넣으세요`); return; }
        if (!seen.has(vid) && vid !== 1) errors.push(`${what}: VLAN ${vid} 을(를) 위 VLAN 목록에도 넣으세요`);
        groups.push({ mode, list, vlan: vid, desc: String(p.desc || '').trim().slice(0, 60) });
      } else {
        let allowed;
        try { allowed = O.parseList(p.allowed); } catch (e) { errors.push(`${what} 허용 VLAN: ${e.message}`); return; }
        if (!allowed.length) { errors.push(`${what}: 허용할 VLAN 을 넣으세요`); return; }
        for (const a of allowed) if (!seen.has(a) && a !== 1) errors.push(`${what}: VLAN ${a} 을(를) 위 VLAN 목록에도 넣으세요`);
        const native = String(p.native || '').trim() ? +p.native : null;
        if (native != null && !(native >= 1 && native <= 4094)) errors.push(`${what}: native VLAN 이 잘못됐습니다`);
        groups.push({ mode, list, allowed, native, desc: String(p.desc || '').trim().slice(0, 60) });
      }
    });
    const lags = [];
    (g.lags || []).forEach((l, i) => {
      if (!String(l.ports || '').trim()) return;
      const what = `LACP ${i + 1}번째 줄`;
      const id = +l.id;
      if (!(id >= 1 && id <= 64)) { errors.push(`${what}: 묶음 번호는 1~64`); return; }
      if (lags.some((x) => x.id === id)) { errors.push(`${what}: 묶음 번호 ${id} 이(가) 겹칩니다`); return; }
      let list;
      try { list = O.parseList(l.ports, 512); } catch (e) { errors.push(`${what}: ${e.message}`); return; }
      if (list.length < 2) { errors.push(`${what}: 포트를 2개 이상 넣으세요`); return; }
      if (list.length > 8) { errors.push(`${what}: 8개까지만 묶을 수 있게 했습니다`); return; }
      usePorts(list, what);
      let allowed;
      try { allowed = O.parseList(l.allowed); } catch (e) { errors.push(`${what} 허용 VLAN: ${e.message}`); return; }
      if (!allowed.length) { errors.push(`${what}: 허용할 VLAN 을 넣으세요`); return; }
      lags.push({ id, list, allowed, desc: String(l.desc || '').trim().slice(0, 60) });
    });
    let svi = null;
    if (String(g.mgmtVlan || '').trim() || String(g.mgmtIp || '').trim()) {
      const vid = +g.mgmtVlan;
      const im = ipMask(g.mgmtIp);
      if (!(vid >= 1 && vid <= 4094)) errors.push('관리 VLAN 번호를 넣으세요');
      else if (!im) errors.push('관리 IP 는 10.0.10.2/24 또는 10.0.10.2 255.255.255.0 처럼 넣으세요');
      else {
        if (!seen.has(vid) && vid !== 1) errors.push(`관리 VLAN ${vid} 을(를) 위 VLAN 목록에도 넣으세요`);
        svi = { vlan: vid, ...im };
      }
    }
    const gw = String(g.gateway || '').trim();
    if (gw && !isIP(gw)) errors.push('게이트웨이 IP 가 잘못됐습니다');
    for (const [k, label] of [['ntp', 'NTP 서버'], ['syslog', '로그 서버']]) {
      const v = String(g[k] || '').trim();
      if (v && !isIP(v)) errors.push(label + ' IP 가 잘못됐습니다');
    }
    const host = String(g.hostname || '').trim();
    if (host && !/^[A-Za-z][A-Za-z0-9_-]{0,62}$/.test(host)) errors.push('장비 이름은 영문으로 시작하고 영문·숫자·-·_ 만 (63자까지)');
    const community = String(g.community || '').trim();
    if (community && !/^[A-Za-z0-9_.@-]{1,32}$/.test(community)) errors.push('SNMP 커뮤니티는 영문·숫자·_.@- 만 (32자까지)');
    if (community && /^(public|private)$/i.test(community)) errors.push('SNMP 커뮤니티로 public/private 는 쓰지 마세요 (보안 점검에서 걸립니다)');
    return { errors, vlans, vName, groups, lags, svi, gw, ntp: String(g.ntp || '').trim(), syslog: String(g.syslog || '').trim(),
      host, community, ssh: !!g.ssh, user: String(g.user || '').trim(), l3: !!g.l3, tz: !!g.tz };
  };

  // ---------------- 벤더별 ----------------
  const GEN = {};

  GEN.c = function (m) {
    const L = [], notes = [];
    L.push('configure terminal');
    if (m.host) L.push('hostname ' + m.host);
    if (m.tz) L.push('clock timezone KST 9 0');
    for (const v of m.vlans) { L.push('vlan ' + v.id); if (v.name) L.push(' name ' + v.name); L.push(' exit'); }
    for (const g of m.groups) {
      const r = runs(g.list);
      L.push((r.length === 1 && r[0][0] === r[0][1] ? 'interface ' : 'interface range ') + cRange(r));
      if (g.desc) L.push(' description ' + g.desc);
      if (g.mode === 'access') {
        L.push(' switchport mode access', ' switchport access vlan ' + g.vlan, ' spanning-tree portfast');
      } else {
        L.push(' switchport mode trunk', ' switchport trunk allowed vlan ' + listStr(g.allowed));
        if (g.native) L.push(' switchport trunk native vlan ' + g.native);
      }
      L.push(' no shutdown', ' exit');
    }
    for (const l of m.lags) {
      const r = runs(l.list);
      L.push('interface range ' + cRange(r));
      if (l.desc) L.push(' description ' + l.desc);
      L.push(' channel-group ' + l.id + ' mode active', ' no shutdown', ' exit');
      L.push('interface Port-channel' + l.id);
      if (l.desc) L.push(' description ' + l.desc);
      L.push(' switchport mode trunk', ' switchport trunk allowed vlan ' + listStr(l.allowed), ' exit');
    }
    if (m.svi) L.push('interface Vlan' + m.svi.vlan, ' ip address ' + m.svi.ip + ' ' + m.svi.mask, ' no shutdown', ' exit');
    if (m.l3) L.push('ip routing');
    if (m.gw) L.push(m.l3 ? 'ip route 0.0.0.0 0.0.0.0 ' + m.gw : 'ip default-gateway ' + m.gw);
    if (m.ntp) L.push('ntp server ' + m.ntp);
    if (m.syslog) L.push('logging host ' + m.syslog);
    if (m.community) L.push('snmp-server community ' + m.community + ' RO');
    if (m.ssh) {
      const u = m.user || 'admin';
      L.push('username ' + u + ' privilege 15 secret <비밀번호>', 'ip domain-name local', 'crypto key generate rsa modulus 2048', 'ip ssh version 2',
        'line vty 0 15', ' login local', ' transport input ssh', ' exit');
      notes.push('<비밀번호> 를 실제 비밀번호로 바꾼 뒤 넣으세요.');
    }
    L.push('end', 'write memory');
    notes.push('예전 장비(3750 등)는 트렁크 앞에 switchport trunk encapsulation dot1q 가 필요할 수 있습니다.');
    if (m.lags.length) notes.push('LACP 는 상대 장비도 같은 포트 수로 active(또는 passive) 로 맞춰야 올라옵니다.');
    return { text: L.join('\n'), notes };
  };

  GEN.j = function (m) {
    const L = [], notes = [];
    const set = (s) => L.push('set ' + s);
    if (m.host) set('system host-name ' + m.host);
    if (m.tz) set('system time-zone Asia/Seoul');
    for (const v of m.vlans) set(`vlans ${junosName(v)} vlan-id ${v.id}`);
    const nm = (id) => junosName(m.vName(id));
    const members = (list) => (list.length === 1 ? nm(list[0]) : '[ ' + list.map(nm).join(' ') + ' ]');
    // 포트가 여럿이면 interface-range 로 묶는다 (포트마다 줄을 쓰지 않게)
    const rangeNames = new Set();
    m.groups.forEach((g, gi) => {
      let target;
      if (g.list.length === 1) target = port('j', g.list[0]);
      else {
        let base = (g.desc || '').toUpperCase().replace(/[^A-Z0-9_-]/g, '_').replace(/^[^A-Z]+/, '').slice(0, 24) || 'RANGE';
        let name = base, k = 2;
        while (rangeNames.has(name)) name = base + '-' + k++;
        rangeNames.add(name);
        target = 'interface-range ' + name;
        for (const [a, b] of runs(g.list)) {
          if (a === b) set(`interfaces ${target} member ${port('j', a)}`);
          else set(`interfaces ${target} member-range ${port('j', a)} to ${port('j', b)}`);
        }
      }
      if (g.desc) set(`interfaces ${target} description "${quote(g.desc)}"`);
      if (g.mode === 'access') {
        set(`interfaces ${target} unit 0 family ethernet-switching interface-mode access vlan members ${nm(g.vlan)}`);
      } else {
        set(`interfaces ${target} unit 0 family ethernet-switching interface-mode trunk vlan members ${members(g.allowed)}`);
        if (g.native) set(`interfaces ${target} native-vlan-id ${g.native}`);
      }
    });
    if (m.lags.length) {
      set('chassis aggregated-devices ethernet device-count ' + (Math.max(...m.lags.map((l) => l.id)) + 1));
      for (const l of m.lags) {
        for (const n of l.list) set(`interfaces ${port('j', n)} ether-options 802.3ad ae${l.id}`);
        if (l.desc) set(`interfaces ae${l.id} description "${quote(l.desc)}"`);
        set(`interfaces ae${l.id} aggregated-ether-options lacp active`);
        set(`interfaces ae${l.id} unit 0 family ethernet-switching interface-mode trunk vlan members ${members(l.allowed)}`);
      }
    }
    if (m.svi) {
      set(`interfaces irb unit ${m.svi.vlan} family inet address ${m.svi.ip}/${m.svi.prefix}`);
      set(`vlans ${nm(m.svi.vlan)} l3-interface irb.${m.svi.vlan}`);
      if (!m.vlans.find((v) => v.id === m.svi.vlan)) notes.push(`관리 VLAN ${m.svi.vlan} 가 VLAN 목록에 없어서 이름을 ${nm(m.svi.vlan)} 로 가정했습니다.`);
    }
    if (m.gw) set('routing-options static route 0.0.0.0/0 next-hop ' + m.gw);
    if (m.ntp) set('system ntp server ' + m.ntp);
    if (m.syslog) set('system syslog host ' + m.syslog + ' any any');
    if (m.community) set('snmp community ' + m.community + ' authorization read-only');
    if (m.ssh) {
      set('system services ssh');
      set(`system login user ${m.user || 'admin'} class super-user authentication plain-text-password`);
      notes.push('plain-text-password 줄은 붙여 넣으면 비밀번호를 두 번 묻습니다. 그 줄은 따로 치세요.');
    }
    notes.push('configure 로 들어가서 붙여 넣고, show | compare 로 확인한 뒤 commit check → commit 하세요.');
    notes.push('주니퍼 포트 번호는 0부터라 앞판 1번 = ' + port('j', 1) + ' 입니다 (설정에서 바꿀 수 있음).');
    if (m.groups.length || m.lags.length) notes.push('공장 설정 포트에 vlan members default 가 있으면 먼저 지우세요 (delete interfaces <포트> unit 0 family ethernet-switching vlan).');
    return { text: L.join('\n'), notes };
  };

  GEN.a = function (m) {
    const L = [], notes = [];
    L.push('configure terminal');
    if (m.host) L.push('hostname ' + m.host);
    if (m.tz) L.push('clock timezone KST plus 9');
    if (m.vlans.length) {
      L.push('vlan database');
      for (const v of m.vlans) L.push(' vlan ' + v.id + (v.name ? ' name ' + v.name : ''));
      L.push(' exit');
    }
    for (const g of m.groups) {
      L.push('interface ' + aRange(runs(g.list)));
      if (g.desc) L.push(' description ' + g.desc);
      if (g.mode === 'access') {
        L.push(' switchport mode access', ' switchport access vlan ' + g.vlan, ' spanning-tree edgeport');
      } else {
        L.push(' switchport mode trunk', ' switchport trunk allowed vlan add ' + listStr(g.allowed));
        if (g.native) L.push(' switchport trunk native vlan ' + g.native);
      }
      L.push(' no shutdown', ' exit');
    }
    for (const l of m.lags) {
      L.push('interface ' + aRange(runs(l.list)));
      if (l.desc) L.push(' description ' + l.desc);
      L.push(' channel-group ' + l.id + ' mode active', ' exit');
      L.push('interface po' + l.id);
      if (l.desc) L.push(' description ' + l.desc);
      L.push(' switchport mode trunk', ' switchport trunk allowed vlan add ' + listStr(l.allowed), ' exit');
    }
    if (m.svi) L.push('interface vlan' + m.svi.vlan, ' ip address ' + m.svi.ip + '/' + m.svi.prefix, ' exit');
    if (m.gw) L.push('ip route 0.0.0.0/0 ' + m.gw);
    if (m.ntp) L.push('ntp server ' + m.ntp);
    if (m.syslog) L.push('log host ' + m.syslog);
    if (m.community) L.push('snmp-server community ' + m.community + ' ro');
    if (m.ssh) {
      L.push('username ' + (m.user || 'admin') + ' privilege 15 password <비밀번호>', 'crypto key generate hostkey rsa 2048', 'service ssh');
      notes.push('<비밀번호> 를 실제 비밀번호로 바꾼 뒤 넣으세요. 이미 호스트 키가 있으면 바꿀지 묻습니다.');
    }
    L.push('end', 'write');
    return { text: L.join('\n'), notes };
  };

  function sizeOf(n) { return [2, 4, 8, 16].find((x) => x >= n) || 16; }

  GEN.o6 = function (m) {
    const L = [], notes = [O.data.aosConfigNote];
    if (m.host) L.push('system name "' + quote(m.host) + '"');
    for (const v of m.vlans) L.push('vlan ' + v.id + (v.name ? ' name "' + quote(v.name) + '"' : ''));
    for (const g of m.groups) {
      const r = runs(g.list);
      if (g.desc) for (const n of g.list) L.push('interfaces ' + port('o6', n) + ' alias "' + quote(g.desc) + '"');
      if (g.mode === 'access') {
        for (const x of r) L.push('vlan ' + g.vlan + ' port default ' + aosRange('o6', x));
      } else {
        if (g.native) for (const x of r) L.push('vlan ' + g.native + ' port default ' + aosRange('o6', x));
        for (const a of g.allowed) {
          if (a === g.native) continue;
          for (const n of g.list) L.push('vlan ' + a + ' 802.1q ' + port('o6', n));
        }
      }
    }
    for (const l of m.lags) {
      L.push(`lacp linkagg ${l.id} size ${sizeOf(l.list.length)} actor admin key ${l.id}`);
      for (const n of l.list) L.push(`lacp agg ${port('o6', n)} actor admin key ${l.id}`);
      for (const a of l.allowed) L.push(`vlan ${a} 802.1q ${l.id}`);
    }
    if (m.lags.length) notes.push('linkagg 크기(size)는 2/4/8 중 포트 수 이상으로 넣었습니다. VLAN 줄의 숫자(vlan 10 802.1q 1)는 묶음 번호입니다.');
    if (m.svi) L.push(`ip interface "vlan${m.svi.vlan}" address ${m.svi.ip} mask ${m.svi.mask} vlan ${m.svi.vlan}`);
    if (m.gw) L.push('ip static-route 0.0.0.0 mask 0.0.0.0 gateway ' + m.gw);
    if (m.ntp) L.push('ntp server ' + m.ntp, 'ntp client enable');
    if (m.syslog) L.push('swlog output socket ' + m.syslog);
    if (m.tz) { L.push('system timezone KST'); notes.push('system timezone 이름은 버전마다 목록이 달라 장비에서 확인하세요.'); }
    if (m.community) notes.push('SNMP 는 AOS 에서 사용자 계정과 커뮤니티를 연결하는 방식이라 자동으로 만들지 않았습니다. 명령어 사전의 "SNMP 읽기 커뮤니티"를 보세요.');
    if (m.ssh) {
      L.push(`user ${m.user || 'admin'} password <비밀번호> read-write all`, 'aaa authentication ssh local');
      notes.push('<비밀번호> 를 실제 비밀번호로 바꾼 뒤 넣으세요.');
    }
    L.push('write memory', 'copy working certified');
    return { text: L.join('\n'), notes };
  };

  GEN.o8 = function (m) {
    const L = [], notes = [O.data.aosConfigNote];
    if (m.host) L.push('system name "' + quote(m.host) + '"');
    for (const v of m.vlans) L.push('vlan ' + v.id + ' admin-state enable' + (v.name ? ' name "' + quote(v.name) + '"' : ''));
    for (const g of m.groups) {
      const r = runs(g.list);
      if (g.desc) for (const n of g.list) L.push('interfaces port ' + port('o8', n) + ' alias "' + quote(g.desc) + '"');
      if (g.mode === 'access') {
        for (const x of r) L.push('vlan ' + g.vlan + ' members port ' + aosRange('o8', x) + ' untagged');
      } else {
        if (g.native) for (const x of r) L.push('vlan ' + g.native + ' members port ' + aosRange('o8', x) + ' untagged');
        const tagged = g.allowed.filter((a) => a !== g.native);
        for (const x of r) for (const vr of runs(tagged)) L.push('vlan ' + (vr[0] === vr[1] ? vr[0] : vr[0] + '-' + vr[1]) + ' members port ' + aosRange('o8', x) + ' tagged');
      }
    }
    for (const l of m.lags) {
      L.push(`linkagg lacp agg ${l.id} size ${sizeOf(l.list.length)} actor admin-key ${l.id}`);
      for (const x of runs(l.list)) L.push(`linkagg lacp port ${aosRange('o8', x)} actor admin-key ${l.id}`);
      for (const vr of runs(l.allowed)) L.push(`vlan ${vr[0] === vr[1] ? vr[0] : vr[0] + '-' + vr[1]} members linkagg ${l.id} tagged`);
    }
    if (m.svi) L.push(`ip interface "vlan${m.svi.vlan}" address ${m.svi.ip} mask ${m.svi.mask} vlan ${m.svi.vlan}`);
    if (m.gw) L.push('ip static-route 0.0.0.0/0 gateway ' + m.gw);
    if (m.ntp) L.push('ntp server ' + m.ntp, 'ntp client admin-state enable');
    if (m.syslog) L.push('swlog output socket ' + m.syslog);
    if (m.tz) { L.push('system timezone KST'); notes.push('system timezone 이름은 버전마다 목록이 달라 장비에서 확인하세요.'); }
    if (m.community) notes.push('SNMP 는 AOS 에서 사용자 계정과 커뮤니티를 연결하는 방식이라 자동으로 만들지 않았습니다. 명령어 사전의 "SNMP 읽기 커뮤니티"를 보세요.');
    if (m.ssh) {
      L.push(`user ${m.user || 'admin'} password <비밀번호> read-write all`, 'aaa authentication ssh local');
      notes.push('<비밀번호> 를 실제 비밀번호로 바꾼 뒤 넣으세요.');
    }
    L.push('write memory flash-synchro');
    return { text: L.join('\n'), notes };
  };

  O.generate = function (g, vid) {
    const m = O.genModel(g);
    if (m.errors.length) return { errors: m.errors };
    const r = GEN[vid](m);
    return { text: r.text, notes: r.notes, errors: [] };
  };
})();
