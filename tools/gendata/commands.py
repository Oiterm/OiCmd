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
    ("l3", "IP·정적 라우팅·DHCP"),
    ("ospf", "OSPF"),
    ("bgp", "BGP"),
    ("rip", "RIP·EIGRP"),
    ("fhrp", "게이트웨이 이중화 (VRRP·HSRP)"),
    ("mcast", "멀티캐스트 (IGMP·PIM)"),
    ("remote", "원격 접속 (SSH·텔넷)"),
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

# ───────────────────────── 원격 접속 (SSH·텔넷) ─────────────────────────
add("ssh-show", "remote", "show", "SSH 켜졌는지·설정 보기", {
    "c": ("show ip ssh", "접속한 SSH 세션: show ssh"),
    "j": "show configuration system services",
    "a": "show ssh server",
    "o6": ("show aaa authentication", "ssh·telnet·http 가 어떤 인증으로 켜져 있는지"),
    "o8": ("show aaa authentication", "ssh·telnet·http 가 어떤 인증으로 켜져 있는지"),
}, keys="ssh 상태 확인 켜짐 서버 22")

add("telnet-on", "remote", "config", "텔넷 켜기", {
    "c": ("line vty 0 15\n login local\n transport input telnet ssh", "로그인할 계정(username)이 있어야 합니다. 보안 점검에서는 텔넷을 끄라고 합니다"),
    "j": "set system services telnet",
    "a": "service telnet",
    "o6": "aaa authentication telnet local",
    "o8": "aaa authentication telnet local",
}, keys="텔넷 telnet 켜기 23 원격")

add("vty-acl", "remote", "config", "원격 접속 허용 IP 제한 (관리 PC 만)", {
    "c": ("ip access-list standard MGMT\n permit <대역> <와일드카드>\nline vty 0 15\n access-class MGMT in",
          "와일드카드는 마스크를 뒤집은 값 (255.255.255.0 → 0.0.0.255). 지금 쓰는 PC 대역이 빠지면 바로 끊깁니다"),
    "j": ("set policy-options prefix-list MGMT <대역>/<프리픽스>\n"
          "set firewall family inet filter PROTECT-RE term SSH from source-prefix-list MGMT\n"
          "set firewall family inet filter PROTECT-RE term SSH from protocol tcp\n"
          "set firewall family inet filter PROTECT-RE term SSH from destination-port ssh\n"
          "set firewall family inet filter PROTECT-RE term SSH then accept\n"
          "set firewall family inet filter PROTECT-RE term SSH-DROP from protocol tcp\n"
          "set firewall family inet filter PROTECT-RE term SSH-DROP from destination-port ssh\n"
          "set firewall family inet filter PROTECT-RE term SSH-DROP then discard\n"
          "set firewall family inet filter PROTECT-RE term ALL then accept\n"
          "set interfaces lo0 unit 0 family inet filter input PROTECT-RE",
          "lo0 필터는 잘못 넣으면 접속이 끊깁니다. commit confirmed 5 로 넣으세요"),
    "a": (None, "버전에 따라 다름 (line vty 의 access-class 등). 공식 문서 확인 필요"),
    "o6": (None, "공식 문서 확인 필요"),
    "o8": (None, "공식 문서 확인 필요"),
}, keys="acl 접속 제한 허용 ip vty access-class 관리 pc 보안 점검")

add("session-timeout", "remote", "config", "접속 자동 끊김 시간 (유휴 시간)", {
    "c": ("line vty 0 15\n exec-timeout 10 0", "10분 0초. 콘솔은 line con 0"),
    "j": ("set system login class <클래스> idle-timeout 10", "사용자에게 붙인 로그인 클래스에 겁니다 (분 단위)"),
    "a": ("line vty 0 32\n exec-timeout 10 0", "vty 번호 범위는 장비마다 다를 수 있습니다"),
    "o6": ("session timeout cli 10", "분 단위"),
    "o8": ("session timeout cli 10", "분 단위"),
}, keys="타임아웃 timeout 유휴 자동 로그아웃 exec-timeout 세션 보안 점검")

add("ssh-client", "remote", "exec", "이 장비에서 다른 장비로 SSH·텔넷 접속", {
    "c": "ssh -l <사용자> <대상IP>\ntelnet <대상IP>",
    "j": "ssh <사용자>@<대상IP>\ntelnet <대상IP>",
    "a": ("ssh <대상IP>\ntelnet <대상IP>", "사용자 이름을 정하는 방법은 버전별 확인 필요"),
    "o6": "ssh <대상IP>\ntelnet <대상IP>",
    "o8": "ssh <대상IP>\ntelnet <대상IP>",
}, keys="ssh 접속 telnet 점프 다른 장비 원격 클라이언트")

add("session-kill", "remote", "exec", "남의 접속 세션 끊기", {
    "c": ("show users\nclear line vty <번호>", "show users 에서 번호 확인"),
    "j": "request system logout user <사용자>",
    "a": ("show users\nclear line vty <번호>", "버전별 확인 필요"),
    "o6": ("who\nkill <번호>", "who 에서 세션 번호 확인"),
    "o8": ("who\nkill <번호>", "who 에서 세션 번호 확인"),
}, keys="세션 끊기 강제 로그아웃 kill clear line 접속자")

# ───────────────────────── 라우팅 프로토콜·이중화 ─────────────────────────
add("ospf", "ospf", "config", "OSPF 켜기 (area 0 에 대역 넣기)", {
    "c": ("router ospf 1\n router-id <라우터ID>\n network <대역> <와일드카드> area 0", "와일드카드는 마스크를 뒤집은 값 (255.255.255.0 → 0.0.0.255)"),
    "j": ("set routing-options router-id <라우터ID>\nset protocols ospf area 0.0.0.0 interface irb.<VLAN번호>", "OSPF 를 돌릴 인터페이스마다 한 줄"),
    "a": "router ospf\n ospf router-id <라우터ID>\n network <대역>/<프리픽스> area 0",
    "o6": ('ip load ospf\nip ospf area 0.0.0.0\nip ospf interface "vlan<VLAN번호>"\nip ospf interface "vlan<VLAN번호>" area 0.0.0.0\n'
           'ip ospf interface "vlan<VLAN번호>" status enable\nip ospf status enable',
           "인터페이스 이름은 ip interface 로 만든 이름 그대로 (예: vlan10). 라우터 ID 는 ip router router-id <라우터ID>"),
    "o8": ('ip load ospf\nip ospf area 0.0.0.0\nip ospf interface "vlan<VLAN번호>"\nip ospf interface "vlan<VLAN번호>" area 0.0.0.0\n'
           'ip ospf interface "vlan<VLAN번호>" admin-state enable\nip ospf admin-state enable',
           "인터페이스 이름은 ip interface 로 만든 이름 그대로. 버전별 확인 필요"),
}, keys="ospf 오에스피에프 동적 라우팅 area 에어리어 router-id")

add("ospf-nbr", "ospf", "show", "OSPF 이웃 보기 (Full 인지)", {
    "c": "show ip ospf neighbor",
    "j": "show ospf neighbor",
    "a": "show ip ospf neighbor",
    "o6": "show ip ospf neighbor",
    "o8": "show ip ospf neighbor",
}, keys="ospf 이웃 neighbor full 인접 adjacency")

add("ospf-intf", "ospf", "show", "OSPF 인터페이스 보기 (area·DR·cost)", {
    "c": "show ip ospf interface brief",
    "j": "show ospf interface",
    "a": "show ip ospf interface",
    "o6": "show ip ospf interface",
    "o8": "show ip ospf interface",
}, keys="ospf 인터페이스 dr bdr cost area")

add("ospf-route", "ospf", "show", "OSPF 로 배운 경로 보기", {
    "c": "show ip route ospf",
    "j": "show route protocol ospf",
    "a": "show ip route ospf",
    "o6": ("show ip ospf routes", "버전별 확인 필요"),
    "o8": ("show ip ospf routes", "버전별 확인 필요"),
}, keys="ospf 경로 route 라우팅 테이블")

add("bgp-show", "bgp", "show", "BGP 이웃 상태 보기", {
    "c": "show ip bgp summary",
    "j": "show bgp summary",
    "a": "show ip bgp summary",
    "o6": "show ip bgp neighbors",
    "o8": "show ip bgp neighbors",
}, keys="bgp 이웃 neighbor summary established")

add("vrrp", "fhrp", "config", "VRRP 게이트웨이 이중화", {
    "c": ("interface vlan <VLAN번호>\n vrrp <그룹> ip <가상IP>\n vrrp <그룹> priority 110\n vrrp <그룹> preempt",
          "priority 높은 쪽이 Master. IOS-XE 16 이상 일부는 vrrp <그룹> address-family ipv4 방식(VRRPv3)"),
    "j": ("set interfaces irb unit <VLAN번호> family inet address <IP>/<프리픽스> vrrp-group <그룹> virtual-address <가상IP>\n"
          "set interfaces irb unit <VLAN번호> family inet address <IP>/<프리픽스> vrrp-group <그룹> priority 110\n"
          "set interfaces irb unit <VLAN번호> family inet address <IP>/<프리픽스> vrrp-group <그룹> accept-data",
          "<IP> 는 이 장비의 실제 IP. accept-data 를 넣어야 가상 IP 로 ping 이 됩니다"),
    "a": ("router vrrp <그룹> vlan<VLAN번호>\n virtual-ip <가상IP> backup\n priority 110\n enable",
          "가상 IP 가 이 장비의 실제 IP 와 같으면 backup 대신 master"),
    "o6": ("vrrp <그룹> <VLAN번호>\nvrrp <그룹> <VLAN번호> ip <가상IP>\nvrrp <그룹> <VLAN번호> priority 110\nvrrp <그룹> <VLAN번호> enable",
           "값을 바꿀 때는 먼저 vrrp <그룹> <VLAN번호> disable"),
    "o8": ("vrrp <그룹> <VLAN번호>\nvrrp <그룹> <VLAN번호> address <가상IP>\nvrrp <그룹> <VLAN번호> priority 110\nvrrp <그룹> <VLAN번호> admin-state enable",
           "버전별 확인 필요. 값을 바꿀 때는 먼저 admin-state disable"),
}, desc="두 L3 스위치가 같은 가상 IP 를 나눠 갖고, PC 게이트웨이를 가상 IP 로 잡습니다. 양쪽 다 넣고 priority 만 다르게.",
   keys="vrrp 게이트웨이 이중화 가상 ip master backup 마스터 백업 failover")

add("vrrp-show", "fhrp", "show", "VRRP 상태 보기 (Master/Backup)", {
    "c": "show vrrp brief",
    "j": "show vrrp summary",
    "a": "show vrrp",
    "o6": "show vrrp",
    "o8": "show vrrp",
}, keys="vrrp 상태 master backup 확인")

add("hsrp", "fhrp", "config", "HSRP 게이트웨이 이중화 (시스코 전용)", {
    "c": ("interface vlan <VLAN번호>\n standby <그룹> ip <가상IP>\n standby <그룹> priority 110\n standby <그룹> preempt",
          "priority 높은 쪽이 Active. 다른 벤더와 섞여 있으면 VRRP 를 쓰세요"),
    "j": (None, "HSRP 는 시스코 전용입니다. 같은 일은 VRRP 로"),
    "a": (None, "HSRP 는 시스코 전용입니다. 같은 일은 VRRP 로"),
    "o6": (None, "HSRP 는 시스코 전용입니다. 같은 일은 VRRP 로"),
    "o8": (None, "HSRP 는 시스코 전용입니다. 같은 일은 VRRP 로"),
}, keys="hsrp standby 게이트웨이 이중화 active standby 가상 ip")

add("hsrp-show", "fhrp", "show", "HSRP 상태 보기", {
    "c": "show standby brief",
    "j": (None, "HSRP 없음. VRRP 는 show vrrp summary"),
    "a": (None, "HSRP 없음. VRRP 는 show vrrp"),
    "o6": (None, "HSRP 없음. VRRP 는 show vrrp"),
    "o8": (None, "HSRP 없음. VRRP 는 show vrrp"),
}, keys="hsrp standby 상태 active")

add("dhcp-relay", "l3", "config", "DHCP 릴레이 (다른 대역의 DHCP 서버로 넘기기)", {
    "c": "interface vlan <VLAN번호>\n ip helper-address <서버IP>",
    "j": ("set forwarding-options dhcp-relay server-group DHCP-SRV <서버IP>\n"
          "set forwarding-options dhcp-relay group RELAY active-server-group DHCP-SRV\n"
          "set forwarding-options dhcp-relay group RELAY interface irb.<VLAN번호>"),
    "a": "service dhcp-relay\ninterface vlan<VLAN번호>\n ip dhcp-relay server-address <서버IP>",
    "o6": ("ip helper address <서버IP>", "장비 전체에 걸립니다"),
    "o8": ("ip helper address <서버IP>", "버전에 따라 ip dhcp relay 명령으로 바뀐 경우가 있어 확인 필요"),
}, keys="dhcp 릴레이 relay helper 헬퍼 ip helper-address 서버")

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

add("ssh-on", "remote", "config", "SSH 켜기", {
    "c": ("hostname <이름>\nip domain-name <도메인>\ncrypto key generate rsa modulus 2048\nip ssh version 2\nusername <사용자> privilege 15 secret <비밀번호>\nline vty 0 15\n login local\n transport input ssh",
          "키를 만들려면 hostname·domain-name 이 먼저 있어야 합니다. transport input ssh 는 텔넷을 막습니다"),
    "j": "set system services ssh",
    "a": "crypto key generate hostkey rsa 2048\nservice ssh",
    "o6": "aaa authentication ssh local",
    "o8": "aaa authentication ssh local",
}, keys="ssh 켜기 암호화 원격 접속 vty")

add("telnet-off", "remote", "config", "텔넷 끄기", {
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

# ═════════════════════ 1.1.0 (2): L3 추가·OSPF·BGP·RIP·EIGRP·멀티캐스트 ═════════════════════
AOS_LOAD = "AOS 는 라우팅 프로토콜을 쓰기 전에 ip load <프로토콜> 로 올립니다"
VER = "버전별 확인 필요"

# ── IP·정적 라우팅·DHCP
add("loopback", "l3", "config", "루프백 주소 만들기 (라우터 ID 용)", {
    "c": "interface Loopback0\n ip address <IP> 255.255.255.255",
    "j": "set interfaces lo0 unit 0 family inet address <IP>/32",
    "a": "interface lo\n ip address <IP>/32",
    "o6": "ip interface Loopback0 address <IP>",
    "o8": "ip interface Loopback0 address <IP>",
}, keys="루프백 loopback lo0 라우터 id")

add("router-id", "l3", "config", "라우터 ID 정하기", {
    "c": ("router ospf 1\n router-id <라우터ID>", "BGP 는 router bgp <AS번호> 아래 bgp router-id <라우터ID>"),
    "j": "set routing-options router-id <라우터ID>",
    "a": ("router ospf\n ospf router-id <라우터ID>", "BGP 는 router bgp <AS번호> 아래 bgp router-id <라우터ID>"),
    "o6": "ip router router-id <라우터ID>",
    "o8": "ip router router-id <라우터ID>",
}, desc="정하지 않으면 장비가 IP 중 하나를 골라 쓰는데, 그 IP 가 바뀌면 이웃이 다시 맺어집니다. 루프백 주소로 고정해 두세요.",
   keys="router-id 라우터 id 아이디 ospf bgp")

add("dhcp-show", "l3", "show", "DHCP 릴레이 설정 보기", {
    "c": "show ip interface vlan <VLAN번호> | include Helper",
    "j": "show dhcp relay binding",
    "a": ("show ip dhcp-relay", VER),
    "o6": "show ip helper",
    "o8": ("show ip helper", VER),
}, keys="dhcp 릴레이 relay 확인 helper")

add("route-null", "l3", "config", "블랙홀(Null) 경로 만들기", {
    "c": "ip route <대역> <마스크> Null0",
    "j": "set routing-options static route <대역>/<프리픽스> discard",
    "a": ("ip route <대역>/<프리픽스> null", VER),
    "o6": (None, "공식 문서 확인 필요"),
    "o8": (None, "공식 문서 확인 필요"),
}, keys="null 블랙홀 discard 요약 경로")

# ── OSPF
add("ospf-passive", "ospf", "config", "OSPF 이웃을 맺지 않을 인터페이스 (passive)", {
    "c": "router ospf 1\n passive-interface vlan <VLAN번호>",
    "j": "set protocols ospf area 0.0.0.0 interface irb.<VLAN번호> passive",
    "a": "router ospf\n passive-interface vlan<VLAN번호>",
    "o6": ('ip ospf interface "vlan<VLAN번호>" type passive', VER),
    "o8": ('ip ospf interface "vlan<VLAN번호>" passive', VER),
}, desc="PC 만 있는 VLAN 은 대역은 광고하되, OSPF 패킷은 내보내지 않게 막아 둡니다.",
   keys="passive 패시브 ospf 인터페이스 막기")

add("ospf-cost", "ospf", "config", "OSPF 비용(cost) 바꾸기", {
    "c": "interface vlan <VLAN번호>\n ip ospf cost <비용>",
    "j": "set protocols ospf area 0.0.0.0 interface irb.<VLAN번호> metric <비용>",
    "a": "interface vlan<VLAN번호>\n ip ospf cost <비용>",
    "o6": 'ip ospf interface "vlan<VLAN번호>" cost <비용>',
    "o8": 'ip ospf interface "vlan<VLAN번호>" cost <비용>',
}, desc="비용이 낮은 쪽으로 트래픽이 갑니다. 두 경로 중 하나를 예비로 두고 싶으면 그쪽 비용을 올리세요.",
   keys="ospf cost 비용 metric 경로 선택 우선")

add("ospf-default", "ospf", "config", "OSPF 로 기본 경로(0.0.0.0/0) 뿌리기", {
    "c": "router ospf 1\n default-information originate",
    "j": ("set policy-options policy-statement OSPF-DEFAULT term 1 from route-filter 0.0.0.0/0 exact\n"
          "set policy-options policy-statement OSPF-DEFAULT term 1 then accept\n"
          "set protocols ospf export OSPF-DEFAULT", "기본 경로(정적)가 라우팅 표에 있어야 합니다"),
    "a": "router ospf\n default-information originate",
    "o6": (None, "AOS 는 route-map 으로 재분배합니다. 공식 문서 확인 필요"),
    "o8": (None, "AOS 는 route-map 으로 재분배합니다. 공식 문서 확인 필요"),
}, desc="인터넷 쪽 기본 경로를 가진 코어에서 아래 장비들로 뿌릴 때 씁니다.",
   keys="ospf default 기본 경로 originate 디폴트")

add("ospf-redist", "ospf", "config", "정적·직접 연결 경로를 OSPF 로 재분배", {
    "c": "router ospf 1\n redistribute static subnets\n redistribute connected subnets",
    "j": ("set policy-options policy-statement TO-OSPF term 1 from protocol [ static direct ]\n"
          "set policy-options policy-statement TO-OSPF term 1 then accept\n"
          "set protocols ospf export TO-OSPF", None),
    "a": "router ospf\n redistribute static\n redistribute connected",
    "o6": ("ip route-map <이름> action permit\nip redist static into ospf route-map <이름> status enable", VER),
    "o8": ("ip route-map <이름> action permit\nip redist static into ospf route-map <이름> admin-state enable", VER),
}, keys="재분배 redistribute redist static connected ospf")

add("ospf-db", "ospf", "show", "OSPF 데이터베이스(LSDB) 보기", {
    "c": "show ip ospf database",
    "j": "show ospf database",
    "a": "show ip ospf database",
    "o6": "show ip ospf lsdb",
    "o8": "show ip ospf lsdb",
}, keys="ospf lsdb database lsa 데이터베이스")

# ── BGP
add("bgp-enable", "bgp", "config", "BGP 켜고 이웃 맺기", {
    "c": "router bgp <AS번호>\n bgp router-id <라우터ID>\n neighbor <이웃IP> remote-as <상대AS>",
    "j": ("set routing-options autonomous-system <AS번호>\n"
          "set protocols bgp group <그룹이름> type external\n"
          "set protocols bgp group <그룹이름> peer-as <상대AS>\n"
          "set protocols bgp group <그룹이름> neighbor <이웃IP>", "같은 AS 끼리(iBGP)면 type internal, peer-as 없이"),
    "a": ("router bgp <AS번호>\n bgp router-id <라우터ID>\n neighbor <이웃IP> remote-as <상대AS>", "모델에 따라 BGP 기능 라이선스가 필요할 수 있습니다"),
    "o6": ("ip load bgp\nip bgp autonomous-system <AS번호>\nip bgp neighbor <이웃IP>\nip bgp neighbor <이웃IP> remote-as <상대AS>\n"
           "ip bgp neighbor <이웃IP> status enable\nip bgp status enable", "AS 번호를 바꾸려면 먼저 ip bgp status disable. " + AOS_LOAD),
    "o8": ("ip load bgp\nip bgp autonomous-system <AS번호>\nip bgp neighbor <이웃IP>\nip bgp neighbor <이웃IP> remote-as <상대AS>\n"
           "ip bgp neighbor <이웃IP> admin-state enable\nip bgp admin-state enable", VER),
}, keys="bgp 비지피 이웃 neighbor remote-as as 번호 피어 peer ebgp ibgp")

add("bgp-network", "bgp", "config", "BGP 로 내 대역 광고하기", {
    "c": ("router bgp <AS번호>\n network <대역> mask <마스크>", "라우팅 표에 똑같은 대역이 있어야 광고됩니다"),
    "j": ("set policy-options policy-statement BGP-OUT term 1 from route-filter <대역>/<프리픽스> exact\n"
          "set policy-options policy-statement BGP-OUT term 1 then accept\n"
          "set protocols bgp group <그룹이름> export BGP-OUT", None),
    "a": "router bgp <AS번호>\n network <대역>/<프리픽스>",
    "o6": "ip bgp network <대역> <마스크>\nip bgp network <대역> <마스크> status enable",
    "o8": ("ip bgp network <대역> <마스크>\nip bgp network <대역> <마스크> admin-state enable", VER),
}, keys="bgp network 광고 advertise 대역")

add("bgp-neighbor", "bgp", "show", "BGP 이웃 하나 자세히 보기", {
    "c": "show ip bgp neighbors <이웃IP>",
    "j": "show bgp neighbor <이웃IP>",
    "a": "show ip bgp neighbors <이웃IP>",
    "o6": "show ip bgp neighbors <이웃IP>",
    "o8": "show ip bgp neighbors <이웃IP>",
}, keys="bgp neighbor 이웃 자세히 detail")

add("bgp-table", "bgp", "show", "BGP 경로 표 보기", {
    "c": "show ip bgp",
    "j": "show route protocol bgp",
    "a": "show ip bgp",
    "o6": "show ip bgp path",
    "o8": "show ip bgp path",
}, keys="bgp table 경로 표 path 라우트")

add("bgp-adv", "bgp", "show", "이웃에게 보낸 경로 / 받은 경로 보기", {
    "c": ("show ip bgp neighbors <이웃IP> advertised-routes\nshow ip bgp neighbors <이웃IP> routes",
          "received-routes 는 soft-reconfiguration inbound 가 있어야 보입니다"),
    "j": "show route advertising-protocol bgp <이웃IP>\nshow route receive-protocol bgp <이웃IP>",
    "a": "show ip bgp neighbors <이웃IP> advertised-routes\nshow ip bgp neighbors <이웃IP> routes",
    "o6": (None, "show ip bgp path 에서 확인"),
    "o8": (None, "show ip bgp path 에서 확인"),
}, keys="bgp advertised received 광고 받은 보낸 경로")

add("bgp-clear", "bgp", "exec", "BGP 경로 다시 주고받기 (soft clear)", {
    "c": "clear ip bgp <이웃IP> soft",
    "j": "clear bgp neighbor <이웃IP> soft",
    "a": "clear ip bgp <이웃IP> soft",
    "o6": ("ip bgp neighbor <이웃IP> clear soft", VER),
    "o8": ("ip bgp neighbor <이웃IP> clear soft", VER),
}, desc="soft 를 빼면 세션이 끊겼다 다시 맺어집니다(서비스 끊김). 정책을 바꾼 뒤에는 soft 로 하세요.",
   keys="bgp clear 리셋 soft 다시 갱신")

add("bgp-shut", "bgp", "config", "BGP 이웃 잠시 끊기", {
    "c": "router bgp <AS번호>\n neighbor <이웃IP> shutdown",
    "j": "deactivate protocols bgp group <그룹이름> neighbor <이웃IP>",
    "a": "router bgp <AS번호>\n neighbor <이웃IP> shutdown",
    "o6": "ip bgp neighbor <이웃IP> status disable",
    "o8": "ip bgp neighbor <이웃IP> admin-state disable",
}, keys="bgp shutdown 끊기 비활성 deactivate 이웃")

# ── RIP·EIGRP
add("rip-enable", "rip", "config", "RIP v2 켜기", {
    "c": "router rip\n version 2\n network <대역>\n no auto-summary",
    "j": ("set protocols rip group <그룹이름> neighbor irb.<VLAN번호>", "알릴 경로는 export 정책으로 정합니다"),
    "a": "router rip\n version 2\n network <대역>/<프리픽스>",
    "o6": ('ip load rip\nip rip interface "vlan<VLAN번호>"\nip rip interface "vlan<VLAN번호>" status enable\nip rip status enable', AOS_LOAD),
    "o8": ('ip load rip\nip rip interface "vlan<VLAN번호>"\nip rip interface "vlan<VLAN번호>" admin-state enable\nip rip admin-state enable', VER),
}, keys="rip 립 라우팅 동적 version 2")

add("rip-show", "rip", "show", "RIP 경로·이웃 보기", {
    "c": ("show ip rip database", "경로만: show ip route rip"),
    "j": ("show rip neighbor", "경로만: show route protocol rip"),
    "a": ("show ip rip", "경로만: show ip route rip"),
    "o6": "show ip rip routes",
    "o8": "show ip rip routes",
}, keys="rip 확인 경로 database")

add("eigrp-enable", "rip", "config", "EIGRP 켜기 (시스코 전용)", {
    "c": "router eigrp <AS번호>\n network <대역> <와일드카드>\n no auto-summary",
    "j": (None, "EIGRP 는 시스코 전용입니다. 같은 일은 OSPF 로"),
    "a": (None, "EIGRP 는 시스코 전용입니다. 같은 일은 OSPF 로"),
    "o6": (None, "EIGRP 는 시스코 전용입니다. 같은 일은 OSPF 로"),
    "o8": (None, "EIGRP 는 시스코 전용입니다. 같은 일은 OSPF 로"),
}, keys="eigrp 이그알피 시스코 라우팅")

add("eigrp-show", "rip", "show", "EIGRP 이웃·경로 보기 (시스코 전용)", {
    "c": ("show ip eigrp neighbors", "경로만: show ip route eigrp"),
    "j": (None, "EIGRP 는 시스코 전용"),
    "a": (None, "EIGRP 는 시스코 전용"),
    "o6": (None, "EIGRP 는 시스코 전용"),
    "o8": (None, "EIGRP 는 시스코 전용"),
}, keys="eigrp 이웃 확인")

# ── 멀티캐스트
add("igmp-snoop", "mcast", "config", "IGMP 스누핑 켜기", {
    "c": ("ip igmp snooping\nip igmp snooping vlan <VLAN번호>", "보통 기본으로 켜져 있음"),
    "j": "set protocols igmp-snooping vlan <이름>",
    "a": ("interface vlan<VLAN번호>\n ip igmp snooping", "보통 기본으로 켜져 있음"),
    "o6": ("ip multicast status enable", "VLAN 별: ip multicast vlan <VLAN번호> status enable"),
    "o8": ("ip multicast admin-state enable", "VLAN 별: ip multicast vlan <VLAN번호> admin-state enable"),
}, desc="멀티캐스트(IPTV·CCTV 스트림 등)를 받겠다는 포트에만 보냅니다. 끄면 VLAN 전체로 퍼집니다.",
   keys="igmp snooping 스누핑 멀티캐스트 multicast iptv cctv")

add("igmp-querier", "mcast", "config", "IGMP 질의자(querier) 켜기 (라우터 없는 L2 망)", {
    "c": "ip igmp snooping querier",
    "j": ("set protocols igmp-snooping vlan <이름> l2-querier source-address <IP>", VER),
    "a": (None, "버전별로 다름. 공식 문서 확인 필요"),
    "o6": ("ip multicast vlan <VLAN번호> querying enable", VER),
    "o8": ("ip multicast vlan <VLAN번호> querying enable", VER),
}, desc="멀티캐스트 라우터(PIM)가 없는 망은 질의자가 없으면 스누핑 표가 시간이 지나 사라져 영상이 끊길 수 있습니다.",
   keys="querier 질의자 igmp query 쿼리어 l2")

add("igmp-groups", "mcast", "show", "멀티캐스트 그룹·가입한 포트 보기", {
    "c": ("show ip igmp snooping groups", "L3(라우터) 쪽: show ip igmp groups"),
    "j": ("show igmp snooping membership", "L3 쪽: show igmp group"),
    "a": ("show ip igmp groups", VER),
    "o6": "show ip multicast group",
    "o8": "show ip multicast group",
}, keys="igmp 그룹 group 가입 membership 멀티캐스트 확인")

add("mcast-routing", "mcast", "config", "멀티캐스트 라우팅 켜기", {
    "c": ("ip multicast-routing", "일부 장비(3850 등)는 ip multicast-routing distributed"),
    "j": (None, "PIM 을 켜면 됩니다"),
    "a": "ip multicast-routing",
    "o6": ("ip load pim", "PIM 을 쓰려면 먼저 올립니다"),
    "o8": ("ip load pim", VER),
}, keys="멀티캐스트 라우팅 multicast-routing 켜기")

add("pim-sm", "mcast", "config", "인터페이스에 PIM-SM 켜기", {
    "c": "interface vlan <VLAN번호>\n ip pim sparse-mode",
    "j": "set protocols pim interface irb.<VLAN번호> mode sparse",
    "a": ("interface vlan<VLAN번호>\n ip pim sparse-mode\n ip igmp", "IGMP 도 같이 켭니다"),
    "o6": 'ip pim interface "vlan<VLAN번호>"\nip pim sparse status enable',
    "o8": ('ip pim interface "vlan<VLAN번호>"\nip pim sparse admin-state enable', VER),
}, keys="pim sparse sm 멀티캐스트 라우팅 인터페이스")

add("pim-rp", "mcast", "config", "PIM RP 주소 정하기 (static RP)", {
    "c": "ip pim rp-address <RP주소>",
    "j": "set protocols pim rp static address <RP주소>",
    "a": "ip pim rp-address <RP주소>",
    "o6": ("ip pim static-rp 224.0.0.0/4 <RP주소>", "static-rp 를 따로 켜야 하는 버전도 있습니다"),
    "o8": ("ip pim static-rp 224.0.0.0/4 <RP주소>", VER),
}, desc="모든 PIM 라우터에 같은 RP 주소를 넣습니다. 보통 코어의 루프백 주소.",
   keys="rp rendezvous static rp pim 멀티캐스트")

add("pim-show", "mcast", "show", "PIM 이웃 보기", {
    "c": "show ip pim neighbor",
    "j": "show pim neighbors",
    "a": "show ip pim sparse-mode neighbor",
    "o6": "show ip pim neighbor",
    "o8": "show ip pim neighbor",
}, keys="pim 이웃 neighbor 확인")

add("mroute", "mcast", "show", "멀티캐스트 라우팅 표 보기", {
    "c": "show ip mroute",
    "j": "show multicast route",
    "a": "show ip mroute",
    "o6": "show ip mroute",
    "o8": "show ip mroute",
}, keys="mroute 멀티캐스트 라우팅 표 경로")

# 분야 안에서 보여 줄 순서 (적힌 것 먼저, 나머지는 넣은 순서)
ORDER = ["ssh-on", "telnet-off", "telnet-on", "ssh-show", "ssh-client", "session-kill", "vty-acl", "session-timeout",
         "ospf", "ospf-passive", "ospf-cost", "ospf-default", "ospf-redist", "ospf-nbr", "ospf-intf", "ospf-db", "ospf-route",
         "bgp-enable", "bgp-network", "bgp-shut", "bgp-show", "bgp-neighbor", "bgp-table", "bgp-adv", "bgp-clear",
         "igmp-snoop", "igmp-querier", "igmp-groups", "mcast-routing", "pim-sm", "pim-rp", "pim-show", "mroute"]


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
        "entries": [{**e, "v": norm(e["v"])} for e in sorted(E, key=lambda e: (ORDER.index(e["id"]) if e["id"] in ORDER else 999))],
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
