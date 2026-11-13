#!/usr/bin/env python3
"""OiCmd 기본 명령어 데이터 → internal/server/ui/commands.json

고치는 법: 아래 ENTRIES 를 고치고 저장소 맨 위에서  python3 tools/gendata/commands.py
(go test ./... 가 commands.json 의 형식·중복을 검사한다)

벤더 키   c: 시스코 IOS/IOS-XE   j: 주니퍼 Junos(EX, ELS)   a: 얼라이드 AW+   o6: 알카텔 AOS6   o8: 알카텔 AOS8
kind      show: 조회 (일반/관리자 모드)   exec: 관리자 모드 동작(저장·재부팅·지우기·ping)   config: 설정 모드
값        문자열 하나 = 명령어. (명령어, 메모) 튜플 = 메모 붙임. None = 해당 기능 없음/다른 방법 (메모만: (None, "메모"))
<...>     자리 표시: 실제 값으로 바꿔 넣는 곳 (변환 기능에서는 아무 단어 하나와 맞는다)

모든 기본 명령어는 공식 문서 기준으로 넣었지만 장비·버전마다 다를 수 있어 화면에서는 '미확인'으로 시작한다.
사용자가 실제 장비에서 쳐 보고 '확인됨'으로 바꾼다(그 표시는 user.json 에 저장).
"""
import json, os, sys

VENDORS = [
    {"id": "c", "name": "시스코", "os": "IOS / IOS-XE", "port": "Gi1/0/1", "prompt": "Switch#",
     "config": "configure terminal", "save": "write memory", "doc": "https://www.cisco.com/c/en/us/support/switches/index.html"},
    {"id": "j", "name": "주니퍼", "os": "Junos (EX, ELS)", "port": "ge-0/0/0", "prompt": "user@switch>",
     "config": "configure", "save": "commit", "doc": "https://www.juniper.net/documentation/"},
    {"id": "a", "name": "얼라이드", "os": "AlliedWare Plus", "port": "port1.0.1", "prompt": "awplus#",
     "config": "configure terminal", "save": "write", "doc": "https://www.alliedtelesis.com/support/documentation"},
    {"id": "o6", "name": "알카텔 AOS6", "os": "OmniSwitch AOS 6", "port": "1/1", "prompt": "->",
     "config": None, "save": "write memory → copy working certified", "doc": "https://myportal.al-enterprise.com/"},
    {"id": "o8", "name": "알카텔 AOS8", "os": "OmniSwitch AOS 8", "port": "1/1/1", "prompt": "->",
     "config": None, "save": "write memory flash-synchro", "doc": "https://myportal.al-enterprise.com/"},
]

CATS = [
    ("info", "기본·장비 정보"),
    ("intf", "인터페이스·포트"),
    ("vlan", "VLAN"),
    ("l2", "MAC·ARP·이웃 장비"),
    ("lag", "포트 묶기 (LACP)"),
    ("stp", "스패닝 트리"),
    ("l3", "IP·라우팅"),
    ("mgmt", "관리·보안"),
    ("trouble", "로그·상태·장애"),
    ("misc", "미러링·스톰"),
    ("save", "저장·재부팅·백업"),
]

AOS_CFG = "AOS 는 설정 모드 없이 바로 입력하면 즉시 적용됩니다."

E = []
def add(id, cat, kind, title, v, desc="", keys=""):
    E.append({"id": id, "cat": cat, "kind": kind, "t": title, "d": desc, "k": keys, "v": v})

# ───────────────────────── 기본·장비 정보 ─────────────────────────
add("show-version", "info", "show", "OS 버전·모델·업타임 보기", {
    "c": "show version",
    "j": "show version",
    "a": "show version",
    "o6": ("show microcode", "OS 버전. 모델·업타임은 show system / show chassis"),
    "o8": ("show microcode", "OS 버전. 모델·업타임은 show system / show chassis"),
}, keys="버전 펌웨어 version firmware 모델 uptime")

add("enter-config", "info", "exec", "관리자 모드·설정 모드 들어가기", {
    "c": ("enable\nconfigure terminal", "나올 때는 end (또는 Ctrl+Z)"),
    "j": ("configure", "나올 때는 exit. 바꾼 것은 commit 해야 적용됩니다"),
    "a": ("enable\nconfigure terminal", "나올 때는 end"),
    "o6": (None, "AOS 는 로그인하면 바로 설정할 수 있고, 친 명령이 즉시 적용됩니다"),
    "o8": (None, "AOS 는 로그인하면 바로 설정할 수 있고, 친 명령이 즉시 적용됩니다"),
}, keys="conf t configure 설정 모드 enable 관리자 모드 en config")

add("show-system", "info", "show", "장비 이름·업타임·위치 보기", {
    "c": ("show version | include uptime", "장비 이름(hostname)은 프롬프트에 보입니다"),
    "j": "show system uptime",
    "a": "show system",
    "o6": "show system",
    "o8": "show system",
}, keys="uptime 업타임 켜진 시간 시스템 system")

add("show-inventory", "info", "show", "시리얼 번호·하드웨어 구성 보기", {
    "c": "show inventory",
    "j": "show chassis hardware",
    "a": ("show system", "모듈·SFP 는 show system pluggable"),
    "o6": "show chassis",
    "o8": "show chassis",
}, keys="시리얼 serial 일련번호 하드웨어 inventory 모듈 섀시 chassis")

add("show-run", "info", "show", "지금 돌아가는 설정 보기", {
    "c": "show running-config",
    "j": ("show configuration | display set", "set 명령 형태로 보기. 계층 형태는 show configuration"),
    "a": "show running-config",
    "o6": ("show configuration snapshot", "write terminal 도 같음"),
    "o8": ("show configuration snapshot", "write terminal 도 같음"),
}, keys="설정 config running 런닝 sh run 컨피그")

add("show-start", "info", "show", "저장된(부팅) 설정 보기", {
    "c": "show startup-config",
    "j": (None, "commit 한 설정이 곧 저장된 설정입니다 (show configuration). 이전 설정은 show system rollback"),
    "a": "show startup-config",
    "o6": ("show running-directory", "지금 working/certified 중 어디로 떴는지와 둘이 같은지(Synchronized) 확인"),
    "o8": ("show running-directory", "지금 working/certified 중 어디로 떴는지와 둘이 같은지(Synchronized) 확인"),
}, keys="startup 스타트업 저장된 설정 부팅 설정")

add("show-clock", "info", "show", "시간 보기", {
    "c": "show clock",
    "j": "show system uptime",
    "a": "show clock",
    "o6": ("system date", "인자 없이 치면 지금 날짜, system time 은 시간"),
    "o8": ("system date", "인자 없이 치면 지금 날짜, system time 은 시간"),
}, keys="시계 시간 날짜 clock time date")

add("show-users", "info", "show", "접속해 있는 사용자 보기", {
    "c": "show users",
    "j": "show system users",
    "a": "show users",
    "o6": ("who", "계정 목록은 show user"),
    "o8": ("who", "계정 목록은 show user"),
}, keys="사용자 접속자 세션 users who")

add("show-tech", "info", "show", "장애 문의용 전체 정보 뽑기", {
    "c": ("show tech-support", "아주 깁니다. 터미널 로그 저장을 켜고 실행하세요"),
    "j": ("request support information | save /var/tmp/rsi.txt", "파일로 저장"),
    "a": ("show tech-support", "결과가 파일로 저장됩니다(tech-support.txt.gz)"),
    "o6": ("show tech-support", "결과가 /flash 에 파일로 저장됩니다"),
    "o8": ("show tech-support eng complete", "결과가 /flash 에 파일로 저장됩니다"),
}, keys="tech support 기술지원 tac 문의")

# ───────────────────────── 인터페이스 ─────────────────────────
add("intf-status", "intf", "show", "포트 상태 한눈에 보기 (연결·VLAN·속도)", {
    "c": "show interfaces status",
    "j": "show interfaces terse",
    "a": ("show interface brief", "버전에 따라 show interface status 도 됨"),
    "o6": "show interfaces status",
    "o8": "show interfaces status",
}, keys="포트 상태 link up down 연결 인터페이스 status brief terse")

add("intf-detail", "intf", "show", "포트 하나 자세히 보기 (카운터 포함)", {
    "c": "show interfaces <포트>",
    "j": "show interfaces <포트> extensive",
    "a": "show interface <포트>",
    "o6": "show interfaces <포트>",
    "o8": ("show interfaces port <포트>", "예전 8.x 는 show interfaces <포트>"),
}, keys="포트 자세히 카운터 에러 interface detail")

add("intf-errors", "intf", "show", "포트 에러 카운터 보기", {
    "c": "show interfaces counters errors",
    "j": "show interfaces <포트> extensive | match error",
    "a": ("show interface <포트>", "input/output errors, CRC 줄을 봅니다"),
    "o6": "show interfaces <포트> counters errors",
    "o8": ("show interfaces port <포트> counters errors", "버전별 확인 필요"),
}, keys="에러 crc error 충돌 drop 카운터")

add("intf-clear", "intf", "exec", "포트 카운터 지우기", {
    "c": "clear counters <포트>",
    "j": "clear interfaces statistics <포트>",
    "a": (None, "버전에 따라 다름. 공식 문서 확인 필요"),
    "o6": ("interfaces <포트> no l2 statistics", "버전별 확인 필요"),
    "o8": "clear interfaces <포트> l2-statistics",
}, keys="카운터 초기화 clear counters 지우기")

add("intf-desc", "intf", "config", "포트 설명 붙이기", {
    "c": "interface <포트>\n description <설명>",
    "j": 'set interfaces <포트> description "<설명>"',
    "a": "interface <포트>\n description <설명>",
    "o6": 'interfaces <포트> alias "<설명>"',
    "o8": 'interfaces port <포트> alias "<설명>"',
}, keys="설명 description alias 이름 붙이기")

add("intf-down", "intf", "config", "포트 끄기 (shutdown)", {
    "c": "interface <포트>\n shutdown",
    "j": "set interfaces <포트> disable",
    "a": "interface <포트>\n shutdown",
    "o6": "interfaces <포트> admin down",
    "o8": "interfaces port <포트> admin-state disable",
}, keys="셧다운 shutdown 끄기 disable 비활성")

add("intf-up", "intf", "config", "포트 켜기 (no shutdown)", {
    "c": "interface <포트>\n no shutdown",
    "j": "delete interfaces <포트> disable",
    "a": "interface <포트>\n no shutdown",
    "o6": "interfaces <포트> admin up",
    "o8": "interfaces port <포트> admin-state enable",
}, keys="노셧 no shutdown 켜기 enable 활성")

add("intf-speed", "intf", "config", "속도·듀플렉스 고정", {
    "c": "interface <포트>\n speed 100\n duplex full",
    "j": "set interfaces <포트> ether-options speed 100m\nset interfaces <포트> ether-options no-auto-negotiation",
    "a": "interface <포트>\n speed 100\n duplex full",
    "o6": "interfaces <포트> speed 100\ninterfaces <포트> duplex full",
    "o8": "interfaces port <포트> speed 100\ninterfaces port <포트> duplex full",
}, desc="상대 장비와 양쪽을 똑같이 맞춰야 합니다. 한쪽만 고정하면 duplex 불일치가 납니다.",
   keys="속도 speed duplex 듀플렉스 반이중 전이중 auto")

add("intf-sfp", "intf", "show", "SFP(광모듈) 정보·광 세기 보기", {
    "c": "show interfaces <포트> transceiver detail",
    "j": "show interfaces diagnostics optics <포트>",
    "a": ("show system pluggable diagnostics", "모듈 목록은 show system pluggable"),
    "o6": "show interfaces <포트> ddm",
    "o8": ("show interfaces port <포트> ddm", "예전 8.x 는 show interfaces <포트> ddm"),
}, keys="sfp 광 모듈 transceiver ddm optics 광세기 dbm")

add("poe", "intf", "show", "PoE 전력 보기", {
    "c": "show power inline",
    "j": "show poe interface",
    "a": "show power-inline",
    "o6": ("show lanpower 1", "1 = 슬롯(스택 번호)"),
    "o8": ("show lanpower slot 1/1", "1/1 = 섀시/슬롯"),
}, keys="poe 전원 lanpower 전력 ap 카메라")

# ───────────────────────── VLAN ─────────────────────────
add("vlan-show", "vlan", "show", "VLAN 목록과 포트 보기", {
    "c": "show vlan brief",
    "j": "show vlans",
    "a": ("show vlan brief", "show vlan all 도 됨"),
    "o6": ("show vlan", "포트별은 show vlan port"),
    "o8": ("show vlan", "포트별은 show vlan members"),
}, keys="vlan 목록 브이랜 show vlan")

add("vlan-create", "vlan", "config", "VLAN 만들기 (이름 붙이기)", {
    "c": "vlan <VLAN번호>\n name <이름>",
    "j": ("set vlans <이름> vlan-id <VLAN번호>", "주니퍼는 VLAN 을 이름으로 다룹니다"),
    "a": "vlan database\n vlan <VLAN번호> name <이름>",
    "o6": 'vlan <VLAN번호> name "<이름>"',
    "o8": 'vlan <VLAN번호> admin-state enable name "<이름>"',
}, keys="vlan 생성 만들기 추가 create")

add("vlan-delete", "vlan", "config", "VLAN 지우기", {
    "c": "no vlan <VLAN번호>",
    "j": "delete vlans <이름>",
    "a": "vlan database\n no vlan <VLAN번호>",
    "o6": "no vlan <VLAN번호>",
    "o8": "no vlan <VLAN번호>",
}, keys="vlan 삭제 지우기 delete remove")

add("vlan-access", "vlan", "config", "포트를 VLAN 에 넣기 (access, untagged)", {
    "c": "interface <포트>\n switchport mode access\n switchport access vlan <VLAN번호>",
    "j": "set interfaces <포트> unit 0 family ethernet-switching interface-mode access vlan members <이름>",
    "a": "interface <포트>\n switchport mode access\n switchport access vlan <VLAN번호>",
    "o6": ("vlan <VLAN번호> port default <포트>", "포트 범위도 됨 (예: 1/1-12)"),
    "o8": ("vlan <VLAN번호> members port <포트> untagged", "포트 범위도 됨 (예: 1/1/1-12)"),
}, keys="access 액세스 untagged 언태그 포트 vlan 할당 pvid")

add("vlan-trunk", "vlan", "config", "트렁크 포트 (여러 VLAN, tagged)", {
    "c": ("interface <포트>\n switchport mode trunk\n switchport trunk allowed vlan <VLAN목록>",
          "예전 장비(3750 등)는 switchport mode trunk 전에 switchport trunk encapsulation dot1q"),
    "j": "set interfaces <포트> unit 0 family ethernet-switching interface-mode trunk vlan members [ <이름> <이름> ]",
    "a": ("interface <포트>\n switchport mode trunk\n switchport trunk allowed vlan add <VLAN목록>", "VLAN 을 추가할 때는 add, 뺄 때는 remove"),
    "o6": ("vlan <VLAN번호> 802.1q <포트>", "VLAN 마다 한 줄씩"),
    "o8": ("vlan <VLAN번호> members port <포트> tagged", "VLAN 범위도 됨 (예: vlan 10-20 members ...)"),
}, keys="trunk 트렁크 tagged 태그 802.1q dot1q allowed")

add("vlan-trunk-add", "vlan", "config", "트렁크에 VLAN 하나 더 허용", {
    "c": ("interface <포트>\n switchport trunk allowed vlan add <VLAN번호>", "add 를 빼먹으면 기존 목록이 통째로 바뀝니다!"),
    "j": "set interfaces <포트> unit 0 family ethernet-switching vlan members <이름>",
    "a": "interface <포트>\n switchport trunk allowed vlan add <VLAN번호>",
    "o6": "vlan <VLAN번호> 802.1q <포트>",
    "o8": "vlan <VLAN번호> members port <포트> tagged",
}, keys="trunk 추가 vlan add allowed 허용")

add("vlan-native", "vlan", "config", "트렁크의 native(untagged) VLAN 정하기", {
    "c": "interface <포트>\n switchport trunk native vlan <VLAN번호>",
    "j": "set interfaces <포트> native-vlan-id <VLAN번호>",
    "a": ("interface <포트>\n switchport trunk native vlan <VLAN번호>", "native 없이 모두 tagged 로: switchport trunk native vlan none"),
    "o6": ("vlan <VLAN번호> port default <포트>", "AOS 는 포트의 default VLAN 이 untagged 로 나갑니다"),
    "o8": "vlan <VLAN번호> members port <포트> untagged",
}, keys="native 네이티브 untagged pvid 기본 vlan")

add("vlan-port-show", "vlan", "show", "포트가 어느 VLAN 에 들어 있는지 보기", {
    "c": ("show interfaces <포트> switchport", "트렁크 전체는 show interfaces trunk"),
    "j": "show ethernet-switching interface <포트>",
    "a": "show interface <포트> switchport",
    "o6": "show vlan port <포트>",
    "o8": "show vlan members port <포트>",
}, keys="포트 vlan 확인 switchport trunk 멤버")

# ───────────────────────── MAC·ARP·이웃 ─────────────────────────
add("mac-table", "l2", "show", "MAC 주소 표 보기", {
    "c": "show mac address-table",
    "j": "show ethernet-switching table",
    "a": "show mac address-table",
    "o6": "show mac-address-table",
    "o8": "show mac-learning",
}, keys="mac 맥 주소 테이블 address table cam")

add("mac-find", "l2", "show", "MAC 주소로 연결 포트 찾기", {
    "c": ("show mac address-table address <MAC>", "MAC 형식: aaaa.bbbb.cccc"),
    "j": ("show ethernet-switching table | match <MAC>", "MAC 형식: aa:bb:cc:dd:ee:ff"),
    "a": ("show mac address-table | include <MAC>", "MAC 형식: aaaa.bbbb.cccc"),
    "o6": ("show mac-address-table | grep <MAC>", "MAC 형식: aa:bb:cc:dd:ee:ff"),
    "o8": ("show mac-learning mac-address <MAC>", "MAC 형식: aa:bb:cc:dd:ee:ff"),
}, keys="mac 찾기 어느 포트 위치 단말 추적")

add("mac-port", "l2", "show", "포트 하나에 붙은 MAC 보기", {
    "c": "show mac address-table interface <포트>",
    "j": "show ethernet-switching table interface <포트>",
    "a": "show mac address-table interface <포트>",
    "o6": "show mac-address-table <포트>",
    "o8": "show mac-learning port <포트>",
}, keys="포트 mac 단말 연결")

add("mac-clear", "l2", "exec", "MAC 표 비우기 (다시 배우게)", {
    "c": "clear mac address-table dynamic",
    "j": "clear ethernet-switching table",
    "a": "clear mac address-table dynamic",
    "o6": (None, "버전에 따라 다름. 공식 문서 확인 필요"),
    "o8": (None, "버전에 따라 다름. 공식 문서 확인 필요"),
}, keys="mac 초기화 clear 플래시 flush")

add("arp", "l2", "show", "ARP 표 보기 (IP ↔ MAC)", {
    "c": ("show ip arp", "L2 스위치는 자기 관리 대역만 보입니다"),
    "j": "show arp no-resolve",
    "a": "show arp",
    "o6": "show arp",
    "o8": "show arp",
}, keys="arp ip mac 매핑 대응")

add("arp-find", "l2", "show", "IP 로 MAC 찾기", {
    "c": "show ip arp <IP>",
    "j": "show arp no-resolve | match <IP>",
    "a": "show arp | include <IP>",
    "o6": "show arp | grep <IP>",
    "o8": "show arp | grep <IP>",
}, keys="ip 로 mac 찾기 arp")

add("lldp-show", "l2", "show", "옆에 붙은 장비 보기 (LLDP)", {
    "c": ("show lldp neighbors", "자세히: show lldp neighbors detail. 시스코끼리는 show cdp neighbors 도 됨"),
    "j": ("show lldp neighbors", "자세히: show lldp neighbors interface <포트>"),
    "a": ("show lldp neighbors", "자세히: show lldp neighbors detail"),
    "o6": "show lldp remote-system",
    "o8": "show lldp remote-system",
}, keys="lldp cdp 이웃 neighbor 옆 장비 연결 구성도")

add("lldp-on", "l2", "config", "LLDP 켜기", {
    "c": "lldp run",
    "j": ("set protocols lldp interface all", "EX 는 보통 기본으로 켜져 있음"),
    "a": "lldp run",
    "o6": ("lldp <포트> lldpdu tx-and-rx", "보통 기본으로 켜져 있음"),
    "o8": ("lldp port <포트> lldpdu tx-and-rx", "보통 기본으로 켜져 있음"),
}, keys="lldp 켜기 활성 run enable")

# ───────────────────────── LACP ─────────────────────────
add("lacp-create", "lag", "config", "LACP 로 포트 묶기", {
    "c": ("interface range <포트> - <끝번호>\n channel-group <번호> mode active",
          "묶음 설정(트렁크 등)은 interface Port-channel<번호> 에서 합니다"),
    "j": ("set chassis aggregated-devices ethernet device-count <개수>\n"
          "set interfaces <포트> ether-options 802.3ad ae<번호>\n"
          "set interfaces ae<번호> aggregated-ether-options lacp active",
          "묶음 설정(트렁크 등)은 set interfaces ae<번호> unit 0 family ethernet-switching ..."),
    "a": ("interface <포트>-<끝포트>\n channel-group <번호> mode active", "묶음 이름은 po<번호>, 설정은 interface po<번호> 에서"),
    "o6": ("lacp linkagg <번호> size <크기> actor admin key <번호>\n"
           "lacp agg <포트> actor admin key <번호>",
           "크기는 2/4/8. 포트마다 lacp agg 줄. VLAN 은 vlan <VLAN번호> 802.1q <번호> 처럼 묶음 번호로"),
    "o8": ("linkagg lacp agg <번호> size <크기> actor admin-key <번호>\n"
           "linkagg lacp port <포트> actor admin-key <번호>",
           "크기는 2/4/8/16. VLAN 은 vlan <VLAN번호> members linkagg <번호> tagged"),
}, keys="lacp 포트채널 port-channel etherchannel 이더채널 링크 묶기 aggregation lag linkagg ae")

add("lag-static", "lag", "config", "LACP 없이 고정으로 묶기 (static)", {
    "c": "interface range <포트> - <끝번호>\n channel-group <번호> mode on",
    "j": (None, "주니퍼는 aggregated-ether-options 에서 lacp 줄을 빼면 static"),
    "a": ("interface <포트>-<끝포트>\n static-channel-group <번호>", "묶음 이름은 sa<번호>"),
    "o6": "static linkagg <번호> size <크기>\nstatic agg <포트> agg num <번호>",
    "o8": "linkagg static agg <번호> size <크기>\nlinkagg static port <포트> agg <번호>",
}, keys="static 고정 묶기 mode on 정적 linkagg")

add("lag-show", "lag", "show", "묶인 포트 상태 보기", {
    "c": "show etherchannel summary",
    "j": "show lacp interfaces",
    "a": ("show etherchannel", "static 은 show static-channel-group"),
    "o6": ("show linkagg", "포트별: show linkagg port"),
    "o8": ("show linkagg", "포트별: show linkagg port"),
}, keys="lacp 상태 etherchannel 포트채널 linkagg 확인")

# ───────────────────────── STP ─────────────────────────
add("stp-show", "stp", "show", "스패닝 트리 상태 보기 (루트·막힌 포트)", {
    "c": "show spanning-tree",
    "j": ("show spanning-tree bridge", "포트별: show spanning-tree interface"),
    "a": ("show spanning-tree", "짧게: show spanning-tree brief"),
    "o6": ("show spantree", "포트별: show spantree ports"),
    "o8": ("show spantree", "포트별: show spantree ports"),
}, keys="stp 스패닝 spanning tree 루트 root 블로킹 루프")

add("stp-mode", "stp", "config", "RSTP 로 바꾸기", {
    "c": ("spanning-tree mode rapid-pvst", "시스코 기본은 pvst"),
    "j": ("set protocols rstp", "EX 기본이 RSTP"),
    "a": ("spanning-tree mode rstp", "AW+ 기본이 RSTP"),
    "o6": ("bridge protocol rstp", "1x1 모드면 VLAN 별로 동작. 버전별 확인 필요"),
    "o8": ("spantree protocol rstp", "버전별 확인 필요"),
}, keys="rstp rapid 모드 스패닝 변경 mode")

add("stp-root", "stp", "config", "이 장비를 루트로 만들기 (우선순위 낮추기)", {
    "c": "spanning-tree vlan <VLAN번호> priority 4096",
    "j": "set protocols rstp bridge-priority 4k",
    "a": "spanning-tree priority 4096",
    "o6": ("bridge <VLAN번호> priority 4096", "1x1 모드 기준. 버전별 확인 필요"),
    "o8": ("spantree vlan <VLAN번호> priority 4096", "버전별 확인 필요"),
}, desc="코어 스위치를 루트로 고정해 두면 루프가 생겨도 예상한 포트가 막힙니다.",
   keys="루트 root priority 우선순위 브리지")

add("stp-edge", "stp", "config", "PC 포트를 바로 열리게 (portfast/edge)", {
    "c": "interface <포트>\n spanning-tree portfast",
    "j": "set protocols rstp interface <포트> edge",
    "a": "interface <포트>\n spanning-tree edgeport",
    "o6": (None, "AOS6 는 버전별로 달라 공식 문서 확인 필요"),
    "o8": (None, "AOS8 는 버전별로 달라 공식 문서 확인 필요"),
}, keys="portfast 포트패스트 edge 엣지 edgeport pc 바로")

add("stp-bpduguard", "stp", "config", "PC 포트에 스위치가 꽂히면 막기 (BPDU guard)", {
    "c": "interface <포트>\n spanning-tree bpduguard enable",
    "j": "set protocols layer2-control bpdu-block interface <포트>",
    "a": ("interface <포트>\n spanning-tree portfast bpdu-guard enable", "edgeport 포트에서만 동작"),
    "o6": (None, "AOS6 는 버전별로 달라 공식 문서 확인 필요"),
    "o8": (None, "AOS8 는 버전별로 달라 공식 문서 확인 필요"),
}, keys="bpdu guard 가드 루프 방지 bpduguard")

# ───────────────────────── IP·라우팅 ─────────────────────────
add("ip-brief", "l3", "show", "IP 인터페이스 목록 보기", {
    "c": "show ip interface brief",
    "j": "show interfaces terse | match inet",
    "a": "show ip interface brief",
    "o6": "show ip interface",
    "o8": "show ip interface",
}, keys="ip 인터페이스 svi vlan ip 주소 brief")

add("svi", "l3", "config", "VLAN 에 IP 주기 (관리 IP / SVI)", {
    "c": "interface vlan <VLAN번호>\n ip address <IP> <마스크>\n no shutdown",
    "j": ("set interfaces irb unit <VLAN번호> family inet address <IP>/<프리픽스>\nset vlans <이름> l3-interface irb.<VLAN번호>",
          "예전(ELS 아닌) EX 는 vlan.<번호> 인터페이스"),
    "a": "interface vlan<VLAN번호>\n ip address <IP>/<프리픽스>",
    "o6": 'ip interface "vlan<VLAN번호>" address <IP> mask <마스크> vlan <VLAN번호>',
    "o8": 'ip interface "vlan<VLAN번호>" address <IP> mask <마스크> vlan <VLAN번호>',
}, keys="svi 관리 ip vlan interface 인터페이스 irb 게이트웨이 주소")

add("default-gw", "l3", "config", "기본 게이트웨이 (L2 스위치 관리용)", {
    "c": ("ip default-gateway <게이트웨이>", "ip routing 을 켠 L3 스위치는 아래 '기본 경로'를 씁니다"),
    "j": "set routing-options static route 0.0.0.0/0 next-hop <게이트웨이>",
    "a": "ip route 0.0.0.0/0 <게이트웨이>",
    "o6": "ip static-route 0.0.0.0 mask 0.0.0.0 gateway <게이트웨이>",
    "o8": "ip static-route 0.0.0.0/0 gateway <게이트웨이>",
}, keys="게이트웨이 gateway default 기본 경로 디폴트")

add("static-route", "l3", "config", "정적 경로 추가", {
    "c": "ip route <대역> <마스크> <게이트웨이>",
    "j": "set routing-options static route <대역>/<프리픽스> next-hop <게이트웨이>",
    "a": "ip route <대역>/<프리픽스> <게이트웨이>",
    "o6": "ip static-route <대역> mask <마스크> gateway <게이트웨이>",
    "o8": "ip static-route <대역>/<프리픽스> gateway <게이트웨이>",
}, keys="정적 라우팅 static route 경로 추가")

add("ip-routing", "l3", "config", "L3 라우팅 켜기", {
    "c": "ip routing",
    "j": (None, "기본으로 라우팅됨"),
    "a": (None, "기본으로 라우팅됨 (L3 지원 모델)"),
    "o6": (None, "기본으로 라우팅됨"),
    "o8": (None, "기본으로 라우팅됨"),
}, keys="라우팅 routing l3 켜기 ip routing")

add("route-show", "l3", "show", "라우팅 표 보기", {
    "c": "show ip route",
    "j": "show route",
    "a": "show ip route",
    "o6": "show ip route",
    "o8": "show ip routes",
}, keys="라우팅 테이블 route 경로 표")

add("ping", "l3", "exec", "ping", {
    "c": "ping <대상IP>",
    "j": "ping <대상IP> count 5",
    "a": "ping <대상IP>",
    "o6": "ping <대상IP>",
    "o8": "ping <대상IP>",
}, keys="ping 핑 통신 확인")

add("traceroute", "l3", "exec", "경로 추적 (traceroute)", {
    "c": "traceroute <대상IP>",
    "j": "traceroute <대상IP>",
    "a": "traceroute <대상IP>",
    "o6": "traceroute <대상IP>",
    "o8": "traceroute <대상IP>",
}, keys="traceroute tracert 경로 추적")

# ───────────────────────── 관리·보안 ─────────────────────────
add("hostname", "mgmt", "config", "장비 이름 바꾸기", {
    "c": "hostname <이름>",
    "j": "set system host-name <이름>",
    "a": "hostname <이름>",
    "o6": 'system name "<이름>"',
    "o8": 'system name "<이름>"',
}, keys="호스트네임 hostname 이름 장비명")

add("user-add", "mgmt", "config", "관리자 계정 만들기", {
    "c": "username <사용자> privilege 15 secret <비밀번호>",
    "j": ("set system login user <사용자> class super-user authentication plain-text-password",
          "엔터를 치면 비밀번호를 두 번 묻습니다"),
    "a": "username <사용자> privilege 15 password <비밀번호>",
    "o6": "user <사용자> password <비밀번호> read-write all",
    "o8": "user <사용자> password <비밀번호> read-write all",
}, keys="계정 사용자 user username 비밀번호 password 관리자")

add("ssh-on", "mgmt", "config", "SSH 켜기", {
    "c": ("ip domain-name <도메인>\ncrypto key generate rsa modulus 2048\nip ssh version 2\nline vty 0 15\n login local\n transport input ssh",
          "transport input ssh 는 텔넷을 막습니다"),
    "j": "set system services ssh",
    "a": "crypto key generate hostkey rsa 2048\nservice ssh",
    "o6": "aaa authentication ssh local",
    "o8": "aaa authentication ssh local",
}, keys="ssh 켜기 암호화 원격 접속 vty")

add("telnet-off", "mgmt", "config", "텔넷 끄기", {
    "c": "line vty 0 15\n transport input ssh",
    "j": "delete system services telnet",
    "a": "no service telnet",
    "o6": "no aaa authentication telnet",
    "o8": "no aaa authentication telnet",
}, keys="텔넷 telnet 끄기 보안 취약점")

add("snmp", "mgmt", "config", "SNMP 읽기 커뮤니티 (v2c)", {
    "c": "snmp-server community <커뮤니티> RO",
    "j": "set snmp community <커뮤니티> authorization read-only",
    "a": "snmp-server community <커뮤니티> ro",
    "o6": ("snmp community map <커뮤니티> user <사용자> on",
           "AOS 는 커뮤니티를 SNMP 권한이 있는 사용자 계정에 연결합니다. snmp security 설정도 확인"),
    "o8": ("snmp community-map mode enable\nsnmp community-map <커뮤니티> user <사용자> enable",
           "AOS 는 커뮤니티를 SNMP 권한이 있는 사용자 계정에 연결합니다. snmp security 설정도 확인"),
}, keys="snmp 커뮤니티 community nms 감시 v2c public")

add("syslog", "mgmt", "config", "로그 서버(syslog)로 보내기", {
    "c": "logging host <서버IP>",
    "j": "set system syslog host <서버IP> any any",
    "a": "log host <서버IP>",
    "o6": "swlog output socket <서버IP>",
    "o8": "swlog output socket <서버IP>",
}, keys="syslog 로그 서버 logging oilog 전송")

add("ntp", "mgmt", "config", "NTP 서버로 시간 맞추기", {
    "c": "ntp server <서버IP>",
    "j": "set system ntp server <서버IP>",
    "a": "ntp server <서버IP>",
    "o6": "ntp server <서버IP>\nntp client enable",
    "o8": "ntp server <서버IP>\nntp client admin-state enable",
}, keys="ntp 시간 동기화 time")

add("ntp-show", "mgmt", "show", "NTP 동기화 상태 보기", {
    "c": "show ntp status",
    "j": "show ntp associations",
    "a": ("show ntp associations", "show ntp status 도 됨"),
    "o6": "show ntp client",
    "o8": "show ntp status",
}, keys="ntp 상태 동기화 확인")

add("timezone", "mgmt", "config", "시간대를 한국(KST)으로", {
    "c": "clock timezone KST 9 0",
    "j": "set system time-zone Asia/Seoul",
    "a": "clock timezone KST plus 9",
    "o6": ("system timezone KST", "지원하는 이름 목록에서 고릅니다. 버전별 확인 필요"),
    "o8": ("system timezone KST", "지원하는 이름 목록에서 고릅니다. 버전별 확인 필요"),
}, keys="시간대 타임존 timezone kst 한국 시간")

add("banner", "mgmt", "config", "로그인 경고 문구 (배너)", {
    "c": "banner motd ^\n<문구>\n^",
    "j": 'set system login message "<문구>"',
    "a": "banner motd <문구>",
    "o6": (None, "/flash/switch/pre_banner.txt 파일로 넣습니다"),
    "o8": (None, "/flash/switch/pre_banner.txt 파일로 넣습니다"),
}, keys="배너 banner motd 경고문 로그인 문구 보안")

# ───────────────────────── 로그·상태·장애 ─────────────────────────
add("log-show", "trouble", "show", "장비 로그 보기", {
    "c": "show logging",
    "j": ("show log messages", "끝부분만: show log messages | last 50"),
    "a": ("show log", "재부팅 뒤에도 남는 로그: show log permanent"),
    "o6": "show log swlog",
    "o8": "show log swlog",
}, keys="로그 log logging 기록 이벤트 swlog")

add("cpu", "trouble", "show", "CPU 사용률 보기", {
    "c": ("show processes cpu sorted", "그래프: show processes cpu history"),
    "j": "show chassis routing-engine",
    "a": "show cpu",
    "o6": "show health",
    "o8": "show health",
}, keys="cpu 사용률 부하 씨피유 health")

add("memory", "trouble", "show", "메모리 사용률 보기", {
    "c": ("show memory statistics", "IOS-XE: show platform resources"),
    "j": "show chassis routing-engine",
    "a": "show memory",
    "o6": "show health",
    "o8": "show health",
}, keys="메모리 memory ram 사용률")

add("env", "trouble", "show", "온도·팬·전원 보기", {
    "c": ("show environment all", "모델에 따라 show env all"),
    "j": "show chassis environment",
    "a": "show system environment",
    "o6": ("show temperature", "전원: show powersupply, 팬: show fan"),
    "o8": ("show temperature", "전원: show powersupply, 팬: show fan"),
}, keys="온도 팬 전원 파워 psu fan temperature 환경 environment")

add("alarms", "trouble", "show", "하드웨어 경보 보기", {
    "c": ("show logging", "%로 시작하는 경고 줄을 봅니다. IOS-XE 일부: show facility-alarm status"),
    "j": "show chassis alarms",
    "a": ("show system environment", "Status 가 Ok 가 아닌 줄을 봅니다"),
    "o6": "show chassis",
    "o8": "show chassis",
}, keys="알람 경보 alarm 장애 하드웨어")

add("cable-test", "trouble", "exec", "랜선 상태 검사 (케이블 테스트)", {
    "c": ("test cable-diagnostics tdr interface <포트>\nshow cable-diagnostics tdr interface <포트>", "검사하는 동안 링크가 끊길 수 있습니다"),
    "j": ("request diagnostics tdr start interface <포트>\nshow diagnostics tdr interface <포트>", "검사하는 동안 링크가 끊길 수 있습니다"),
    "a": ("test cable-diagnostics tdr interface <포트>\nshow test cable-diagnostics tdr", "검사하는 동안 링크가 끊길 수 있습니다"),
    "o6": (None, "모델에 따라 다름. 공식 문서 확인 필요"),
    "o8": (None, "모델에 따라 다름. 공식 문서 확인 필요"),
}, keys="케이블 테스트 tdr 랜선 단선 cable diagnostics")

# ───────────────────────── 미러링·스톰 ─────────────────────────
add("mirror", "misc", "config", "포트 미러링 (패킷 떠보기)", {
    "c": "monitor session 1 source interface <포트> both\nmonitor session 1 destination interface <받는포트>",
    "j": "set forwarding-options analyzer <이름> input ingress interface <포트>.0\n"
         "set forwarding-options analyzer <이름> input egress interface <포트>.0\n"
         "set forwarding-options analyzer <이름> output interface <받는포트>.0",
    "a": ("interface <받는포트>\n mirror interface <포트> direction both", "받는 포트는 VLAN 에서 빠집니다"),
    "o6": "port mirroring 1 source <포트> destination <받는포트> bidirectional",
    "o8": "port-mirroring 1 source port <포트> destination port <받는포트> bidirectional",
}, desc="와이어샤크 PC 를 <받는포트>에 꽂으면 <포트>의 패킷이 보입니다. 다 보고 나면 꼭 지우세요.",
   keys="미러링 mirror span 스팬 패킷 캡처 와이어샤크 wireshark monitor")

add("mirror-show", "misc", "show", "미러링 설정 보기", {
    "c": "show monitor session all",
    "j": "show forwarding-options analyzer",
    "a": "show mirror",
    "o6": "show port mirroring status",
    "o8": "show port-mirroring status",
}, keys="미러링 확인 span monitor")

add("storm", "misc", "config", "브로드캐스트 폭주 제한 (storm control)", {
    "c": "interface <포트>\n storm-control broadcast level 10",
    "j": "set forwarding-options storm-control-profiles <이름> all bandwidth-percentage 10\n"
         "set interfaces <포트> unit 0 family ethernet-switching storm-control <이름>",
    "a": "interface <포트>\n storm-control broadcast level 10",
    "o6": (None, "AOS6 는 버전별로 달라 공식 문서 확인 필요 (flood-limit)"),
    "o8": (None, "AOS8 는 버전별로 달라 공식 문서 확인 필요 (flood-limit)"),
}, keys="스톰 storm broadcast 브로드캐스트 폭주 루프")

# ───────────────────────── 저장·재부팅·백업 ─────────────────────────
add("save", "save", "exec", "설정 저장", {
    "c": ("write memory", "copy running-config startup-config 도 같음"),
    "j": ("commit", "설정 모드에서. 먼저 commit check 로 검사하면 안전"),
    "a": ("write", "copy running-config startup-config 도 같음"),
    "o6": ("write memory\ncopy working certified", "copy working certified 까지 해야 재부팅 뒤에도 남습니다"),
    "o8": ("write memory flash-synchro", "working 저장과 certified 복사를 한 번에"),
}, keys="저장 save write 세이브 wr commit 메모리")

add("diff", "save", "show", "바꾼 내용 미리 보기 (저장 전 비교)", {
    "c": (None, "IOS 는 바로 비교가 어려움. IOS-XE: show archive config differences"),
    "j": ("show | compare", "설정 모드에서. commit 전에 꼭 확인"),
    "a": (None, "show running-config 와 show startup-config 를 비교"),
    "o6": ("show configuration status", "저장 안 된 변경이 있는지 표시"),
    "o8": ("show configuration status", "저장 안 된 변경이 있는지 표시"),
}, keys="비교 diff compare 변경 확인 차이")

add("rollback", "save", "exec", "직전 설정으로 되돌리기", {
    "c": (None, "저장 전이면 reload (저장된 설정으로 부팅). 아카이브가 있으면 configure replace"),
    "j": ("rollback 1\ncommit", "설정 모드에서. 0 은 지금, 1 은 바로 전 commit"),
    "a": (None, "저장 전이면 reload"),
    "o6": ("reload", "저장하지 않았으면 certified 설정으로 다시 뜹니다"),
    "o8": ("reload from working no rollback-timeout", "write memory 전이면 이전 설정"),
}, keys="롤백 rollback 되돌리기 복구 취소")

add("commit-confirm", "save", "exec", "자동 되돌림 걸고 적용 (원격 작업 안전장치)", {
    "c": ("reload in 10", "작업이 끝나면 reload cancel. 저장 안 한 상태여야 의미가 있음"),
    "j": ("commit confirmed 5", "5분 안에 다시 commit 하지 않으면 자동으로 되돌아감"),
    "a": (None, "저장하지 않고 작업하다 끊기면 reload 로 되돌리기"),
    "o6": (None, "저장하지 않고 작업하다 끊기면 reload 로 되돌리기"),
    "o8": (None, "저장하지 않고 작업하다 끊기면 reload 로 되돌리기"),
}, desc="원격으로 관리 IP·VLAN 을 바꾸다 접속이 끊길 때를 대비합니다.",
   keys="commit confirmed reload in 원격 안전 되돌림")

add("reboot", "save", "exec", "재부팅", {
    "c": "reload",
    "j": "request system reboot",
    "a": ("reload", "reboot 도 같음"),
    "o6": ("reload", "저장 안 한 설정은 사라집니다"),
    "o8": "reload from working no rollback-timeout",
}, keys="재부팅 리부팅 reload reboot 재시작")

add("backup", "save", "exec", "설정 파일 백업 (TFTP)", {
    "c": "copy running-config tftp://<서버IP>/<파일>",
    "j": ("file copy /config/juniper.conf.gz scp://<사용자>@<서버IP>/<파일>", "텍스트로: show configuration | save /var/tmp/<파일>"),
    "a": "copy running-config tftp://<서버IP>/<파일>",
    "o6": (None, "PC 에서 FTP/SCP 로 /flash/working/boot.cfg 를 가져옵니다"),
    "o8": (None, "PC 에서 SCP/SFTP 로 /flash/working/vcboot.cfg 를 가져옵니다"),
}, keys="백업 backup tftp 설정 파일 복사 copy")

add("factory", "save", "exec", "공장 초기화 (설정 모두 지우기)", {
    "c": ("write erase\ndelete flash:vlan.dat\nreload", "되돌릴 수 없습니다! 재부팅 때 저장하겠냐고 물으면 no"),
    "j": ("request system zeroize", "되돌릴 수 없습니다! 설정·로그 모두 지우고 재부팅"),
    "a": ("erase startup-config\nreload", "되돌릴 수 없습니다!"),
    "o6": (None, "되돌릴 수 없는 작업이라 공식 절차 확인 필요"),
    "o8": (None, "되돌릴 수 없는 작업이라 공식 절차 확인 필요"),
}, keys="초기화 공장 factory reset erase 지우기 zeroize", desc="되돌릴 수 없습니다. 콘솔로 붙어 있는 상태에서만 하세요.")


def norm(v):
    out = {}
    for k, x in v.items():
        if x is None:
            out[k] = {"cmd": None, "note": ""}
        elif isinstance(x, tuple):
            out[k] = {"cmd": x[0], "note": x[1] or ""}
        else:
            out[k] = {"cmd": x, "note": ""}
    return out


def main():
    ids = set()
    vk = [v["id"] for v in VENDORS]
    cats = [c[0] for c in CATS]
    for e in E:
        assert e["id"] not in ids, "중복 id " + e["id"]
        ids.add(e["id"])
        assert e["cat"] in cats, e["id"]
        assert e["kind"] in ("show", "exec", "config"), e["id"]
        assert set(e["v"]) == set(vk), "벤더 빠짐 " + e["id"]
    data = {
        "version": 1,
        "vendors": VENDORS,
        "cats": [{"id": a, "name": b} for a, b in CATS],
        "aosConfigNote": AOS_CFG,
        "entries": [{**e, "v": norm(e["v"])} for e in E],
    }
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = os.path.join(root, "internal", "server", "ui", "commands.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    n = sum(1 for e in E for x in e["v"].values() if not (x is None or (isinstance(x, tuple) and x[0] is None)))
    print(f"{len(E)}개 항목, 명령어 {n}개 → {os.path.relpath(out, root)}")


if __name__ == "__main__":
    main()
