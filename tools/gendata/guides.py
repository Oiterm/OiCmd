"""OiCmd 따라하기(작업 순서) 데이터 — commands.py 가 불러서 commands.json 의 "guides" 로 넣는다.

guide(id, 분야, 제목, 설명, {벤더: V([...단계], check=[...], undo=[...], note="")}, ...)
  단계·확인·되돌리기 = (명령어, 이 명령이 하는 일) 튜플. 명령어가 여러 줄이면 하위 모드 줄은 앞에 공백 한 칸.
  벤더 값이 (None, "이유") 면 그 벤더는 이 작업이 없거나 다른 방법.
mode   config: 앞에 설정 모드 들어가기, 뒤에 저장 단계를 자동으로 붙임
       remote: config 와 같고, 주니퍼는 commit confirmed 로 (원격 접속이 끊길 수 있는 작업)
       show:   조회·점검 순서만 (자동으로 붙이는 것 없음)
<자리>  화면에서 한 번 넣으면 모든 따라하기에 같이 채워진다. 같은 뜻이면 같은 이름을 쓴다(HINTS 에 예시).

명령어는 사전(commands.py)과 같은 공식 문서 기준. 확실하지 않은 벤더는 note 에 "버전별 확인 필요".
"""

VER = "버전별 확인 필요"
AOS_LOAD = "AOS 는 라우팅 프로토콜을 쓰기 전에 ip load 로 올립니다"

# 자리 이름 → 입력칸에 보여 줄 예시 (포트 계열은 화면에서 벤더 형식으로 보여 줌)
HINTS = {
    "장비이름": "SW-3F-01", "사용자": "admin", "비밀번호": "", "도메인": "lab.local",
    "관리VLAN": "99", "관리IP": "10.0.99.13", "마스크": "255.255.255.0", "프리픽스": "24", "게이트웨이": "10.0.99.1",
    "관리대역": "10.0.99.0", "관리와일드카드": "0.0.0.255", "관리프리픽스": "24",
    "VLAN번호": "10", "VLAN이름": "OFFICE", "VLAN목록": "10,20,99", "VLAN이름목록": "OFFICE CCTV MGMT", "네이티브VLAN": "1",
    "음성VLAN": "30", "음성VLAN이름": "VOICE",
    "묶음번호": "1", "게이트웨이IP": "10.0.10.1", "상위장비IP": "10.0.0.1",
    "대역": "10.0.10.0", "와일드카드": "0.0.0.255", "시작IP": "10.0.10.100", "끝IP": "10.0.10.200",
    "제외시작": "10.0.10.1", "제외끝": "10.0.10.99", "풀이름": "POOL-10", "DNS": "8.8.8.8",
    "NTP서버": "10.0.99.5", "로그서버": "10.0.99.5", "NMS서버": "10.0.99.6", "커뮤니티": "oi-read",
    "SNMP사용자": "nms", "SNMP그룹": "NMSGRP", "인증비밀번호": "", "암호비밀번호": "",
    "DHCP서버": "10.0.1.10", "인증서버": "10.0.99.20", "비밀키": "", "서버이름": "RAD1",
    "루프백IP": "10.255.0.1", "라우터ID": "10.255.0.1", "AS번호": "65001", "상대AS": "65002", "이웃IP": "10.0.0.2",
    "광고대역": "10.0.10.0", "광고마스크": "255.255.255.0", "광고프리픽스": "24", "그룹이름": "ISP",
    "가상IP": "10.0.10.1", "실제IP": "10.0.10.2", "우선순위": "110", "그룹": "1",
    "RP주소": "10.255.0.1", "막을IP": "10.0.10.50", "서버IP": "10.0.1.10", "서비스포트": "23", "ACL이름": "BLOCK-PC",
    "속도": "100M", "받는포트": "", "분석이름": "CAP1", "최대MAC": "2", "TFTP서버": "10.0.99.5", "파일": "SW-3F-01.cfg",
    "대상IP": "10.0.10.50", "MAC": "",
}

# 설정 모드 들어가기 / 나와서 저장 (mode config·remote 에 자동으로 붙음)
ENTER = {
    "c": [("enable", "관리자 모드로 들어갑니다. 프롬프트 끝이 > 에서 # 로 바뀝니다"),
          ("configure terminal", "설정 모드로 들어갑니다. 프롬프트가 (config)# 로 바뀝니다. 이제부터 치는 줄은 바로 적용됩니다")],
    "j": [("configure", "설정 모드로 들어갑니다. 프롬프트가 # 로 바뀝니다. set 으로 친 것은 commit 하기 전까지 적용되지 않습니다")],
    "a": [("enable", "관리자 모드로 들어갑니다. 프롬프트 끝이 > 에서 # 로 바뀝니다"),
          ("configure terminal", "설정 모드로 들어갑니다. 프롬프트가 (config)# 로 바뀝니다. 이제부터 치는 줄은 바로 적용됩니다")],
    "o6": [], "o8": [],
}
SAVE = {
    "c": [("end", "설정 모드에서 나와 # 으로 돌아갑니다"),
          ("write memory", "지금 설정을 저장합니다(startup-config). 안 하면 재부팅 때 사라집니다")],
    "j": [("show | compare", "commit 전에 바꾼 내용을 확인합니다. + 는 추가, - 는 지워지는 줄"),
          ("commit", "바꾼 내용을 한꺼번에 적용하고 저장합니다. 틀린 곳이 있으면 여기서 오류가 나고 아무것도 적용되지 않습니다"),
          ("exit", "설정 모드에서 나옵니다")],
    "a": [("end", "설정 모드에서 나와 # 으로 돌아갑니다"),
          ("write", "지금 설정을 저장합니다(startup-config). 안 하면 재부팅 때 사라집니다")],
    "o6": [("write memory", "지금 설정을 working 폴더에 저장합니다"),
           ("copy working certified", "working 을 certified 로 복사합니다. 이것까지 해야 재부팅 뒤에도 확실히 남습니다")],
    "o8": [("write memory flash-synchro", "저장(working)과 certified 복사를 한 번에 합니다")],
}
SAVE_REMOTE_J = [
    ("show | compare", "commit 전에 바꾼 내용을 확인합니다"),
    ("commit confirmed 5", "적용하되, 5분 안에 다시 commit 하지 않으면 자동으로 되돌립니다. 접속이 끊겨도 5분 뒤 원래대로 돌아옵니다"),
    ("commit", "새 창으로 다시 접속되는 것을 확인한 다음 한 번 더 commit 해서 확정합니다"),
    ("exit", "설정 모드에서 나옵니다"),
]

G = []


def V(steps, check=(), undo=(), note=""):
    return {"steps": list(steps), "check": list(check), "undo": list(undo), "note": note}


def guide(id, cat, t, d, v, keys="", warn="", rel=(), mode="config"):
    G.append({"id": id, "cat": cat, "t": t, "d": d, "k": keys, "warn": warn, "rel": list(rel), "mode": mode, "v": v})


NO_HSRP = (None, "HSRP 는 시스코 전용입니다. 같은 일은 'VRRP 게이트웨이 이중화' 따라하기로 하세요")
NO_EIGRP = (None, "EIGRP 는 시스코 전용입니다. 같은 일은 'OSPF 기본' 따라하기로 하세요")

# ═══════════════════════════ 처음 설정·관리 ═══════════════════════════
guide("g-init", "mgmt", "새 장비 첫 설정 (이름·계정·관리 IP·게이트웨이)",
      "박스에서 꺼낸 스위치에 콘솔로 붙어서 원격으로 들어올 수 있게 만드는 기본 순서입니다.", {
    "c": V([
        ("hostname <장비이름>", "장비 이름을 정합니다. 프롬프트가 바로 바뀌어서 어느 장비에 붙었는지 알기 쉽습니다"),
        ("username <사용자> privilege 15 secret <비밀번호>", "관리자 계정을 만듭니다. privilege 15 = 최고 권한, secret = 비밀번호를 암호화(해시)해서 저장"),
        ("enable secret <비밀번호>", "enable(관리자 모드) 들어갈 때 묻는 비밀번호입니다"),
        ("vlan <관리VLAN>\n name MGMT", "관리용 VLAN 을 만들고 이름을 붙입니다"),
        ("interface vlan <관리VLAN>\n ip address <관리IP> <마스크>\n no shutdown", "관리 VLAN 에 장비 IP(SVI)를 줍니다. SVI 는 기본으로 꺼져 있어 no shutdown 이 필요합니다"),
        ("ip default-gateway <게이트웨이>", "다른 대역에서 이 장비로 들어올 수 있게 게이트웨이를 정합니다 (L2 스위치용. ip routing 켠 L3 는 ip route 0.0.0.0 0.0.0.0)"),
    ], check=[("show ip interface brief", "Vlan<관리VLAN> 이 up/up 인지, IP 가 맞는지"),
              ("ping <게이트웨이>", "게이트웨이까지 통신 되는지")],
       note="관리 VLAN 이 업링크 포트(트렁크)에 허용돼 있어야 밖에서 들어옵니다. SSH 는 'SSH 설정' 따라하기"),
    "j": V([
        ("set system host-name <장비이름>", "장비 이름을 정합니다 (commit 후 프롬프트에 반영)"),
        ("set system root-authentication plain-text-password", "root 비밀번호를 정합니다. 엔터를 치면 두 번 묻습니다. 공장 초기 상태에서는 이게 없으면 commit 이 안 됩니다"),
        ("set system login user <사용자> class super-user authentication plain-text-password", "관리자 계정을 만듭니다. super-user = 최고 권한. 엔터를 치면 비밀번호를 두 번 묻습니다"),
        ("set vlans MGMT vlan-id <관리VLAN>", "관리용 VLAN 을 만듭니다. 주니퍼는 VLAN 을 이름(MGMT)으로 다룹니다"),
        ("set interfaces irb unit <관리VLAN> family inet address <관리IP>/<프리픽스>", "VLAN 용 IP 인터페이스(irb)에 장비 IP 를 줍니다"),
        ("set vlans MGMT l3-interface irb.<관리VLAN>", "만든 irb 를 MGMT VLAN 에 연결합니다. 이 줄이 없으면 IP 가 VLAN 과 이어지지 않습니다"),
        ("set routing-options static route 0.0.0.0/0 next-hop <게이트웨이>", "기본 경로(게이트웨이)를 넣습니다"),
    ], check=[("show interfaces terse irb", "irb.<관리VLAN> 이 up 인지, IP 가 맞는지"),
              ("ping <게이트웨이> count 5", "게이트웨이까지 통신 되는지")]),
    "a": V([
        ("hostname <장비이름>", "장비 이름을 정합니다"),
        ("username <사용자> privilege 15 password <비밀번호>", "관리자 계정을 만듭니다. 기본 계정 manager(비번 friend)는 계정을 만든 뒤 지우거나 비밀번호를 바꾸세요"),
        ("vlan database\n vlan <관리VLAN> name MGMT", "VLAN 은 vlan database 모드에서 만듭니다"),
        ("interface vlan<관리VLAN>\n ip address <관리IP>/<프리픽스>", "관리 VLAN 에 장비 IP 를 줍니다. AW+ 는 /24 처럼 프리픽스로 씁니다"),
        ("ip route 0.0.0.0/0 <게이트웨이>", "기본 경로(게이트웨이)를 넣습니다"),
    ], check=[("show ip interface brief", "vlan<관리VLAN> 이 up 인지"), ("ping <게이트웨이>", "게이트웨이까지 통신 되는지")]),
    "o6": V([
        ('system name "<장비이름>"', "장비 이름을 정합니다"),
        ("user <사용자> password <비밀번호> read-write all", "관리자 계정을 만듭니다. read-write all = 모든 기능 읽기·쓰기. 기본 계정 admin(비번 switch)은 비밀번호를 바꾸세요"),
        ('vlan <관리VLAN> name "MGMT"', "관리용 VLAN 을 만듭니다"),
        ('ip interface "vlan<관리VLAN>" address <관리IP> mask <마스크> vlan <관리VLAN>', "IP 인터페이스를 만들어 관리 VLAN 에 붙입니다. 따옴표 안 이름은 마음대로 정해도 됩니다"),
        ("ip static-route 0.0.0.0 mask 0.0.0.0 gateway <게이트웨이>", "기본 경로(게이트웨이)를 넣습니다"),
    ], check=[("show ip interface", "IP 와 상태 확인"), ("ping <게이트웨이>", "게이트웨이까지 통신 되는지")]),
    "o8": V([
        ('system name "<장비이름>"', "장비 이름을 정합니다"),
        ("user <사용자> password <비밀번호> read-write all", "관리자 계정을 만듭니다. 기본 계정 admin(비번 switch)은 비밀번호를 바꾸세요"),
        ('vlan <관리VLAN> admin-state enable name "MGMT"', "관리용 VLAN 을 만들고 켭니다"),
        ('ip interface "vlan<관리VLAN>" address <관리IP> mask <마스크> vlan <관리VLAN>', "IP 인터페이스를 만들어 관리 VLAN 에 붙입니다"),
        ("ip static-route 0.0.0.0/0 gateway <게이트웨이>", "기본 경로(게이트웨이)를 넣습니다"),
    ], check=[("show ip interface", "IP 와 상태 확인"), ("ping <게이트웨이>", "게이트웨이까지 통신 되는지")]),
}, keys="초기 설정 처음 신규 장비 기본 세팅 관리 ip hostname 계정 게이트웨이 초기화 후", rel=["hostname", "user-add", "svi", "default-gw"])

guide("g-ssh", "remote", "SSH 설정 (텔넷 끄고 SSH 로만 접속)",
      "보안 점검 단골 항목입니다. 계정 → 키 → SSH 켜기 → 텔넷 끄기 순서로 합니다.", {
    "c": V([
        ("hostname <장비이름>", "RSA 키 이름에 hostname 이 들어갑니다. 기본 이름(Switch)이면 키 생성이 거부됩니다"),
        ("ip domain-name <도메인>", "키 이름은 hostname.domain 으로 만들어져서 도메인도 먼저 있어야 합니다. 아무 이름이나 괜찮습니다"),
        ("crypto key generate rsa modulus 2048", "SSH 에 쓸 RSA 키를 만듭니다. 키가 생기는 순간 SSH 서버가 켜집니다. 2048 미만은 보안 점검에 걸립니다"),
        ("ip ssh version 2", "취약한 SSH v1 을 막고 v2 만 씁니다. 키를 만든 뒤에 쳐야 합니다"),
        ("username <사용자> privilege 15 secret <비밀번호>", "SSH 로 로그인할 로컬 계정입니다. 이미 있으면 건너뛰세요"),
        ("line vty 0 15", "원격 접속 줄(vty) 0~15번 설정으로 들어갑니다. 동시에 16명까지 접속할 수 있다는 뜻"),
        (" login local", "원격 접속할 때 위에서 만든 로컬 계정(username)으로 로그인하게 합니다"),
        (" transport input ssh", "vty 로는 SSH 만 받습니다. 텔넷이 막힙니다 (지금 텔넷으로 붙어 있으면 다음 접속부터 막힘)"),
    ], check=[("show ip ssh", "SSH Enabled - version 2.0 이 나오면 성공"),
              ("show ssh", "지금 SSH 로 붙어 있는 세션")],
       undo=[("line vty 0 15\n transport input telnet ssh", "텔넷도 다시 받기")]),
    "j": V([
        ("set system login user <사용자> class super-user authentication plain-text-password", "SSH 로 로그인할 계정입니다. 이미 있으면 건너뛰세요"),
        ("set system services ssh", "SSH 서버를 켭니다. 키는 장비가 알아서 만듭니다"),
        ("set system services ssh root-login deny", "root 계정으로는 SSH 로그인을 못 하게 막습니다 (보안 점검 항목)"),
        ("delete system services telnet", "텔넷 서비스를 지웁니다"),
    ], check=[("show configuration system services", "ssh 만 있고 telnet 이 없는지"),
              ("show system users", "지금 접속한 사용자")]),
    "a": V([
        ("username <사용자> privilege 15 password <비밀번호>", "SSH 로 로그인할 계정입니다. 이미 있으면 건너뛰세요"),
        ("crypto key generate hostkey rsa 2048", "SSH 서버 키(호스트 키)를 만듭니다"),
        ("service ssh", "SSH 서버를 켭니다"),
        ("no service telnet", "텔넷 서버를 끕니다"),
    ], check=[("show ssh server", "SSH 서버 상태·버전"), ("show crypto key hostkey", "만든 키 확인")]),
    "o6": V([
        ("user <사용자> password <비밀번호> read-write all", "SSH 로 로그인할 계정입니다. 이미 있으면 건너뛰세요"),
        ("aaa authentication ssh local", "SSH 로 들어오는 사람을 로컬 계정으로 인증하게 합니다. 이것이 SSH 를 켜는 명령입니다 (키는 장비가 갖고 있음)"),
        ("no aaa authentication telnet", "텔넷 접속을 끕니다"),
    ], check=[("show aaa authentication", "ssh 는 local, telnet 은 없는지")]),
    "o8": V([
        ("user <사용자> password <비밀번호> read-write all", "SSH 로 로그인할 계정입니다. 이미 있으면 건너뛰세요"),
        ("aaa authentication ssh local", "SSH 로 들어오는 사람을 로컬 계정으로 인증하게 합니다. 이것이 SSH 를 켜는 명령입니다"),
        ("no aaa authentication telnet", "텔넷 접속을 끕니다"),
    ], check=[("show aaa authentication", "ssh 는 local, telnet 은 없는지")]),
}, keys="ssh 설정 순서 텔넷 끄기 보안 점검 원격 접속 키 생성 crypto rsa vty", rel=["ssh-on", "telnet-off", "ssh-show"],
   warn="원격(텔넷)으로 붙어서 작업 중이면 텔넷을 끄기 전에 새 창으로 SSH 접속이 되는지 먼저 확인하세요.")

guide("g-vty-acl", "remote", "관리 PC 대역에서만 원격 접속 허용",
      "보안 점검에서 '접근 IP 제한' 항목입니다. 허용할 대역을 목록으로 만들고 원격 접속에 겁니다.", {
    "c": V([
        ("ip access-list standard MGMT", "이름이 MGMT 인 표준 ACL 을 만듭니다 (출발지 IP 만 봅니다)"),
        (" permit <관리대역> <관리와일드카드>", "허용할 관리 PC 대역. 와일드카드는 마스크를 뒤집은 값 (255.255.255.0 → 0.0.0.255). 나머지는 끝의 보이지 않는 deny 로 막힘"),
        ("line vty 0 15", "원격 접속 줄 설정으로 들어갑니다"),
        (" access-class MGMT in", "원격 접속으로 들어오는 쪽(in)에 MGMT 목록을 겁니다"),
    ], check=[("show access-lists MGMT", "줄마다 맞은 횟수(matches)가 올라가는지"),
              ("show running-config | section line vty", "access-class 가 들어갔는지")],
       undo=[("line vty 0 15\n no access-class MGMT in", "제한 풀기")]),
    "j": V([
        ("set policy-options prefix-list MGMT <관리대역>/<관리프리픽스>", "허용할 관리 PC 대역 목록(MGMT)을 만듭니다"),
        ("set firewall family inet filter PROTECT-RE term SSH from source-prefix-list MGMT", "규칙 SSH: 출발지가 MGMT 목록이고"),
        ("set firewall family inet filter PROTECT-RE term SSH from protocol tcp", "TCP 이며"),
        ("set firewall family inet filter PROTECT-RE term SSH from destination-port ssh", "목적지 포트가 22(ssh)이면"),
        ("set firewall family inet filter PROTECT-RE term SSH then accept", "허용합니다"),
        ("set firewall family inet filter PROTECT-RE term SSH-DROP from protocol tcp", "규칙 SSH-DROP: 그 밖의 TCP"),
        ("set firewall family inet filter PROTECT-RE term SSH-DROP from destination-port ssh", "22번 접속은"),
        ("set firewall family inet filter PROTECT-RE term SSH-DROP then discard", "버립니다"),
        ("set firewall family inet filter PROTECT-RE term ALL then accept", "나머지 트래픽(OSPF·SNMP 등)은 그대로 허용합니다. 이 줄이 없으면 장비로 가는 모든 것이 막힙니다"),
        ("set interfaces lo0 unit 0 family inet filter input PROTECT-RE", "장비 자신으로 들어오는 트래픽은 lo0 를 거치므로 여기에 필터를 겁니다"),
    ], check=[("show firewall filter PROTECT-RE", "필터가 걸렸는지")],
       undo=[("delete interfaces lo0 unit 0 family inet filter", "필터 떼기 (설정 모드에서, 그다음 commit)")]),
    "a": (None, "버전에 따라 다름 (line vty 의 access-class 등). 공식 문서 확인 필요"),
    "o6": (None, "공식 문서 확인 필요"),
    "o8": (None, "공식 문서 확인 필요"),
}, keys="접근 제한 허용 ip 관리 pc vty acl access-class 보안 점검 원격", rel=["vty-acl"], mode="remote",
   warn="지금 접속한 PC 의 IP 가 허용 대역에 없으면 넣는 순간 끊깁니다. 콘솔로 붙어서 하거나, 시스코는 미리 reload in 10 을 걸어 두세요.")

guide("g-time-log", "mgmt", "시간·로그 설정 (시간대·NTP·syslog)",
      "로그 시간이 맞아야 장애 때 앞뒤를 따질 수 있습니다. 시간대 → NTP → 로그 서버(OiLog 등) 순서.", {
    "c": V([
        ("clock timezone KST 9 0", "시간대를 한국(UTC+9)으로 정합니다. 안 하면 로그가 9시간 어긋나 보입니다"),
        ("ntp server <NTP서버>", "NTP 서버로 시간을 맞춥니다. 맞추는 데 몇 분 걸립니다"),
        ("service timestamps log datetime msec localtime show-timezone", "로그 줄 앞에 날짜·시간(밀리초, 한국 시간)을 붙입니다"),
        ("logging trap informational", "로그 서버로 보낼 수준. informational(6) = 일반 정보까지 보냄"),
        ("logging host <로그서버>", "로그를 syslog 서버(UDP 514)로 보냅니다"),
    ], check=[("show clock", "시간이 맞는지"), ("show ntp status", "Clock is synchronized 가 나오면 성공"),
              ("show logging", "Trap logging 에 로그 서버가 보이는지")]),
    "j": V([
        ("set system time-zone Asia/Seoul", "시간대를 한국으로 정합니다"),
        ("set system ntp server <NTP서버>", "NTP 서버로 시간을 맞춥니다"),
        ("set system syslog host <로그서버> any any", "모든 종류(any)의 모든 수준(any) 로그를 syslog 서버로 보냅니다"),
    ], check=[("show system uptime", "Current time 이 맞는지"), ("show ntp associations", "서버 앞에 * 가 붙으면 동기화됨")]),
    "a": V([
        ("clock timezone KST plus 9", "시간대를 한국(UTC+9)으로 정합니다"),
        ("ntp server <NTP서버>", "NTP 서버로 시간을 맞춥니다"),
        ("log host <로그서버>", "로그를 syslog 서버로 보냅니다"),
    ], check=[("show clock", "시간이 맞는지"), ("show ntp associations", "서버 앞에 * 가 붙으면 동기화됨")]),
    "o6": V([
        ("system timezone KST", "시간대를 한국으로 정합니다. " + VER),
        ("ntp server <NTP서버>", "NTP 서버를 넣습니다"),
        ("ntp client enable", "NTP 로 시간 맞추기를 켭니다. AOS 는 서버만 넣으면 동작하지 않습니다"),
        ("swlog output socket <로그서버>", "로그(swlog)를 syslog 서버로 보냅니다"),
    ], check=[("system date", "날짜 확인 (system time 은 시간)"), ("show ntp client", "동기화 상태")]),
    "o8": V([
        ("system timezone KST", "시간대를 한국으로 정합니다. " + VER),
        ("ntp server <NTP서버>", "NTP 서버를 넣습니다"),
        ("ntp client admin-state enable", "NTP 로 시간 맞추기를 켭니다"),
        ("swlog output socket <로그서버>", "로그(swlog)를 syslog 서버로 보냅니다"),
    ], check=[("system date", "날짜 확인"), ("show ntp status", "동기화 상태")]),
}, keys="ntp 시간 동기화 시간대 timezone kst syslog 로그 서버 oilog 로그 시간", rel=["timezone", "ntp", "syslog", "ntp-show"])

guide("g-snmp", "mgmt", "NMS 에 장비 등록 (SNMP v2c + 트랩)",
      "와치올·OiNMS 같은 NMS 가 장비를 읽어 가게 커뮤니티를 만들고, 장애 알림(트랩)을 보냅니다.", {
    "c": V([
        ("snmp-server community <커뮤니티> RO", "읽기 전용(RO) 커뮤니티를 만듭니다. public·private 는 보안 점검에 걸리니 쓰지 마세요"),
        ("snmp-server location <장비이름>", "NMS 화면에 보일 위치 정보 (자유롭게)"),
        ("snmp-server host <NMS서버> version 2c <커뮤니티>", "트랩(장애 알림)을 받을 NMS 서버"),
        ("snmp-server enable traps snmp linkdown linkup", "포트 up/down 트랩을 보냅니다"),
    ], check=[("show snmp community", "커뮤니티 확인"), ("show snmp host", "트랩 받을 서버 확인")]),
    "j": V([
        ("set snmp community <커뮤니티> authorization read-only", "읽기 전용 커뮤니티를 만듭니다"),
        ("set snmp location <장비이름>", "NMS 화면에 보일 위치 정보"),
        ("set snmp trap-group NMS version v2", "트랩 묶음 NMS 를 만들고 v2 로 보냅니다"),
        ("set snmp trap-group NMS targets <NMS서버>", "트랩을 받을 서버"),
    ], check=[("show snmp statistics", "요청이 들어오는지 (Get 숫자가 늘어나는지)")]),
    "a": V([
        ("snmp-server community <커뮤니티> ro", "읽기 전용 커뮤니티를 만듭니다"),
        ("snmp-server host <NMS서버> version 2c <커뮤니티>", "트랩을 받을 NMS 서버. 보낼 트랩 종류는 " + VER),
    ], check=[("show snmp-server community", "커뮤니티 확인")]),
    "o6": V([
        ("user <SNMP사용자> password <비밀번호> read-only all no auth", "AOS 는 커뮤니티를 계정에 연결합니다. NMS 용 읽기 전용 계정을 만듭니다"),
        ("snmp security no-security", "v2c(인증 없는 SNMP)를 받게 합니다. 기본값은 v3 만 받는 경우가 많습니다. " + VER),
        ("snmp community map <커뮤니티> user <SNMP사용자> on", "커뮤니티 이름을 위 계정에 연결합니다"),
        ("snmp station <NMS서버> 162 <SNMP사용자> v2 enable", "트랩 받을 서버. " + VER),
    ], check=[("show snmp community map", "커뮤니티 연결 확인"), ("show snmp station", "트랩 서버 확인")]),
    "o8": V([
        ("user <SNMP사용자> password <비밀번호> read-only all no auth", "NMS 용 읽기 전용 계정을 만듭니다"),
        ("snmp security no-security", "v2c 를 받게 합니다. " + VER),
        ("snmp community-map mode enable", "커뮤니티 연결 기능을 켭니다"),
        ("snmp community-map <커뮤니티> user <SNMP사용자> enable", "커뮤니티 이름을 위 계정에 연결합니다"),
        ("snmp station <NMS서버> 162 <SNMP사용자> v2 enable", "트랩 받을 서버. " + VER),
    ], check=[("show snmp community-map", "커뮤니티 연결 확인"), ("show snmp station", "트랩 서버 확인")]),
}, keys="snmp nms 등록 커뮤니티 트랩 trap 와치올 감시 v2c", rel=["snmp"],
   warn="보안 점검에서 v3 를 요구하면 'SNMPv3 설정' 따라하기를 쓰세요.")

guide("g-snmpv3", "devsec", "SNMPv3 설정 (암호화된 감시)",
      "v2c 는 커뮤니티가 평문으로 다녀서 공공기관 점검에서 v3 를 요구합니다. NMS 에도 같은 사용자·비밀번호를 넣습니다.", {
    "c": V([
        ("snmp-server group <SNMP그룹> v3 priv", "v3 그룹을 만듭니다. priv = 인증 + 암호화 둘 다 하는 가장 높은 수준"),
        ("snmp-server user <SNMP사용자> <SNMP그룹> v3 auth sha <인증비밀번호> priv aes 128 <암호비밀번호>", "사용자를 만듭니다. auth sha = 인증, priv aes 128 = 내용 암호화. 이 줄은 show run 에 안 보입니다"),
        ("no snmp-server community <커뮤니티>", "예전 v2c 커뮤니티가 있으면 지웁니다"),
    ], check=[("show snmp user", "사용자·인증·암호화 방식 확인"), ("show snmp group", "그룹 확인")]),
    "j": V([
        ("set snmp v3 usm local-engine user <SNMP사용자> authentication-sha authentication-password <인증비밀번호>", "사용자와 인증(SHA) 비밀번호"),
        ("set snmp v3 usm local-engine user <SNMP사용자> privacy-aes128 privacy-password <암호비밀번호>", "암호화(AES128) 비밀번호"),
        ("set snmp v3 vacm security-to-group security-model usm security-name <SNMP사용자> group <SNMP그룹>", "사용자를 그룹에 넣습니다"),
        ("set snmp view all oid .1 include", "보여 줄 범위(view) all = 전체 MIB"),
        ("set snmp v3 vacm access group <SNMP그룹> default-context-prefix security-model usm security-level privacy read-view all", "그룹에 읽기 권한(view all)을 줍니다. privacy = 암호화 필수"),
    ], check=[("show snmp v3", "사용자·그룹 확인")]),
    "a": V([
        ("snmp-server view all 1 included", "보여 줄 범위 all = 전체 MIB"),
        ("snmp-server group <SNMP그룹> priv read all", "v3 그룹 (인증 + 암호화), 읽기 view all"),
        ("snmp-server user <SNMP사용자> <SNMP그룹> auth sha <인증비밀번호> priv aes <암호비밀번호>", "사용자를 만듭니다"),
    ], check=[("show snmp-server user", "사용자 확인")]),
    "o6": V([
        ("user <SNMP사용자> password <인증비밀번호> read-only all sha+aes", "AOS 는 계정 하나에 SNMPv3 를 붙입니다. 비밀번호 하나로 인증·암호화를 같이 합니다. " + VER),
        ("snmp security privacy all", "암호화된 SNMP 요청만 받습니다"),
    ], check=[("show user <SNMP사용자>", "SNMP 레벨 확인")]),
    "o8": V([
        ("user <SNMP사용자> password <인증비밀번호> read-only all sha+aes", "계정 하나에 SNMPv3 를 붙입니다. " + VER),
        ("snmp security privacy all", "암호화된 SNMP 요청만 받습니다"),
    ], check=[("show user <SNMP사용자>", "SNMP 레벨 확인")]),
}, keys="snmpv3 snmp v3 암호화 보안 점검 usm nms", rel=["snmpv3", "snmp-v2-off"])

guide("g-harden", "devsec", "보안 점검 대비 기본 하드닝",
      "공공기관 정기 점검에서 자주 나오는 항목을 한 번에 넣습니다. 숫자(길이·시간)는 기관 기준에 맞추세요.", {
    "c": V([
        ("service password-encryption", "설정 파일에 평문으로 보이는 비밀번호를 가립니다 (약한 암호라 secret 이 더 좋음)"),
        ("security passwords min-length 9", "비밀번호 최소 길이"),
        ("login block-for 300 attempts 5 within 60", "60초 안에 5번 틀리면 300초 동안 로그인을 막습니다"),
        ("line vty 0 15\n exec-timeout 10 0", "원격 접속이 10분 동안 아무것도 안 하면 끊습니다"),
        ("line con 0\n exec-timeout 10 0", "콘솔도 똑같이"),
        ("no ip http server", "웹 관리(HTTP)를 끕니다 (평문 전송)"),
        ("no ip http secure-server", "HTTPS 웹 관리도 안 쓰면 끕니다"),
        ("no service pad\nno ip bootp server\nno ip source-route", "안 쓰는 옛 서비스를 끕니다"),
        ("banner motd ^\nAuthorized users only.\n^", "로그인 화면 경고 문구. ^ 사이가 문구입니다"),
    ], check=[("show running-config | include password|timeout|http", "들어갔는지 한 번에 확인")]),
    "j": V([
        ("set system login password minimum-length 9", "비밀번호 최소 길이"),
        ("set system login password change-type character-sets\nset system login password minimum-changes 3", "대·소문자·숫자·특수문자 중 3종류 이상"),
        ("set system login retry-options tries-before-disconnect 5", "5번 틀리면 접속을 끊습니다"),
        ("set system login retry-options lockout-period 5", "그리고 5분 잠급니다"),
        ("set system login class ADMIN-10M idle-timeout 10\nset system login class ADMIN-10M permissions all", "10분 유휴 시 끊는 관리자용 로그인 클래스를 만듭니다"),
        ("set system login user <사용자> class ADMIN-10M", "관리자 계정에 그 클래스를 붙입니다 (super-user 대신)"),
        ("delete system services web-management http", "웹 관리(HTTP)를 끕니다"),
        ("delete system services telnet\ndelete system services ftp", "안 쓰는 서비스를 끕니다"),
        ('set system login message "Authorized users only."', "로그인 화면 경고 문구"),
    ], check=[("show configuration system login", "로그인 관련 설정 확인")]),
    "a": V([
        ("service password-encryption", "설정 파일의 비밀번호를 가립니다"),
        ("security-password minimum-length 9\nsecurity-password minimum-categories 3", "비밀번호 최소 길이와 종류(대·소문자·숫자·특수문자 중 3)"),
        ("aaa local authentication attempts max-fail 5\naaa local authentication attempts lockout-time 300", "5번 틀리면 300초 잠금"),
        ("line vty 0 32\n exec-timeout 10 0", "원격 접속 10분 유휴 시 끊기 (vty 범위는 장비마다 다를 수 있음)"),
        ("no service http", "웹 관리(HTTP)를 끕니다"),
        ("no service telnet\nno service ftp", "안 쓰는 서비스를 끕니다"),
        ("banner motd Authorized users only.", "로그인 화면 경고 문구"),
    ], check=[("show running-config", "들어갔는지 확인")]),
    "o6": V([
        ("user password-size min 9", "비밀번호 최소 길이"),
        ("user password-policy min-uppercase 1\nuser password-policy min-digit 1", "대문자·숫자 최소 1개. " + VER),
        ("user lockout-threshold 5\nuser lockout-window 5\nuser lockout-duration 5", "5분 안에 5번 틀리면 5분 잠금. " + VER),
        ("session timeout cli 10", "10분 유휴 시 끊기"),
        ("no ip service http\nno ip service ftp\nno ip service telnet", "웹·FTP·텔넷을 끕니다"),
    ], check=[("show user password-policy", "규칙 확인"), ("show ip service", "켜진 서비스 확인")],
       note="배너는 /flash/switch/pre_banner.txt 파일로 넣습니다"),
    "o8": V([
        ("user password-size min 9", "비밀번호 최소 길이"),
        ("user password-policy min-uppercase 1\nuser password-policy min-digit 1", "대문자·숫자 최소 1개. " + VER),
        ("user lockout-threshold 5\nuser lockout-window 5\nuser lockout-duration 5", "5분 안에 5번 틀리면 5분 잠금. " + VER),
        ("session timeout cli 10", "10분 유휴 시 끊기"),
        ("no ip service http\nno ip service ftp\nno ip service telnet", "웹·FTP·텔넷을 끕니다"),
    ], check=[("show user password-policy", "규칙 확인"), ("show ip service", "켜진 서비스 확인")],
       note="배너는 /flash/switch/pre_banner.txt 파일로 넣습니다"),
}, keys="보안 점검 하드닝 hardening 취약점 비밀번호 정책 잠금 타임아웃 배너 http 끄기 공공기관", rel=["pw-encrypt", "pw-policy", "login-lockout", "session-timeout", "http-off", "banner", "unused-svc-off"],
   warn="웹 관리로 장비를 관리하고 있다면 HTTP/HTTPS 를 끄기 전에 확인하세요.")

guide("g-aaa", "devsec", "장비 로그인을 RADIUS 서버로 (서버 죽으면 로컬 계정)",
      "여러 장비 계정을 인증 서버 한 곳에서 관리합니다. 서버가 안 될 때를 대비해 로컬 계정을 꼭 남겨 둡니다.", {
    "c": V([
        ("username <사용자> privilege 15 secret <비밀번호>", "서버가 죽었을 때 쓸 로컬 계정을 먼저 만듭니다"),
        ("aaa new-model", "AAA 방식을 켭니다. 이 순간부터 로그인 방식이 바뀌니 접속 창 하나는 열어 두세요"),
        ("radius server <서버이름>\n address ipv4 <인증서버> auth-port 1812 acct-port 1813\n key <비밀키>", "RADIUS 서버를 등록합니다. key 는 서버에 넣은 값과 같아야 합니다"),
        ("aaa authentication login default group radius local", "로그인할 때 RADIUS 로 먼저 묻고, 서버가 응답이 없으면 로컬 계정으로"),
        ("aaa authorization exec default group radius local", "로그인한 뒤의 권한(레벨)도 서버에서 받습니다"),
    ], check=[("test aaa group radius <사용자> <비밀번호> new-code", "장비에서 서버로 인증이 되는지 시험"),
              ("show aaa servers", "서버 상태(UP)·요청 횟수")],
       note="TACACS+ 면 radius 대신 tacacs server / group tacacs+"),
    "j": V([
        ("set system login user <사용자> class super-user authentication plain-text-password", "서버가 죽었을 때 쓸 로컬 계정"),
        ("set system radius-server <인증서버> secret <비밀키>", "RADIUS 서버를 등록합니다"),
        ("set system authentication-order [ radius password ]", "RADIUS 로 먼저 묻고, 안 되면 로컬(password)"),
    ], check=[("show configuration system authentication-order", "순서 확인")],
       note="RADIUS 사용자는 서버에서 Juniper-Local-User-Name 속성으로 로컬 클래스(예: remote 템플릿 계정)와 이어 줘야 합니다"),
    "a": V([
        ("username <사용자> privilege 15 password <비밀번호>", "서버가 죽었을 때 쓸 로컬 계정"),
        ("radius-server host <인증서버> key <비밀키>", "RADIUS 서버를 등록합니다"),
        ("aaa authentication login default group radius local", "RADIUS 로 먼저 묻고, 안 되면 로컬 계정"),
    ], check=[("show radius", "서버 상태")]),
    "o6": V([
        ("user <사용자> password <비밀번호> read-write all", "서버가 죽었을 때 쓸 로컬 계정"),
        ("aaa radius-server <서버이름> host <인증서버> key <비밀키>", "RADIUS 서버를 이름 붙여 등록합니다"),
        ("aaa authentication default <서버이름> local", "모든 접속(ssh·telnet·http 등)을 서버로 먼저, 안 되면 로컬로"),
    ], check=[("show aaa server", "서버 등록 확인"), ("show aaa authentication", "인증 순서 확인")]),
    "o8": V([
        ("user <사용자> password <비밀번호> read-write all", "서버가 죽었을 때 쓸 로컬 계정"),
        ("aaa radius-server <서버이름> host <인증서버> key <비밀키>", "RADIUS 서버를 이름 붙여 등록합니다"),
        ("aaa authentication default <서버이름> local", "모든 접속을 서버로 먼저, 안 되면 로컬로"),
    ], check=[("show aaa server", "서버 등록 확인"), ("show aaa authentication", "인증 순서 확인")]),
}, keys="aaa radius tacacs 인증 서버 로그인 계정 통합 관리 local", rel=["radius-server", "tacacs-server", "aaa-login"], mode="remote",
   warn="AAA 설정이 틀리면 로그인을 못 하게 됩니다. 콘솔이나 열어 둔 접속 창에서 하고, 새 창으로 로그인되는지 확인한 뒤에 저장하세요.")

# ═══════════════════════════ VLAN·포트 ═══════════════════════════
guide("g-vlan-access", "vlan", "VLAN 만들고 PC 포트 넣기 (access)",
      "PC·CCTV·AP 처럼 VLAN 하나만 쓰는 단말 포트 설정입니다.", {
    "c": V([
        ("vlan <VLAN번호>\n name <VLAN이름>", "VLAN 을 만들고 이름을 붙입니다 (이름은 없어도 되지만 나중에 알아보기 쉬움)"),
        ("interface <포트>", "설정할 포트로 들어갑니다. 여러 개면 interface range Gi1/0/1 - 10"),
        (" description <VLAN이름>-PC", "포트 설명. 나중에 show interfaces status 에서 보입니다"),
        (" switchport mode access", "VLAN 하나만 쓰는 access 포트로 고정합니다 (상대와 트렁크 협상 안 함)"),
        (" switchport access vlan <VLAN번호>", "이 포트를 VLAN 에 넣습니다"),
        (" spanning-tree portfast", "PC 포트라 STP 대기(30초) 없이 바로 열리게 합니다"),
        (" no shutdown", "포트를 켭니다 (꺼져 있었다면)"),
    ], check=[("show vlan brief", "VLAN 이 있고 포트가 그 줄에 보이는지"),
              ("show interfaces <포트> switchport", "Access Mode VLAN 이 맞는지")]),
    "j": V([
        ("set vlans <VLAN이름> vlan-id <VLAN번호>", "VLAN 을 만듭니다. 주니퍼는 이름으로 다룹니다"),
        ('set interfaces <포트> description "<VLAN이름>-PC"', "포트 설명"),
        ("set interfaces <포트> unit 0 family ethernet-switching interface-mode access", "access 포트로 정합니다"),
        ("set interfaces <포트> unit 0 family ethernet-switching vlan members <VLAN이름>", "이 포트를 VLAN 에 넣습니다"),
        ("set protocols rstp interface <포트> edge", "PC 포트라 STP 대기 없이 바로 열리게 합니다"),
    ], check=[("show vlans <VLAN이름>", "VLAN 과 포트 확인"), ("show ethernet-switching interface <포트>", "포트의 VLAN 확인")]),
    "a": V([
        ("vlan database\n vlan <VLAN번호> name <VLAN이름>", "VLAN 은 vlan database 에서 만듭니다"),
        ("interface <포트>", "설정할 포트로 들어갑니다. 여러 개면 interface port1.0.1-1.0.10"),
        (" description <VLAN이름>-PC", "포트 설명"),
        (" switchport mode access", "access 포트로 정합니다"),
        (" switchport access vlan <VLAN번호>", "이 포트를 VLAN 에 넣습니다"),
        (" spanning-tree edgeport", "PC 포트라 STP 대기 없이 바로 열리게 합니다"),
    ], check=[("show vlan brief", "VLAN 과 포트 확인"), ("show interface <포트> switchport", "포트의 VLAN 확인")]),
    "o6": V([
        ('vlan <VLAN번호> name "<VLAN이름>"', "VLAN 을 만들고 이름을 붙입니다"),
        ("vlan <VLAN번호> port default <포트>", "포트의 기본(untagged) VLAN 을 정합니다. 범위도 됨 (1/1-12)"),
        ('interfaces <포트> alias "<VLAN이름>-PC"', "포트 설명"),
    ], check=[("show vlan port <포트>", "포트의 VLAN 확인"), ("show vlan", "VLAN 목록")]),
    "o8": V([
        ('vlan <VLAN번호> admin-state enable name "<VLAN이름>"', "VLAN 을 만들고 켭니다"),
        ("vlan <VLAN번호> members port <포트> untagged", "포트를 VLAN 에 untagged(access)로 넣습니다. 범위도 됨 (1/1/1-12)"),
        ('interfaces port <포트> alias "<VLAN이름>-PC"', "포트 설명"),
    ], check=[("show vlan members port <포트>", "포트의 VLAN 확인"), ("show vlan", "VLAN 목록")]),
}, keys="vlan 생성 access 액세스 포트 할당 pc 단말 untagged", rel=["vlan-create", "vlan-access", "vlan-show"])

guide("g-trunk", "vlan", "스위치끼리 트렁크 연결 (여러 VLAN 넘기기)",
      "스위치와 스위치(또는 AP·서버)를 잇는 포트에 여러 VLAN 을 태그 붙여 넘깁니다. 양쪽 다 똑같이 맞춥니다.", {
    "c": V([
        ("interface <업링크포트>", "상대 스위치와 연결된 포트로 들어갑니다"),
        (" description UPLINK", "포트 설명"),
        (" switchport trunk encapsulation dot1q", "옛 장비(3750·3560 등)만 필요. 요즘 장비는 이 명령이 없어 오류가 나면 건너뛰세요"),
        (" switchport mode trunk", "트렁크 포트로 고정합니다"),
        (" switchport trunk allowed vlan <VLAN목록>", "넘길 VLAN 만 허용합니다 (예: 10,20,99). 안 쓰면 전부 넘어감"),
        (" switchport trunk native vlan <네이티브VLAN>", "태그 없이 다닐 VLAN. 양쪽이 같아야 합니다 (다르면 CDP 경고, VLAN 섞임)"),
    ], check=[("show interfaces trunk", "포트가 trunking 이고 허용·활성 VLAN 이 맞는지")],
       note="이미 쓰는 트렁크에 VLAN 을 더할 때는 switchport trunk allowed vlan add <번호> — add 를 빼면 목록이 통째로 바뀌어 장애가 납니다!"),
    "j": V([
        ('set interfaces <업링크포트> description "UPLINK"', "포트 설명"),
        ("set interfaces <업링크포트> unit 0 family ethernet-switching interface-mode trunk", "트렁크 포트로 정합니다"),
        ("set interfaces <업링크포트> unit 0 family ethernet-switching vlan members [ <VLAN이름목록> ]", "넘길 VLAN 들 (이름을 띄어쓰기로)"),
        ("set interfaces <업링크포트> native-vlan-id <네이티브VLAN>", "태그 없이 다닐 VLAN (필요할 때만)"),
    ], check=[("show ethernet-switching interface <업링크포트>", "tagged VLAN 목록 확인")]),
    "a": V([
        ("interface <업링크포트>", "상대 스위치와 연결된 포트로 들어갑니다"),
        (" description UPLINK", "포트 설명"),
        (" switchport mode trunk", "트렁크 포트로 정합니다"),
        (" switchport trunk allowed vlan add <VLAN목록>", "넘길 VLAN 을 더합니다 (AW+ 는 add/remove 로 넣고 뺌)"),
        (" switchport trunk native vlan <네이티브VLAN>", "태그 없이 다닐 VLAN. 모두 태그로 보내려면 native vlan none"),
    ], check=[("show interface <업링크포트> switchport", "trunk 모드와 VLAN 확인")]),
    "o6": V([
        ("vlan <VLAN번호> 802.1q <업링크포트>", "VLAN 을 이 포트에 태그(tagged)로 붙입니다. VLAN 마다 한 줄씩 반복"),
        ("vlan <네이티브VLAN> port default <업링크포트>", "태그 없이 다닐 VLAN (기본은 1)"),
    ], check=[("show vlan port <업링크포트>", "tagged/untagged VLAN 확인")]),
    "o8": V([
        ("vlan <VLAN목록> members port <업링크포트> tagged", "VLAN 들을 이 포트에 태그로 붙입니다. 범위도 됨 (vlan 10-20 members ...)"),
        ("vlan <네이티브VLAN> members port <업링크포트> untagged", "태그 없이 다닐 VLAN (기본은 1)"),
    ], check=[("show vlan members port <업링크포트>", "tagged/untagged VLAN 확인")]),
}, keys="trunk 트렁크 tagged 태그 업링크 스위치 연결 allowed native 802.1q", rel=["vlan-trunk", "vlan-trunk-add", "vlan-native", "vlan-port-show"],
   warn="관리 VLAN 이 지나가는 트렁크를 원격으로 바꾸면 접속이 끊길 수 있습니다.")

guide("g-lacp", "lag", "LACP 로 업링크 두 줄 묶기 + 트렁크",
      "케이블 두 가닥을 하나처럼 써서 대역폭을 늘리고 한 줄이 끊겨도 통신이 유지되게 합니다. 양쪽 장비 모두 설정합니다.", {
    "c": V([
        ("interface range <포트1> , <포트2>", "묶을 포트 두 개를 한꺼번에 설정합니다 (쉼표 앞뒤 띄어쓰기)"),
        (" channel-group <묶음번호> mode active", "LACP(active)로 묶습니다. Port-channel<묶음번호> 가 자동으로 생깁니다"),
        ("interface Port-channel<묶음번호>", "이제부터 트렁크 같은 설정은 묶음(포트채널)에 합니다. 멤버 포트에 따로 하지 않습니다"),
        (" switchport mode trunk", "묶음을 트렁크로"),
        (" switchport trunk allowed vlan <VLAN목록>", "넘길 VLAN"),
    ], check=[("show etherchannel summary", "Po<묶음번호>(SU) 이고 멤버가 (P) 면 정상. (I)·(s) 면 상대 설정 확인")]),
    "j": V([
        ("set chassis aggregated-devices ethernet device-count 2", "ae 인터페이스를 몇 개까지 만들지 정합니다 (처음 한 번)"),
        ("set interfaces <포트1> ether-options 802.3ad ae<묶음번호>", "첫 번째 포트를 ae<묶음번호> 에 넣습니다"),
        ("set interfaces <포트2> ether-options 802.3ad ae<묶음번호>", "두 번째 포트도"),
        ("set interfaces ae<묶음번호> aggregated-ether-options lacp active", "LACP 로 상대와 협상합니다"),
        ("set interfaces ae<묶음번호> unit 0 family ethernet-switching interface-mode trunk", "묶음을 트렁크로"),
        ("set interfaces ae<묶음번호> unit 0 family ethernet-switching vlan members [ <VLAN이름목록> ]", "넘길 VLAN"),
    ], check=[("show lacp interfaces", "두 포트 모두 Collecting distributing 이면 정상")],
       note="멤버 포트에 이미 family ethernet-switching 설정이 있으면 먼저 delete interfaces <포트> unit 0 으로 지워야 commit 됩니다"),
    "a": V([
        ("interface <포트1>,<포트2>", "묶을 포트 두 개를 한꺼번에 설정합니다"),
        (" channel-group <묶음번호> mode active", "LACP(active)로 묶습니다. po<묶음번호> 가 생깁니다"),
        ("interface po<묶음번호>", "트렁크 설정은 묶음(po)에 합니다"),
        (" switchport mode trunk", "묶음을 트렁크로"),
        (" switchport trunk allowed vlan add <VLAN목록>", "넘길 VLAN"),
    ], check=[("show etherchannel", "멤버 포트 상태 확인")]),
    "o6": V([
        ("lacp linkagg <묶음번호> size 2 actor admin key <묶음번호>", "LACP 묶음을 만듭니다. size = 최대 포트 수(2/4/8), admin key = 포트와 묶음을 잇는 번호"),
        ("lacp agg <포트1> actor admin key <묶음번호>", "첫 번째 포트를 같은 key 로 묶음에 넣습니다"),
        ("lacp agg <포트2> actor admin key <묶음번호>", "두 번째 포트도"),
        ("vlan <VLAN번호> 802.1q <묶음번호>", "VLAN 을 묶음 번호에 태그로 붙입니다. VLAN 마다 반복"),
    ], check=[("show linkagg", "묶음 상태 UP"), ("show linkagg port", "포트별 상태(Attached)")]),
    "o8": V([
        ("linkagg lacp agg <묶음번호> size 2 actor admin-key <묶음번호>", "LACP 묶음을 만듭니다"),
        ("linkagg lacp port <포트1> actor admin-key <묶음번호>", "첫 번째 포트를 묶음에 넣습니다"),
        ("linkagg lacp port <포트2> actor admin-key <묶음번호>", "두 번째 포트도"),
        ("vlan <VLAN목록> members linkagg <묶음번호> tagged", "VLAN 들을 묶음에 태그로 붙입니다"),
    ], check=[("show linkagg", "묶음 상태 UP"), ("show linkagg port", "포트별 상태")]),
}, keys="lacp 포트채널 port-channel etherchannel 링크 묶기 이중화 업링크 linkagg ae lag", rel=["lacp-create", "lag-show"],
   warn="한쪽만 설정한 채 두 줄을 다 꽂으면 루프가 생길 수 있습니다. 양쪽 설정을 마친 뒤 두 번째 케이블을 꽂으세요.")

guide("g-stp", "stp", "스패닝 트리 기본 세팅 (코어 루트 + PC 포트 보호)",
      "루프가 생겨도 원하는 곳이 막히게 코어를 루트로 고정하고, PC 포트는 빨리 열리되 스위치가 꽂히면 막히게 합니다.", {
    "c": V([
        ("spanning-tree mode rapid-pvst", "빠른 RSTP 로 바꿉니다 (시스코 기본은 느린 pvst). 모든 스위치를 같은 방식으로"),
        ("spanning-tree vlan <VLAN목록> priority 4096", "코어 스위치에서만: 우선순위를 낮춰 루트가 되게 합니다 (낮을수록 우선, 기본 32768)"),
        ("interface <포트>", "PC 가 꽂히는 포트로 (access 스위치에서)"),
        (" spanning-tree portfast", "STP 대기 없이 바로 열립니다"),
        (" spanning-tree bpduguard enable", "이 포트로 스위치(BPDU)가 들어오면 포트를 err-disabled 로 꺼서 루프를 막습니다"),
    ], check=[("show spanning-tree root", "루트가 코어 스위치인지"), ("show spanning-tree summary", "모드와 portfast·bpduguard 상태")]),
    "j": V([
        ("set protocols rstp", "RSTP 를 씁니다 (EX 기본)"),
        ("set protocols rstp bridge-priority 4k", "코어 스위치에서만: 루트가 되게 우선순위를 낮춥니다"),
        ("set protocols rstp interface <포트> edge", "PC 포트를 바로 열리게"),
        ("set protocols layer2-control bpdu-block interface <포트>", "PC 포트로 스위치가 들어오면 막습니다"),
    ], check=[("show spanning-tree bridge", "루트 브리지 확인"), ("show spanning-tree interface", "포트 역할·상태")]),
    "a": V([
        ("spanning-tree mode rstp", "RSTP 를 씁니다 (AW+ 기본)"),
        ("spanning-tree priority 4096", "코어 스위치에서만: 루트가 되게 우선순위를 낮춥니다"),
        ("interface <포트>", "PC 가 꽂히는 포트로"),
        (" spanning-tree edgeport", "바로 열리게"),
        (" spanning-tree portfast bpdu-guard enable", "스위치가 꽂히면 막습니다 (edgeport 에서만 동작)"),
    ], check=[("show spanning-tree brief", "루트와 포트 상태")]),
    "o6": V([
        ("bridge protocol rstp", "RSTP 를 씁니다. " + VER),
        ("bridge <VLAN번호> priority 4096", "코어 스위치에서만: 루트가 되게 (1x1 모드 기준). " + VER),
    ], check=[("show spantree", "루트와 상태"), ("show spantree ports", "포트별 상태")],
       note="PC 포트 edge·BPDU 보호는 AOS6 버전별로 달라 공식 문서 확인 필요"),
    "o8": V([
        ("spantree protocol rstp", "RSTP 를 씁니다. " + VER),
        ("spantree vlan <VLAN번호> priority 4096", "코어 스위치에서만: 루트가 되게. " + VER),
    ], check=[("show spantree", "루트와 상태"), ("show spantree ports", "포트별 상태")],
       note="PC 포트 edge·BPDU 보호는 AOS8 버전별로 달라 공식 문서 확인 필요"),
}, keys="stp 스패닝 트리 루프 방지 루트 rstp portfast bpdu guard edge", rel=["stp-mode", "stp-root", "stp-edge", "stp-bpduguard", "stp-show"])

guide("g-mirror", "misc", "포트 미러링으로 패킷 뜨기 (와이어샤크)",
      "보고 싶은 포트의 패킷을 다른 포트로 복사해서, 거기 꽂은 노트북 와이어샤크로 봅니다. 다 보면 꼭 지웁니다.", {
    "c": V([
        ("monitor session 1 source interface <포트> both", "볼 포트(source). both = 들어오고 나가는 것 모두"),
        ("monitor session 1 destination interface <받는포트>", "복사본을 내보낼 포트. 이 포트는 평소 통신이 안 됩니다"),
    ], check=[("show monitor session 1", "source·destination 확인")],
       undo=[("no monitor session 1", "다 보고 나면 지웁니다")]),
    "j": V([
        ("set forwarding-options analyzer <분석이름> input ingress interface <포트>.0", "볼 포트로 들어오는 것"),
        ("set forwarding-options analyzer <분석이름> input egress interface <포트>.0", "볼 포트에서 나가는 것"),
        ("set forwarding-options analyzer <분석이름> output interface <받는포트>.0", "복사본을 내보낼 포트"),
    ], check=[("show forwarding-options analyzer", "설정 확인")],
       undo=[("delete forwarding-options analyzer <분석이름>", "다 보고 나면 지웁니다 (설정 모드, commit)")]),
    "a": V([
        ("interface <받는포트>", "복사본을 받을 포트로 들어갑니다 (AW+ 는 받는 쪽에서 설정)"),
        (" mirror interface <포트> direction both", "볼 포트의 양방향 패킷을 받습니다. 받는 포트는 VLAN 에서 빠집니다"),
    ], check=[("show mirror", "설정 확인")],
       undo=[("interface <받는포트>\n no mirror interface <포트>", "다 보고 나면 지웁니다")]),
    "o6": V([
        ("port mirroring 1 source <포트> destination <받는포트> bidirectional", "볼 포트 → 받는 포트, 양방향"),
    ], check=[("show port mirroring status", "상태 확인")], undo=[("no port mirroring 1", "다 보고 나면 지웁니다")]),
    "o8": V([
        ("port-mirroring 1 source port <포트> destination port <받는포트> bidirectional", "볼 포트 → 받는 포트, 양방향"),
    ], check=[("show port-mirroring status", "상태 확인")], undo=[("no port-mirroring 1", "다 보고 나면 지웁니다")]),
}, keys="미러링 mirror span 패킷 캡처 와이어샤크 wireshark 분석", rel=["mirror", "mirror-show"],
   warn="업링크 같은 바쁜 포트를 미러링하면 받는 포트가 넘칠 수 있습니다. 받는 포트에 다른 장비를 꽂아 두지 마세요.")

# ═══════════════════════════ L3·라우팅 ═══════════════════════════
guide("g-intervlan", "l3", "VLAN 간 라우팅 (L3 스위치를 게이트웨이로)",
      "VLAN 마다 L3 스위치에 게이트웨이 IP 를 주고, 바깥(방화벽)으로 가는 기본 경로를 넣습니다. VLAN 이 여러 개면 VLAN·IP 단계를 반복.", {
    "c": V([
        ("ip routing", "L3 라우팅을 켭니다. 이게 없으면 VLAN 끼리 통신이 안 됩니다"),
        ("vlan <VLAN번호>\n name <VLAN이름>", "VLAN 을 만듭니다"),
        ("interface vlan <VLAN번호>\n ip address <게이트웨이IP> <마스크>\n no shutdown", "이 VLAN PC 들의 게이트웨이가 될 IP 입니다"),
        ("ip route 0.0.0.0 0.0.0.0 <상위장비IP>", "모르는 목적지는 방화벽(상위 장비)으로 보냅니다"),
    ], check=[("show ip route", "C(직접 연결)로 VLAN 대역, S* 로 기본 경로가 보이는지"),
              ("show ip interface brief", "Vlan 인터페이스 up/up")],
       note="방화벽에도 이 VLAN 대역으로 돌아오는 경로(L3 스위치 쪽)를 넣어야 인터넷이 됩니다"),
    "j": V([
        ("set vlans <VLAN이름> vlan-id <VLAN번호>", "VLAN 을 만듭니다"),
        ("set interfaces irb unit <VLAN번호> family inet address <게이트웨이IP>/<프리픽스>", "게이트웨이 IP (irb)"),
        ("set vlans <VLAN이름> l3-interface irb.<VLAN번호>", "irb 를 VLAN 에 연결합니다"),
        ("set routing-options static route 0.0.0.0/0 next-hop <상위장비IP>", "기본 경로"),
    ], check=[("show route", "VLAN 대역과 0.0.0.0/0 확인")]),
    "a": V([
        ("vlan database\n vlan <VLAN번호> name <VLAN이름>", "VLAN 을 만듭니다"),
        ("interface vlan<VLAN번호>\n ip address <게이트웨이IP>/<프리픽스>", "게이트웨이 IP. L3 지원 모델은 기본으로 라우팅됩니다"),
        ("ip route 0.0.0.0/0 <상위장비IP>", "기본 경로"),
    ], check=[("show ip route", "VLAN 대역과 기본 경로 확인")]),
    "o6": V([
        ('vlan <VLAN번호> name "<VLAN이름>"', "VLAN 을 만듭니다"),
        ('ip interface "vlan<VLAN번호>" address <게이트웨이IP> mask <마스크> vlan <VLAN번호>', "게이트웨이 IP. AOS 는 기본으로 라우팅됩니다"),
        ("ip static-route 0.0.0.0 mask 0.0.0.0 gateway <상위장비IP>", "기본 경로"),
    ], check=[("show ip route", "경로 확인"), ("show ip interface", "인터페이스 확인")]),
    "o8": V([
        ('vlan <VLAN번호> admin-state enable name "<VLAN이름>"', "VLAN 을 만듭니다"),
        ('ip interface "vlan<VLAN번호>" address <게이트웨이IP> mask <마스크> vlan <VLAN번호>', "게이트웨이 IP"),
        ("ip static-route 0.0.0.0/0 gateway <상위장비IP>", "기본 경로"),
    ], check=[("show ip routes", "경로 확인"), ("show ip interface", "인터페이스 확인")]),
}, keys="vlan 간 라우팅 inter-vlan l3 svi 게이트웨이 ip routing 기본 경로 코어", rel=["ip-routing", "svi", "static-route", "route-show"])

guide("g-dhcp-relay", "l3", "DHCP 릴레이 (다른 대역 DHCP 서버에서 IP 받기)",
      "PC 와 DHCP 서버가 다른 VLAN 에 있으면 게이트웨이(L3)가 요청을 서버로 넘겨 줘야 합니다.", {
    "c": V([
        ("interface vlan <VLAN번호>", "PC 들이 있는 VLAN 의 게이트웨이 인터페이스로"),
        (" ip helper-address <DHCP서버>", "이 VLAN 에서 들어온 DHCP 요청(브로드캐스트)을 서버로 넘깁니다"),
    ], check=[("show ip interface vlan <VLAN번호> | include Helper", "Helper address 확인")]),
    "j": V([
        ("set forwarding-options dhcp-relay server-group DHCP-SRV <DHCP서버>", "DHCP 서버 목록"),
        ("set forwarding-options dhcp-relay group RELAY active-server-group DHCP-SRV", "릴레이 묶음이 쓸 서버 목록"),
        ("set forwarding-options dhcp-relay group RELAY interface irb.<VLAN번호>", "요청을 받을 VLAN 인터페이스"),
    ], check=[("show dhcp relay binding", "넘겨 준 기록")]),
    "a": V([
        ("service dhcp-relay", "DHCP 릴레이 기능을 켭니다"),
        ("interface vlan<VLAN번호>", "PC VLAN 인터페이스로"),
        (" ip dhcp-relay server-address <DHCP서버>", "넘길 서버"),
    ], check=[("show ip dhcp-relay", "설정 확인. " + VER)]),
    "o6": V([
        ("ip helper address <DHCP서버>", "DHCP 요청을 서버로 넘깁니다 (장비 전체에 걸림)"),
    ], check=[("show ip helper", "설정 확인")]),
    "o8": V([
        ("ip helper address <DHCP서버>", "DHCP 요청을 서버로 넘깁니다. 버전에 따라 ip dhcp relay 명령으로 바뀐 경우가 있음"),
    ], check=[("show ip helper", "설정 확인. " + VER)]),
}, keys="dhcp 릴레이 relay helper ip 못 받음 다른 대역 서버", rel=["dhcp-relay", "dhcp-show"])

guide("g-dhcp-server", "l3", "스위치를 DHCP 서버로 (작은 사이트)",
      "서버가 없는 작은 사이트에서 L3 스위치가 직접 IP 를 나눠 줍니다.", {
    "c": V([
        ("ip dhcp excluded-address <제외시작> <제외끝>", "나눠 주지 않을 IP (게이트웨이·서버·프린터 같은 고정 IP 범위)"),
        ("ip dhcp pool <풀이름>", "DHCP 풀(나눠 줄 목록)을 만들고 그 설정으로 들어갑니다"),
        (" network <대역> <마스크>", "나눠 줄 대역"),
        (" default-router <게이트웨이IP>", "PC 에 알려 줄 게이트웨이"),
        (" dns-server <DNS>", "PC 에 알려 줄 DNS"),
        (" lease 7", "IP 를 빌려주는 기간 (일)"),
    ], check=[("show ip dhcp pool", "풀 사용량"), ("show ip dhcp binding", "누구에게 어떤 IP 를 줬는지"),
              ("show ip dhcp conflict", "IP 충돌 기록")]),
    "j": V([
        ("set access address-assignment pool <풀이름> family inet network <대역>/<프리픽스>", "나눠 줄 대역"),
        ("set access address-assignment pool <풀이름> family inet range R1 low <시작IP> high <끝IP>", "실제로 나눠 줄 범위"),
        ("set access address-assignment pool <풀이름> family inet dhcp-attributes router <게이트웨이IP>", "게이트웨이"),
        ("set access address-assignment pool <풀이름> family inet dhcp-attributes name-server <DNS>", "DNS"),
        ("set system services dhcp-local-server group <풀이름> interface irb.<VLAN번호>", "이 VLAN 에서 DHCP 서버로 동작"),
    ], check=[("show dhcp server binding", "나눠 준 IP")]),
    "a": V([
        ("service dhcp-server", "DHCP 서버 기능을 켭니다"),
        ("ip dhcp pool <풀이름>", "풀을 만들고 들어갑니다"),
        (" network <대역> <마스크>", "나눠 줄 대역"),
        (" range <시작IP> <끝IP>", "실제로 나눠 줄 범위"),
        (" default-router <게이트웨이IP>", "게이트웨이"),
        (" dns-server <DNS>", "DNS"),
        (" lease 7 0 0", "빌려주는 기간 (일 시 분)"),
    ], check=[("show ip dhcp binding", "나눠 준 IP. " + VER)], note=VER),
    "o6": (None, "AOS 는 dhcpd.conf 파일로 DHCP 서버를 설정합니다. 공식 문서 확인 필요"),
    "o8": (None, "AOS 는 dhcpd.conf 파일로 DHCP 서버를 설정합니다. 공식 문서 확인 필요"),
}, keys="dhcp 서버 server pool 풀 ip 나눠주기 할당 lease")

guide("g-ospf", "ospf", "OSPF 기본 (이웃 맺고 경로 주고받기)",
      "루프백으로 라우터 ID 를 고정하고, 연결 대역을 area 0 에 넣고, PC 만 있는 VLAN 은 passive 로 둡니다. 이웃 장비도 같은 순서로.", {
    "c": V([
        ("ip routing", "라우팅을 켭니다 (L3 스위치)"),
        ("interface Loopback0\n ip address <루프백IP> 255.255.255.255", "절대 안 꺼지는 가상 인터페이스. 라우터 ID 와 관리용으로 씁니다"),
        ("router ospf 1", "OSPF 프로세스 1 을 켭니다 (1 은 이 장비 안에서만 쓰는 번호, 이웃과 달라도 됨)"),
        (" router-id <라우터ID>", "라우터 ID 를 고정합니다 (보통 루프백 IP). 장비마다 달라야 합니다"),
        (" network <루프백IP> 0.0.0.0 area 0", "루프백을 OSPF 에 넣습니다"),
        (" network <대역> <와일드카드> area 0", "이 대역에 속한 인터페이스에서 OSPF 를 켜고 대역을 광고합니다. 와일드카드 = 마스크 뒤집은 값"),
        (" passive-interface vlan <VLAN번호>", "PC 만 있는 VLAN 은 대역은 광고하되 OSPF 패킷은 안 보냅니다"),
    ], check=[("show ip ospf neighbor", "이웃이 FULL 이면 성공. EXSTART·INIT 에 멈추면 MTU·area·인증 확인"),
              ("show ip route ospf", "O 로 시작하는 경로가 들어왔는지")],
       undo=[("no router ospf 1", "OSPF 를 통째로 지웁니다")]),
    "j": V([
        ("set interfaces lo0 unit 0 family inet address <루프백IP>/32", "루프백 주소"),
        ("set routing-options router-id <라우터ID>", "라우터 ID 를 고정합니다"),
        ("set protocols ospf area 0.0.0.0 interface lo0.0 passive", "루프백을 OSPF 에 넣습니다 (이웃은 안 맺음)"),
        ("set protocols ospf area 0.0.0.0 interface irb.<VLAN번호>", "이웃 장비와 연결된 인터페이스에서 OSPF 를 켭니다. 인터페이스마다 한 줄"),
    ], check=[("show ospf neighbor", "State Full 이면 성공"), ("show route protocol ospf", "OSPF 경로")]),
    "a": V([
        ("interface lo\n ip address <루프백IP>/32", "루프백 주소"),
        ("router ospf", "OSPF 를 켭니다"),
        (" ospf router-id <라우터ID>", "라우터 ID 를 고정합니다"),
        (" network <루프백IP>/32 area 0", "루프백을 OSPF 에 넣습니다"),
        (" network <대역>/<프리픽스> area 0", "이 대역 인터페이스에서 OSPF 를 켭니다"),
        (" passive-interface vlan<VLAN번호>", "PC 만 있는 VLAN 은 passive"),
    ], check=[("show ip ospf neighbor", "Full 이면 성공"), ("show ip route ospf", "OSPF 경로")]),
    "o6": V([
        ("ip router router-id <라우터ID>", "라우터 ID 를 고정합니다"),
        ("ip load ospf", AOS_LOAD),
        ("ip ospf area 0.0.0.0", "area 0 을 만듭니다"),
        ('ip ospf interface "vlan<VLAN번호>"', "OSPF 를 돌릴 IP 인터페이스를 넣습니다 (ip interface 로 만든 이름 그대로)"),
        ('ip ospf interface "vlan<VLAN번호>" area 0.0.0.0', "그 인터페이스를 area 0 에"),
        ('ip ospf interface "vlan<VLAN번호>" status enable', "인터페이스에서 OSPF 를 켭니다"),
        ("ip ospf status enable", "마지막으로 OSPF 전체를 켭니다"),
    ], check=[("show ip ospf neighbor", "Full 이면 성공"), ("show ip ospf routes", "OSPF 경로. " + VER)]),
    "o8": V([
        ("ip router router-id <라우터ID>", "라우터 ID 를 고정합니다"),
        ("ip load ospf", AOS_LOAD),
        ("ip ospf area 0.0.0.0", "area 0 을 만듭니다"),
        ('ip ospf interface "vlan<VLAN번호>"', "OSPF 를 돌릴 IP 인터페이스를 넣습니다"),
        ('ip ospf interface "vlan<VLAN번호>" area 0.0.0.0', "그 인터페이스를 area 0 에"),
        ('ip ospf interface "vlan<VLAN번호>" admin-state enable', "인터페이스에서 OSPF 를 켭니다"),
        ("ip ospf admin-state enable", "마지막으로 OSPF 전체를 켭니다"),
    ], check=[("show ip ospf neighbor", "Full 이면 성공"), ("show ip ospf routes", "OSPF 경로. " + VER)], note=VER),
}, keys="ospf 설정 순서 이웃 area router-id 루프백 동적 라우팅 passive", rel=["ospf", "loopback", "router-id", "ospf-passive", "ospf-nbr", "ospf-route"])

guide("g-ospf-default", "ospf", "OSPF 로 기본 경로 뿌리기 (코어 → 아래 장비)",
      "인터넷으로 나가는 기본 경로를 가진 코어에서, OSPF 이웃들에게 기본 경로를 알려 줍니다.", {
    "c": V([
        ("ip route 0.0.0.0 0.0.0.0 <상위장비IP>", "코어에 기본 경로가 먼저 있어야 합니다 (방화벽 방향)"),
        ("router ospf 1", "OSPF 설정으로"),
        (" default-information originate", "내가 가진 기본 경로를 OSPF 로 뿌립니다 (always 를 붙이면 경로가 없어도 뿌림)"),
    ], check=[("show ip ospf database external", "0.0.0.0 LSA 가 있는지 (코어에서)"),
              ("show ip route 0.0.0.0", "아래 장비에서 O*E2 로 들어왔는지")]),
    "j": V([
        ("set routing-options static route 0.0.0.0/0 next-hop <상위장비IP>", "기본 경로가 먼저 있어야 합니다"),
        ("set policy-options policy-statement OSPF-DEFAULT term 1 from route-filter 0.0.0.0/0 exact", "정책: 0.0.0.0/0 하나만 골라서"),
        ("set policy-options policy-statement OSPF-DEFAULT term 1 then accept", "허용"),
        ("set protocols ospf export OSPF-DEFAULT", "그 정책으로 OSPF 에 내보냅니다"),
    ], check=[("show ospf database external", "0.0.0.0 확인")]),
    "a": V([
        ("ip route 0.0.0.0/0 <상위장비IP>", "기본 경로가 먼저 있어야 합니다"),
        ("router ospf", "OSPF 설정으로"),
        (" default-information originate", "기본 경로를 OSPF 로 뿌립니다"),
    ], check=[("show ip ospf database external", "0.0.0.0 확인")]),
    "o6": (None, "AOS 는 route-map 으로 재분배합니다. 공식 문서 확인 필요"),
    "o8": (None, "AOS 는 route-map 으로 재분배합니다. 공식 문서 확인 필요"),
}, keys="ospf 기본 경로 default originate 디폴트 뿌리기", rel=["ospf-default"])

guide("g-bgp", "bgp", "BGP 기본 (eBGP 이웃 맺고 내 대역 광고)",
      "다른 AS(통신사·다른 기관)와 경로를 주고받습니다. AS 번호·이웃 IP 는 상대와 미리 맞춥니다.", {
    "c": V([
        ("router bgp <AS번호>", "내 AS 번호로 BGP 를 켭니다"),
        (" bgp router-id <라우터ID>", "라우터 ID 를 고정합니다"),
        (" neighbor <이웃IP> remote-as <상대AS>", "이웃과 상대 AS. AS 가 다르면 eBGP, 같으면 iBGP"),
        (" neighbor <이웃IP> description <그룹이름>", "이웃 설명"),
        (" network <광고대역> mask <광고마스크>", "내 대역을 광고합니다. 라우팅 표에 똑같은 대역이 있어야 나갑니다"),
    ], check=[("show ip bgp summary", "State/PfxRcd 에 숫자가 나오면 이웃 성공 (Idle·Active 면 실패)"),
              ("show ip bgp neighbors <이웃IP> advertised-routes", "내가 보낸 경로")]),
    "j": V([
        ("set routing-options autonomous-system <AS번호>", "내 AS 번호"),
        ("set routing-options router-id <라우터ID>", "라우터 ID"),
        ("set protocols bgp group <그룹이름> type external", "eBGP 이웃 묶음을 만듭니다"),
        ("set protocols bgp group <그룹이름> peer-as <상대AS>", "상대 AS"),
        ("set protocols bgp group <그룹이름> neighbor <이웃IP>", "이웃 IP"),
        ("set policy-options policy-statement BGP-OUT term 1 from route-filter <광고대역>/<광고프리픽스> exact", "광고할 대역 고르기"),
        ("set policy-options policy-statement BGP-OUT term 1 then accept", "허용"),
        ("set protocols bgp group <그룹이름> export BGP-OUT", "그 정책으로 이웃에게 보냅니다. 주니퍼는 export 없이는 광고하지 않습니다"),
    ], check=[("show bgp summary", "Establ 이면 성공"), ("show route advertising-protocol bgp <이웃IP>", "보낸 경로")]),
    "a": V([
        ("router bgp <AS번호>", "내 AS 번호로 BGP 를 켭니다"),
        (" bgp router-id <라우터ID>", "라우터 ID"),
        (" neighbor <이웃IP> remote-as <상대AS>", "이웃과 상대 AS"),
        (" network <광고대역>/<광고프리픽스>", "내 대역 광고"),
    ], check=[("show ip bgp summary", "이웃 상태")], note="모델에 따라 BGP 기능 라이선스가 필요할 수 있습니다"),
    "o6": V([
        ("ip load bgp", AOS_LOAD),
        ("ip bgp autonomous-system <AS번호>", "내 AS 번호 (바꾸려면 먼저 ip bgp status disable)"),
        ("ip bgp neighbor <이웃IP>", "이웃을 만듭니다"),
        ("ip bgp neighbor <이웃IP> remote-as <상대AS>", "상대 AS"),
        ("ip bgp neighbor <이웃IP> status enable", "이웃을 켭니다"),
        ("ip bgp network <광고대역> <광고마스크>\nip bgp network <광고대역> <광고마스크> status enable", "광고할 대역을 만들고 켭니다"),
        ("ip bgp status enable", "마지막으로 BGP 전체를 켭니다"),
    ], check=[("show ip bgp neighbors", "이웃 상태 established")]),
    "o8": V([
        ("ip load bgp", AOS_LOAD),
        ("ip bgp autonomous-system <AS번호>", "내 AS 번호"),
        ("ip bgp neighbor <이웃IP>", "이웃을 만듭니다"),
        ("ip bgp neighbor <이웃IP> remote-as <상대AS>", "상대 AS"),
        ("ip bgp neighbor <이웃IP> admin-state enable", "이웃을 켭니다"),
        ("ip bgp network <광고대역> <광고마스크>\nip bgp network <광고대역> <광고마스크> admin-state enable", "광고할 대역을 만들고 켭니다"),
        ("ip bgp admin-state enable", "마지막으로 BGP 전체를 켭니다"),
    ], check=[("show ip bgp neighbors", "이웃 상태")], note=VER),
}, keys="bgp 설정 순서 이웃 ebgp as 번호 광고 network neighbor", rel=["bgp-enable", "bgp-network", "bgp-show", "bgp-adv"])

guide("g-rip", "rip", "RIP v2 기본",
      "작은 망이나 옛 장비와 경로를 주고받을 때. 이웃 장비도 같은 설정.", {
    "c": V([
        ("router rip", "RIP 를 켭니다"),
        (" version 2", "v2 로 (서브넷 마스크를 같이 보냄)"),
        (" network <대역>", "이 대역(클래스 단위) 인터페이스에서 RIP 를 켭니다"),
        (" no auto-summary", "대역을 클래스 단위로 뭉쳐 광고하지 않게 합니다"),
    ], check=[("show ip route rip", "R 로 시작하는 경로"), ("show ip protocols", "RIP 버전·네트워크")]),
    "j": V([
        ("set protocols rip group <그룹이름> neighbor irb.<VLAN번호>", "이웃 장비 쪽 인터페이스에서 RIP 를 켭니다"),
        ("set policy-options policy-statement RIP-OUT term 1 from protocol [ direct rip ]\nset policy-options policy-statement RIP-OUT term 1 then accept", "알릴 경로: 직접 연결 + RIP 로 배운 것"),
        ("set protocols rip group <그룹이름> export RIP-OUT", "그 정책으로 내보냅니다"),
    ], check=[("show rip neighbor", "이웃"), ("show route protocol rip", "RIP 경로")]),
    "a": V([
        ("router rip", "RIP 를 켭니다"),
        (" version 2", "v2 로"),
        (" network <대역>/<프리픽스>", "이 대역 인터페이스에서 RIP"),
    ], check=[("show ip rip", "RIP 상태"), ("show ip route rip", "RIP 경로")]),
    "o6": V([
        ("ip load rip", AOS_LOAD),
        ('ip rip interface "vlan<VLAN번호>"', "RIP 를 돌릴 인터페이스"),
        ('ip rip interface "vlan<VLAN번호>" status enable', "인터페이스에서 켜기"),
        ("ip rip status enable", "RIP 전체 켜기"),
    ], check=[("show ip rip routes", "RIP 경로")]),
    "o8": V([
        ("ip load rip", AOS_LOAD),
        ('ip rip interface "vlan<VLAN번호>"', "RIP 를 돌릴 인터페이스"),
        ('ip rip interface "vlan<VLAN번호>" admin-state enable', "인터페이스에서 켜기"),
        ("ip rip admin-state enable", "RIP 전체 켜기"),
    ], check=[("show ip rip routes", "RIP 경로")], note=VER),
}, keys="rip 립 v2 동적 라우팅", rel=["rip-enable", "rip-show"])

guide("g-eigrp", "rip", "EIGRP 기본 (시스코 전용)",
      "시스코끼리만 쓰는 라우팅 프로토콜. AS 번호가 양쪽 같아야 이웃이 맺어집니다.", {
    "c": V([
        ("router eigrp <AS번호>", "EIGRP 를 켭니다. AS 번호는 이웃과 같아야 합니다"),
        (" network <대역> <와일드카드>", "이 대역 인터페이스에서 EIGRP 를 켭니다"),
        (" no auto-summary", "클래스 단위로 뭉치지 않게"),
        (" passive-interface vlan <VLAN번호>", "PC 만 있는 VLAN 은 이웃을 안 맺게"),
    ], check=[("show ip eigrp neighbors", "이웃"), ("show ip route eigrp", "D 로 시작하는 경로")]),
    "j": NO_EIGRP, "a": NO_EIGRP, "o6": NO_EIGRP, "o8": NO_EIGRP,
}, keys="eigrp 이그알피 시스코", rel=["eigrp-enable", "eigrp-show"])

guide("g-vrrp", "fhrp", "VRRP 게이트웨이 이중화",
      "L3 스위치 두 대가 가상 IP 하나를 나눠 갖고, PC 게이트웨이는 가상 IP 로 잡습니다. 두 장비에 똑같이 넣고 우선순위만 다르게(예: 110 / 100).", {
    "c": V([
        ("interface vlan <VLAN번호>", "이중화할 VLAN 인터페이스로"),
        (" ip address <실제IP> <마스크>", "이 장비의 실제 IP (두 장비가 서로 달라야 함)"),
        (" vrrp <그룹> ip <가상IP>", "가상 IP. 두 장비 같은 그룹 번호·같은 가상 IP"),
        (" vrrp <그룹> priority <우선순위>", "높은 쪽이 Master (기본 100)"),
        (" vrrp <그룹> preempt", "Master 가 살아 돌아오면 다시 Master 를 가져옵니다 (VRRP 는 보통 기본으로 켜져 있음)"),
    ], check=[("show vrrp brief", "한쪽 Master, 다른 쪽 Backup 이면 정상 (둘 다 Master 면 서로 못 보는 것)")],
       note="IOS-XE 16 이상 일부는 vrrp <그룹> address-family ipv4 방식(VRRPv3)입니다"),
    "j": V([
        ("set interfaces irb unit <VLAN번호> family inet address <실제IP>/<프리픽스> vrrp-group <그룹> virtual-address <가상IP>", "실제 IP 아래에 VRRP 그룹과 가상 IP"),
        ("set interfaces irb unit <VLAN번호> family inet address <실제IP>/<프리픽스> vrrp-group <그룹> priority <우선순위>", "높은 쪽이 Master"),
        ("set interfaces irb unit <VLAN번호> family inet address <실제IP>/<프리픽스> vrrp-group <그룹> accept-data", "가상 IP 로 오는 ping 에 응답 (없으면 ping 안 됨)"),
    ], check=[("show vrrp summary", "master / backup 확인")]),
    "a": V([
        ("router vrrp <그룹> vlan<VLAN번호>", "VLAN 인터페이스에 VRRP 그룹을 만듭니다"),
        (" virtual-ip <가상IP> backup", "가상 IP. 실제 IP 와 같으면 backup 대신 master"),
        (" priority <우선순위>", "높은 쪽이 Master"),
        (" enable", "VRRP 를 켭니다"),
    ], check=[("show vrrp", "Master / Backup 확인")]),
    "o6": V([
        ("vrrp <그룹> <VLAN번호>", "VLAN 에 VRRP 그룹을 만듭니다"),
        ("vrrp <그룹> <VLAN번호> ip <가상IP>", "가상 IP"),
        ("vrrp <그룹> <VLAN번호> priority <우선순위>", "높은 쪽이 Master"),
        ("vrrp <그룹> <VLAN번호> enable", "켭니다. 나중에 값을 바꿀 때는 먼저 disable"),
    ], check=[("show vrrp", "Master / Backup 확인")]),
    "o8": V([
        ("vrrp <그룹> <VLAN번호>", "VLAN 에 VRRP 그룹을 만듭니다"),
        ("vrrp <그룹> <VLAN번호> address <가상IP>", "가상 IP"),
        ("vrrp <그룹> <VLAN번호> priority <우선순위>", "높은 쪽이 Master"),
        ("vrrp <그룹> <VLAN번호> admin-state enable", "켭니다. 값을 바꿀 때는 먼저 admin-state disable"),
    ], check=[("show vrrp", "Master / Backup 확인")], note=VER),
}, keys="vrrp 게이트웨이 이중화 가상 ip master backup failover 설정 순서", rel=["vrrp", "vrrp-show"])

guide("g-hsrp", "fhrp", "HSRP 게이트웨이 이중화 (시스코 전용)",
      "시스코 두 대끼리 게이트웨이 이중화. 다른 벤더와 섞이면 VRRP 를 씁니다.", {
    "c": V([
        ("interface vlan <VLAN번호>", "이중화할 VLAN 인터페이스로"),
        (" ip address <실제IP> <마스크>", "이 장비의 실제 IP"),
        (" standby <그룹> ip <가상IP>", "가상 IP. 두 장비 같은 그룹·같은 가상 IP"),
        (" standby <그룹> priority <우선순위>", "높은 쪽이 Active (기본 100)"),
        (" standby <그룹> preempt", "HSRP 는 기본이 꺼져 있어서 넣어야 Active 가 돌아옵니다"),
    ], check=[("show standby brief", "한쪽 Active, 다른 쪽 Standby 면 정상")]),
    "j": NO_HSRP, "a": NO_HSRP, "o6": NO_HSRP, "o8": NO_HSRP,
}, keys="hsrp standby 게이트웨이 이중화 active 시스코", rel=["hsrp", "hsrp-show"])

guide("g-igmp", "mcast", "L2 망 멀티캐스트 (IGMP 스누핑 + 질의자)",
      "IPTV·CCTV 멀티캐스트를 받겠다는 포트로만 보내서 망이 넘치지 않게 합니다. 멀티캐스트 라우터가 없으면 질의자를 한 대에만 켭니다.", {
    "c": V([
        ("ip igmp snooping", "IGMP 스누핑을 켭니다 (보통 기본으로 켜져 있음)"),
        ("ip igmp snooping vlan <VLAN번호>", "그 VLAN 에서 켭니다"),
        ("ip igmp snooping querier", "질의자: 주기적으로 '누가 받고 있나' 물어봐서 스누핑 표를 유지합니다. 망에 한 대만"),
    ], check=[("show ip igmp snooping groups", "그룹별로 받는 포트"), ("show ip igmp snooping querier", "질의자가 누구인지")]),
    "j": V([
        ("set protocols igmp-snooping vlan <VLAN이름>", "그 VLAN 에서 스누핑을 켭니다"),
        ("set protocols igmp-snooping vlan <VLAN이름> l2-querier source-address <관리IP>", "질의자. 출발지는 이 장비 IP. " + VER),
    ], check=[("show igmp snooping membership", "그룹별 받는 포트")]),
    "a": V([
        ("interface vlan<VLAN번호>\n ip igmp snooping", "그 VLAN 에서 스누핑 (보통 기본으로 켜져 있음)"),
    ], check=[("show ip igmp groups", "그룹 확인. " + VER)], note="질의자는 버전별로 달라 공식 문서 확인 필요"),
    "o6": V([
        ("ip multicast status enable", "스누핑을 켭니다"),
        ("ip multicast vlan <VLAN번호> querying enable", "질의자. " + VER),
    ], check=[("show ip multicast group", "그룹 확인")]),
    "o8": V([
        ("ip multicast admin-state enable", "스누핑을 켭니다"),
        ("ip multicast vlan <VLAN번호> querying enable", "질의자. " + VER),
    ], check=[("show ip multicast group", "그룹 확인")]),
}, keys="igmp 스누핑 querier 질의자 멀티캐스트 iptv cctv 영상 끊김", rel=["igmp-snoop", "igmp-querier", "igmp-groups"])

guide("g-pim", "mcast", "멀티캐스트 라우팅 (PIM-SM + static RP)",
      "멀티캐스트를 VLAN·대역 너머로 보낼 때. 모든 PIM 라우터에 같은 RP 주소를 넣습니다.", {
    "c": V([
        ("ip multicast-routing", "멀티캐스트 라우팅을 켭니다 (3850 등은 ip multicast-routing distributed)"),
        ("ip pim rp-address <RP주소>", "RP(만남의 장소) 주소. 보통 코어의 루프백. 모든 라우터 같게"),
        ("interface vlan <VLAN번호>\n ip pim sparse-mode", "멀티캐스트가 지나갈 인터페이스마다 PIM 을 켭니다 (IGMP 도 같이 켜짐)"),
    ], check=[("show ip pim neighbor", "PIM 이웃"), ("show ip mroute", "(*,G)·(S,G) 경로")]),
    "j": V([
        ("set protocols pim rp static address <RP주소>", "RP 주소"),
        ("set protocols pim interface irb.<VLAN번호> mode sparse", "인터페이스마다 PIM"),
    ], check=[("show pim neighbors", "PIM 이웃"), ("show multicast route", "멀티캐스트 경로")]),
    "a": V([
        ("ip multicast-routing", "멀티캐스트 라우팅을 켭니다"),
        ("ip pim rp-address <RP주소>", "RP 주소"),
        ("interface vlan<VLAN번호>\n ip pim sparse-mode\n ip igmp", "인터페이스마다 PIM 과 IGMP"),
    ], check=[("show ip pim sparse-mode neighbor", "PIM 이웃"), ("show ip mroute", "경로")]),
    "o6": V([
        ("ip load pim", "PIM 을 올립니다"),
        ("ip pim static-rp 224.0.0.0/4 <RP주소>", "모든 그룹(224.0.0.0/4)의 RP"),
        ('ip pim interface "vlan<VLAN번호>"', "인터페이스마다 PIM"),
        ("ip pim sparse status enable", "PIM-SM 을 켭니다"),
    ], check=[("show ip pim neighbor", "PIM 이웃"), ("show ip mroute", "경로")]),
    "o8": V([
        ("ip load pim", "PIM 을 올립니다"),
        ("ip pim static-rp 224.0.0.0/4 <RP주소>", "모든 그룹의 RP"),
        ('ip pim interface "vlan<VLAN번호>"', "인터페이스마다 PIM"),
        ("ip pim sparse admin-state enable", "PIM-SM 을 켭니다"),
    ], check=[("show ip pim neighbor", "PIM 이웃"), ("show ip mroute", "경로")], note=VER),
}, keys="pim 멀티캐스트 라우팅 rp sparse mroute", rel=["mcast-routing", "pim-sm", "pim-rp", "pim-show", "mroute"])

# ═══════════════════════════ ACL·QoS·보안 ═══════════════════════════
guide("g-acl-block", "acl", "특정 PC(IP) 통신 막기",
      "ACL 을 만들고 → 포트(또는 VLAN)에 겁니다. 만들기만 하고 안 걸면 아무 일도 안 일어납니다.", {
    "c": V([
        ("ip access-list standard <ACL이름>", "표준 ACL 을 만듭니다 (출발지 IP 만 봄)"),
        (" deny host <막을IP>", "이 IP 에서 오는 것을 막습니다"),
        (" permit any", "나머지는 허용. 이 줄이 없으면 끝의 보이지 않는 deny any 때문에 전부 막힙니다"),
        ("interface <포트>", "PC 가 꽂힌 포트(또는 interface vlan <번호>)로"),
        (" ip access-group <ACL이름> in", "들어오는 쪽(in)에 겁니다"),
    ], check=[("show access-lists <ACL이름>", "deny 줄의 matches 가 올라가는지")],
       undo=[("interface <포트>\n no ip access-group <ACL이름> in\nexit\nno ip access-list standard <ACL이름>", "떼고 지우기")]),
    "j": V([
        ("set firewall family ethernet-switching filter <ACL이름> term BLOCK from ip-source-address <막을IP>/32", "규칙 BLOCK: 출발지가 막을 IP 면"),
        ("set firewall family ethernet-switching filter <ACL이름> term BLOCK then discard", "버립니다"),
        ("set firewall family ethernet-switching filter <ACL이름> term ALLOW then accept", "나머지는 허용 (없으면 전부 막힘)"),
        ("set interfaces <포트> unit 0 family ethernet-switching filter input <ACL이름>", "포트 들어오는 쪽에 겁니다"),
    ], check=[("show firewall filter <ACL이름>", "필터 확인 (횟수는 then count 를 넣어야 보임)")],
       undo=[("delete interfaces <포트> unit 0 family ethernet-switching filter\ndelete firewall family ethernet-switching filter <ACL이름>", "떼고 지우기 (설정 모드, commit)")]),
    "a": V([
        ("access-list hardware <ACL이름>", "포트에 거는 hardware ACL 을 만듭니다"),
        (" deny ip <막을IP>/32 any", "이 IP 에서 어디로 가든 막습니다"),
        (" permit ip any any", "나머지는 허용"),
        ("interface <포트>", "PC 가 꽂힌 포트로"),
        (" access-group <ACL이름>", "겁니다 (들어오는 쪽)"),
    ], check=[("show access-list", "ACL 확인")],
       undo=[("interface <포트>\n no access-group <ACL이름>\nexit\nno access-list hardware <ACL이름>", "떼고 지우기")]),
    "o6": V([
        ("policy condition <ACL이름>-c source ip <막을IP>", "조건: 출발지가 막을 IP"),
        ("policy action <ACL이름>-a disposition drop", "동작: 버리기"),
        ("policy rule <ACL이름>-r condition <ACL이름>-c action <ACL이름>-a", "조건과 동작을 이어 규칙으로"),
        ("qos apply", "정책을 실제로 적용합니다. 이걸 안 치면 동작하지 않습니다 (장비 전체에 걸림)"),
    ], check=[("show active policy rule", "적용된 규칙과 맞은 횟수")],
       undo=[("no policy rule <ACL이름>-r\nqos apply", "지우기")]),
    "o8": V([
        ("policy condition <ACL이름>-c source ip <막을IP>", "조건: 출발지가 막을 IP"),
        ("policy action <ACL이름>-a disposition drop", "동작: 버리기"),
        ("policy rule <ACL이름>-r condition <ACL이름>-c action <ACL이름>-a", "조건과 동작을 이어 규칙으로"),
        ("qos apply", "정책을 실제로 적용합니다"),
    ], check=[("show active policy rule", "적용된 규칙과 맞은 횟수")],
       undo=[("no policy rule <ACL이름>-r\nqos apply", "지우기")]),
}, keys="acl 차단 막기 ip 특정 pc 통신 deny access-list 정책", rel=["acl-std", "acl-apply", "acl-show", "acl-remove"])

guide("g-acl-svc", "acl", "특정 서비스(포트 번호)만 막기 (확장 ACL)",
      "예: 사용자 대역에서 서버로 가는 텔넷(23)만 막고 나머지는 허용. 포트 번호를 바꾸면 다른 서비스(22 SSH, 3389 원격 데스크톱, 445 파일 공유).", {
    "c": V([
        ("ip access-list extended <ACL이름>", "확장 ACL (출발지·목적지·프로토콜·포트를 다 봄)"),
        (" deny tcp <대역> <와일드카드> host <서버IP> eq <서비스포트>", "대역에서 서버의 그 TCP 포트로 가는 것을 막습니다"),
        (" permit ip any any", "나머지는 허용"),
        ("interface vlan <VLAN번호>", "사용자 VLAN 의 게이트웨이 인터페이스로"),
        (" ip access-group <ACL이름> in", "그 VLAN 에서 들어오는 쪽에 겁니다"),
    ], check=[("show access-lists <ACL이름>", "matches 확인")],
       undo=[("interface vlan <VLAN번호>\n no ip access-group <ACL이름> in", "떼기")]),
    "j": V([
        ("set firewall family ethernet-switching filter <ACL이름> term BLOCK from ip-source-address <대역>/<프리픽스>", "출발지 대역"),
        ("set firewall family ethernet-switching filter <ACL이름> term BLOCK from ip-destination-address <서버IP>/32", "목적지 서버"),
        ("set firewall family ethernet-switching filter <ACL이름> term BLOCK from ip-protocol tcp", "TCP"),
        ("set firewall family ethernet-switching filter <ACL이름> term BLOCK from destination-port <서비스포트>", "목적지 포트"),
        ("set firewall family ethernet-switching filter <ACL이름> term BLOCK then discard", "버립니다"),
        ("set firewall family ethernet-switching filter <ACL이름> term ALLOW then accept", "나머지 허용"),
        ("set vlans <VLAN이름> forwarding-options filter input <ACL이름>", "사용자 VLAN 에 겁니다"),
    ], check=[("show firewall filter <ACL이름>", "필터 확인")]),
    "a": V([
        ("access-list hardware <ACL이름>", "hardware ACL 을 만듭니다"),
        (" deny tcp <대역>/<프리픽스> <서버IP>/32 eq <서비스포트>", "대역 → 서버의 TCP 포트 막기"),
        (" permit ip any any", "나머지 허용"),
        ("interface <포트>", "사용자 쪽 포트(업링크 아닌 쪽)로"),
        (" access-group <ACL이름>", "겁니다 (들어오는 쪽)"),
    ], check=[("show access-list", "ACL 확인")]),
    "o6": V([
        ("policy condition <ACL이름>-c source ip <대역> mask <마스크> destination ip <서버IP> destination tcp-port <서비스포트>", "조건: 대역 → 서버 TCP 포트"),
        ("policy action <ACL이름>-a disposition drop", "동작: 버리기"),
        ("policy rule <ACL이름>-r condition <ACL이름>-c action <ACL이름>-a", "규칙으로 잇기"),
        ("qos apply", "적용"),
    ], check=[("show active policy rule", "적용 확인")]),
    "o8": V([
        ("policy condition <ACL이름>-c source ip <대역> mask <마스크> destination ip <서버IP> destination tcp-port <서비스포트>", "조건: 대역 → 서버 TCP 포트"),
        ("policy action <ACL이름>-a disposition drop", "동작: 버리기"),
        ("policy rule <ACL이름>-r condition <ACL이름>-c action <ACL이름>-a", "규칙으로 잇기"),
        ("qos apply", "적용"),
    ], check=[("show active policy rule", "적용 확인")]),
}, keys="확장 acl extended 포트 번호 서비스 차단 텔넷 원격데스크톱 3389 445", rel=["acl-ext", "acl-apply"])

guide("g-ratelimit", "qos", "포트 속도 제한 (들어오는·나가는)",
      "한 포트(사용자·CCTV 등)가 대역폭을 다 먹지 못하게 묶어 둡니다.", {
    "c": V([
        ("policy-map LIMIT-IN\n class class-default\n  police 100000000 conform-action transmit exceed-action drop", "들어오는 속도 제한 정책. 100000000 bps = 100M, 넘는 것은 버림"),
        ("interface <포트>\n service-policy input LIMIT-IN", "포트 들어오는 쪽에 겁니다"),
        ("policy-map LIMIT-OUT\n class class-default\n  shape average 100000000", "나가는 속도를 100M 로 다듬습니다(shaping)"),
        ("interface <포트>\n service-policy output LIMIT-OUT", "포트 나가는 쪽에 겁니다"),
    ], check=[("show policy-map interface <포트>", "drop 숫자로 제한이 걸리는지")],
       note="2960 계열은 나가는 쪽을 interface 에서 srr-queue bandwidth limit <퍼센트> 로 합니다"),
    "j": V([
        ("set firewall policer LIMIT if-exceeding bandwidth-limit 100m burst-size-limit 1m\nset firewall policer LIMIT then discard", "100M 넘으면 버리는 policer"),
        ("set firewall family ethernet-switching filter LIMIT-F term ALL then policer LIMIT\nset firewall family ethernet-switching filter LIMIT-F term ALL then accept", "모든 트래픽에 policer 를 거는 필터"),
        ("set interfaces <포트> unit 0 family ethernet-switching filter input LIMIT-F", "포트 들어오는 쪽에 겁니다"),
        ("set class-of-service interfaces <포트> shaping-rate 100m", "나가는 쪽은 shaping 으로 100M"),
    ], check=[("show firewall", "policer 카운터")]),
    "a": V([
        ("mls qos enable", "QoS 기능을 켭니다"),
        ("policy-map LIMIT-IN\n class default\n  police single-rate 100000 100000 100000 action drop-red", "들어오는 쪽 100000 kbps(100M) 제한. " + VER),
        ("interface <포트>\n service-policy input LIMIT-IN", "포트에 겁니다"),
        ("interface <포트>\n egress-rate-limit 100m", "나가는 쪽 100M"),
    ], check=[("show mls qos interface <포트>", "QoS 상태")]),
    "o6": V([
        ("qos port <포트> maximum ingress-bandwidth <속도>", "들어오는 쪽 최대 속도 (100M 처럼)"),
        ("qos port <포트> maximum egress-bandwidth <속도>", "나가는 쪽 최대 속도"),
        ("qos apply", "적용"),
    ], check=[("show qos port <포트>", "설정 확인")]),
    "o8": V([
        ("qos port <포트> maximum ingress-bandwidth <속도>", "들어오는 쪽 최대 속도 (100M 처럼)"),
        ("qos port <포트> maximum egress-bandwidth <속도>", "나가는 쪽 최대 속도"),
        ("qos apply", "적용"),
    ], check=[("show qos port <포트>", "설정 확인")]),
}, keys="속도 제한 대역폭 rate limit police shaping qos 업로드 다운로드", rel=["rate-in", "rate-out", "qos-show"])

guide("g-voice", "qos", "IP 전화 포트 (음성 VLAN + 우선순위)",
      "전화기 뒤에 PC 를 꽂는 포트. PC 는 데이터 VLAN, 전화는 음성 VLAN 으로 가고 음성이 먼저 나가게 합니다.", {
    "c": V([
        ("vlan <음성VLAN>\n name <음성VLAN이름>", "음성 VLAN 을 만듭니다"),
        ("mls qos", "QoS 를 켭니다 (Catalyst 9000 은 필요 없음)"),
        ("interface <포트>", "전화가 꽂히는 포트로"),
        (" switchport mode access\n switchport access vlan <VLAN번호>", "PC 용 데이터 VLAN"),
        (" switchport voice vlan <음성VLAN>", "전화는 CDP/LLDP 로 이 VLAN 을 알아 가서 태그를 붙여 보냅니다"),
        (" mls qos trust dscp", "전화가 매긴 우선순위(DSCP)를 믿습니다"),
        (" spanning-tree portfast", "바로 열리게"),
    ], check=[("show interfaces <포트> switchport", "Voice VLAN 확인")]),
    "j": V([
        ("set vlans <음성VLAN이름> vlan-id <음성VLAN>", "음성 VLAN 을 만듭니다"),
        ("set switch-options voip interface <포트>.0 vlan <음성VLAN이름> forwarding-class expedited-forwarding", "포트에 음성 VLAN 을 붙이고 높은 우선순위 큐로"),
        ("set protocols lldp-med interface <포트>", "전화에 LLDP-MED 로 음성 VLAN 을 알려 줍니다"),
    ], check=[("show ethernet-switching interface <포트>", "VLAN 확인")]),
    "a": V([
        ("vlan database\n vlan <음성VLAN> name <음성VLAN이름>", "음성 VLAN 을 만듭니다"),
        ("interface <포트>", "전화가 꽂히는 포트로"),
        (" switchport access vlan <VLAN번호>", "PC 용 데이터 VLAN"),
        (" switchport voice vlan <음성VLAN>", "전화가 LLDP-MED 로 받아 가는 음성 VLAN"),
    ], check=[("show interface <포트> switchport", "Voice VLAN 확인")]),
    "o6": (None, "AOS 는 음성 VLAN 을 tagged 로 붙이고 LLDP-MED network-policy 로 전화에 알려 줍니다. " + VER),
    "o8": (None, "AOS 는 음성 VLAN 을 tagged 로 붙이고 LLDP-MED network-policy 로 전화에 알려 줍니다. " + VER),
}, keys="음성 voice vlan ip 전화 인터넷 전화 voip qos 우선순위", rel=["voice-vlan", "qos-trust"])

guide("g-portsec", "psec", "포트 보안 (공유기·허브 몰래 꽂기 막기)",
      "포트 하나에 붙을 수 있는 MAC 개수를 제한합니다. 위반 때 어떻게 할지(막기/끄기)도 정합니다.", {
    "c": V([
        ("interface <포트>", "PC 포트로"),
        (" switchport mode access", "포트 보안은 access(또는 trunk 고정) 포트에서만 됩니다"),
        (" switchport port-security maximum <최대MAC>", "허용할 MAC 개수"),
        (" switchport port-security violation restrict", "넘는 MAC 은 막고 로그만 남깁니다. 기본값 shutdown 은 포트를 통째로 끕니다"),
        (" switchport port-security mac-address sticky", "처음 배운 MAC 을 설정에 적어 둡니다 (저장하면 재부팅 후에도 유지)"),
        (" switchport port-security", "마지막에 포트 보안을 켭니다"),
        ("errdisable recovery cause psecure-violation\nerrdisable recovery interval 300", "shutdown 방식일 때 꺼진 포트를 300초 뒤 자동으로 살립니다 (선택)"),
    ], check=[("show port-security interface <포트>", "Secure-up 이고 MAC 개수·위반 횟수"),
              ("show port-security address", "배운 MAC 목록")]),
    "j": V([
        ("set switch-options interface <포트>.0 interface-mac-limit <최대MAC> packet-action drop", "MAC 개수 제한. 넘는 MAC 의 패킷은 버림"),
    ], check=[("show ethernet-switching interface <포트> detail", "MAC 제한 확인")]),
    "a": V([
        ("interface <포트>", "PC 포트로"),
        (" switchport port-security maximum <최대MAC>", "허용할 MAC 개수"),
        (" switchport port-security violation restrict", "넘으면 막고 로그"),
        (" switchport port-security", "포트 보안을 켭니다"),
    ], check=[("show port-security interface <포트>", "상태 확인")]),
    "o6": V([
        ("port-security <포트>", "포트 보안을 켭니다"),
        ("port-security <포트> maximum <최대MAC>", "MAC 개수"),
        ("port-security <포트> violation restrict", "넘으면 막기"),
    ], check=[("show port-security", "상태 확인")], note=VER),
    "o8": V([
        ("port-security port <포트> admin-status enable", "포트 보안을 켭니다"),
        ("port-security port <포트> maximum <최대MAC>", "MAC 개수"),
        ("port-security port <포트> violation restrict", "넘으면 막기"),
    ], check=[("show port-security", "상태 확인")], note=VER),
}, keys="포트 보안 port security mac 제한 공유기 허브 sticky violation err-disabled", rel=["port-sec", "port-sec-show", "errdisable"])

guide("g-dot1x", "psec", "802.1X 포트 인증 (NAC·RADIUS 연동)",
      "인증 서버가 허락한 사용자·단말만 포트를 열어 줍니다. 서버 등록 → 802.1X 켜기 → 포트에 걸기 순서.", {
    "c": V([
        ("username <사용자> privilege 15 secret <비밀번호>", "aaa new-model 을 켜면 로그인 방식이 바뀌어서 로컬 계정을 먼저 만듭니다"),
        ("aaa new-model", "AAA 를 켭니다"),
        ("radius server <서버이름>\n address ipv4 <인증서버> auth-port 1812 acct-port 1813\n key <비밀키>", "RADIUS(NAC) 서버 등록"),
        ("aaa authentication dot1x default group radius", "802.1X 인증은 RADIUS 로"),
        ("dot1x system-auth-control", "장비 전체에서 802.1X 를 켭니다"),
        ("interface <포트>\n switchport mode access", "인증할 PC 포트로"),
        (" authentication port-control auto", "인증되기 전까지 포트를 막아 둡니다"),
        (" dot1x pae authenticator", "이 포트가 인증을 묻는 쪽(authenticator)"),
    ], check=[("show authentication sessions", "포트별 인증 결과(Authorized)"), ("show aaa servers", "서버 상태")]),
    "j": V([
        ("set access radius-server <인증서버> secret <비밀키>", "RADIUS 서버 등록"),
        ("set access profile DOT1X authentication-order radius\nset access profile DOT1X radius authentication-server <인증서버>", "인증 프로필"),
        ("set protocols dot1x authenticator authentication-profile-name DOT1X", "802.1X 가 이 프로필을 씁니다"),
        ("set protocols dot1x authenticator interface <포트> supplicant multiple", "포트에 걸기. multiple = 여러 단말 각각 인증"),
    ], check=[("show dot1x interface", "인증 상태")]),
    "a": V([
        ("radius-server host <인증서버> key <비밀키>", "RADIUS 서버 등록"),
        ("aaa authentication dot1x default group radius", "802.1X 인증은 RADIUS 로"),
        ("interface <포트>\n dot1x port-control auto", "포트에 걸기"),
    ], check=[("show dot1x supplicant", "인증 상태")]),
    "o6": V([
        ("aaa radius-server <서버이름> host <인증서버> key <비밀키>", "RADIUS 서버 등록"),
        ("aaa authentication 802.1x <서버이름>", "802.1X 인증은 이 서버로"),
        ("vlan port mobile <포트>", "포트를 mobile(인증 결과로 VLAN 이 바뀔 수 있게)로"),
        ("vlan port <포트> 802.1x enable", "포트에 802.1X 를 켭니다"),
    ], check=[("show 802.1x users", "인증 사용자")], note=VER),
    "o8": V([
        ("aaa radius-server <서버이름> host <인증서버> key <비밀키>", "RADIUS 서버 등록"),
        ("aaa device-authentication 802.1x <서버이름>", "802.1X 인증은 이 서버로"),
        ("unp port <포트> port-type edge", "AOS8 은 UNP 로 합니다. 포트를 사용자 포트(edge)로"),
        ("unp port <포트> 802.1x-authentication", "포트에 802.1X 를 켭니다"),
    ], check=[("show unp user", "인증 사용자")], note=VER),
}, keys="802.1x dot1x 인증 nac radius 지니언스 포트 인증 unp", rel=["dot1x", "dot1x-show", "radius-server"],
   warn="업링크·서버 포트에는 걸지 마세요. 인증 서버와 통신이 끊기면 그 포트들이 모두 막힙니다.")

guide("g-dhcp-snoop", "dsec", "불법 DHCP·ARP 위조 막기 (DHCP 스누핑 → ARP 검사)",
      "누가 공유기를 꽂아 엉뚱한 IP 를 뿌리는 것을 막고(스누핑), 그 표를 이용해 ARP 위조까지 막습니다. 순서가 중요합니다.", {
    "c": V([
        ("ip dhcp snooping", "DHCP 스누핑 기능을 켭니다"),
        ("ip dhcp snooping vlan <VLAN번호>", "보호할 VLAN"),
        ("no ip dhcp snooping information option", "option 82 를 끕니다. 안 끄면 일부 DHCP 서버가 응답을 버려 IP 를 못 받습니다"),
        ("interface <업링크포트>\n ip dhcp snooping trust", "진짜 DHCP 서버 쪽(업링크)은 믿습니다. 이걸 빼먹으면 모두 IP 를 못 받습니다"),
        ("ip arp inspection vlan <VLAN번호>", "ARP 검사(DAI): 스누핑 표와 다른 ARP 를 버립니다. 스누핑이 먼저 동작해야 합니다"),
        ("interface <업링크포트>\n ip arp inspection trust", "업링크는 ARP 검사에서도 믿습니다"),
    ], check=[("show ip dhcp snooping", "켜진 VLAN·trust 포트"), ("show ip dhcp snooping binding", "IP·MAC·포트 표가 쌓이는지"),
              ("show ip arp inspection statistics", "버린 ARP 숫자")],
       undo=[("no ip arp inspection vlan <VLAN번호>\nno ip dhcp snooping", "장애 나면 바로 끄기")],
       note="고정 IP 장비(프린터·서버)는 스누핑 표에 없어 ARP 검사에 걸립니다. ARP ACL 로 따로 허용하세요"),
    "j": V([
        ("set vlans <VLAN이름> forwarding-options dhcp-security", "그 VLAN 에서 DHCP 스누핑을 켭니다"),
        ("set vlans <VLAN이름> forwarding-options dhcp-security group UPLINK overrides trusted\nset vlans <VLAN이름> forwarding-options dhcp-security group UPLINK interface <업링크포트>.0", "업링크가 access 포트일 때만 trust 로 (트렁크는 기본 trust)"),
        ("set vlans <VLAN이름> forwarding-options dhcp-security arp-inspection", "ARP 검사"),
    ], check=[("show dhcp-security binding", "표 확인")],
       undo=[("delete vlans <VLAN이름> forwarding-options dhcp-security", "끄기")]),
    "a": V([
        ("service dhcp-snooping", "DHCP 스누핑 기능을 켭니다"),
        ("interface vlan<VLAN번호>\n ip dhcp snooping", "보호할 VLAN"),
        ("interface <업링크포트>\n ip dhcp snooping trust", "업링크는 믿기"),
        ("interface vlan<VLAN번호>\n arp security", "ARP 검사"),
    ], check=[("show ip dhcp snooping binding", "표 확인")], undo=[("no service dhcp-snooping", "끄기")]),
    "o6": V([
        ("ip helper dhcp-snooping enable", "DHCP 스누핑을 켭니다 (VLAN 별: ip helper dhcp-snooping vlan <VLAN번호> enable)"),
        ("ip helper dhcp-snooping port <업링크포트> trust", "업링크는 믿기"),
    ], check=[("show ip helper dhcp-snooping binding", "표 확인")], undo=[("ip helper dhcp-snooping disable", "끄기")],
       note="ARP 위조는 포트마다 ip-source-filter 로 비슷하게 막습니다. " + VER),
    "o8": V([
        ("dhcp-snooping admin-state enable", "DHCP 스누핑을 켭니다"),
        ("dhcp-snooping port <업링크포트> trust", "업링크는 믿기"),
    ], check=[("show dhcp-snooping binding", "표 확인")], undo=[("dhcp-snooping admin-state disable", "끄기")],
       note="ARP 위조는 포트마다 ip-source-filter 로 비슷하게 막습니다. " + VER),
}, keys="dhcp 스누핑 snooping 불법 공유기 arp 검사 dai 스푸핑 trust", rel=["dhcp-snoop", "arp-inspect", "dhcp-snoop-show", "dhcp-snoop-off"],
   warn="업무 시간에 켜면 trust 를 빠뜨린 순간 그 VLAN 전체가 IP 를 못 받습니다. 한 VLAN 씩, 업무 외 시간에.")

guide("g-storm", "misc", "브로드캐스트 폭주 막기 (storm control)",
      "루프나 고장 난 NIC 때문에 브로드캐스트가 쏟아질 때 포트 대역폭의 일정 비율 이상은 버립니다.", {
    "c": V([
        ("interface <포트>", "사용자 포트로 (업링크엔 보통 안 겁니다)"),
        (" storm-control broadcast level 10", "브로드캐스트가 포트 대역폭의 10% 를 넘으면 버립니다"),
        (" storm-control multicast level 10", "멀티캐스트도 (IPTV 망이면 넣지 마세요)"),
        (" storm-control action trap", "넘을 때 SNMP 트랩을 보냅니다 (shutdown 으로 하면 포트를 끔)"),
    ], check=[("show storm-control <포트>", "기준값과 현재 값")]),
    "j": V([
        ("set forwarding-options storm-control-profiles SC all bandwidth-percentage 10", "전체(브로드·멀티·모르는 유니캐스트) 10% 프로필"),
        ("set interfaces <포트> unit 0 family ethernet-switching storm-control SC", "포트에 겁니다"),
    ], check=[("show ethernet-switching interface <포트> detail", "storm-control 확인")]),
    "a": V([
        ("interface <포트>\n storm-control broadcast level 10", "브로드캐스트 10% 넘으면 버림"),
    ], check=[("show running-config interface <포트>", "설정 확인")]),
    "o6": (None, "AOS6 는 버전별로 달라 공식 문서 확인 필요 (flood-limit)"),
    "o8": (None, "AOS8 는 버전별로 달라 공식 문서 확인 필요 (flood-limit)"),
}, keys="스톰 storm broadcast 브로드캐스트 폭주 루프", rel=["storm"])

# ═══════════════════════════ 작업 안전·점검 (조회 순서) ═══════════════════════════
guide("g-safe", "save", "원격 작업 전 안전장치 (자동 되돌리기)",
      "원격으로 관리 IP·VLAN·ACL 을 바꾸다 접속이 끊기면 현장에 가야 합니다. 일정 시간 뒤 자동으로 되돌아가게 걸어 두고 작업합니다.", {
    "c": V([
        ("show running-config", "지금 설정을 터미널 로그로 남겨 둡니다 (OiTerm 로그 저장)"),
        ("write memory", "작업 전 상태를 저장합니다. 이게 되돌아갈 지점입니다"),
        ("reload in 10", "10분 뒤 재부팅을 예약합니다. 작업하다 끊겨도 10분 뒤 저장된(작업 전) 설정으로 다시 뜹니다"),
        ("configure terminal", "이제 작업합니다. 작업 중에는 write memory 하지 마세요"),
        ("end", "작업을 마치고"),
        ("reload cancel", "접속이 살아 있으면 예약한 재부팅을 취소합니다"),
        ("write memory", "확인이 끝났으면 그때 저장합니다"),
    ], check=[("show reload", "예약된 재부팅 시각")]),
    "j": V([
        ("configure", "설정 모드로"),
        ("show | compare", "작업한 뒤 바꾼 내용을 확인합니다"),
        ("commit confirmed 5", "적용하되, 5분 안에 다시 commit 하지 않으면 자동으로 이전 설정으로 돌아갑니다"),
        ("commit", "새 창으로 접속되는 것을 확인했으면 확정합니다"),
    ], check=[("show system commit", "commit 기록")], note="되돌리려면 설정 모드에서 rollback 1 → commit"),
    "a": V([
        ("write", "작업 전 상태를 저장합니다. 이게 되돌아갈 지점입니다"),
        ("configure terminal", "작업합니다. 확인이 끝날 때까지 저장(write)하지 마세요"),
        ("end", "작업을 마치고 새 창으로 접속되는지 확인합니다"),
        ("write", "확인이 끝났으면 그때 저장합니다"),
    ], note="자동 되돌림 기능은 따로 없습니다. 작업하다 끊기면 현장(또는 다른 경로)에서 reload 하면 저장된(작업 전) 설정으로 뜹니다"),
    "o6": V([
        ("show running-directory", "working 과 certified 가 같은지(Synchronized) 확인합니다"),
        ("write memory", "작업이 끝나고 새 창으로 접속되는지 확인한 뒤에만 저장합니다"),
        ("copy working certified", "확정"),
    ], note="AOS 는 친 명령이 바로 적용됩니다. 작업하다 끊기면 저장하지 않은 상태이므로 reload 하면 certified(작업 전) 설정으로 뜹니다"),
    "o8": V([
        ("show running-directory", "working 과 certified 가 같은지 확인합니다"),
        ("write memory flash-synchro", "작업이 끝나고 확인한 뒤에만 저장합니다"),
    ], note="AOS 는 친 명령이 바로 적용됩니다. 작업하다 끊기면 저장하지 않은 상태이므로 reload 하면 이전 설정으로 뜹니다"),
}, keys="원격 작업 안전 자동 되돌리기 commit confirmed reload in 끊김 대비 롤백", rel=["commit-confirm", "rollback", "save"], mode="show")

guide("g-backup", "save", "작업 전 설정 백업",
      "설정을 바꾸기 전에 지금 설정을 파일로 남깁니다. TFTP 서버(PC 에 띄운 TFTP)로 보내거나 터미널 로그로 저장합니다.", {
    "c": V([
        ("show running-config", "터미널 로그 저장을 켠 상태로 치면 그대로 텍스트로 남습니다 (가장 간단)"),
        ("copy running-config tftp://<TFTP서버>/<파일>", "TFTP 서버로 설정 파일을 보냅니다. 물어보면 엔터"),
    ]),
    "j": V([
        ("show configuration | display set | save /var/tmp/<파일>", "set 형식 텍스트로 장비 안에 저장"),
        ("file copy /config/juniper.conf.gz scp://<사용자>@<TFTP서버>/<파일>", "설정 파일을 SCP 로 PC/서버에 복사"),
    ]),
    "a": V([
        ("show running-config", "터미널 로그로 남기기"),
        ("copy running-config tftp://<TFTP서버>/<파일>", "TFTP 서버로 보냅니다"),
    ]),
    "o6": V([
        ("show configuration snapshot", "터미널 로그로 남기기"),
    ], note="파일은 PC 에서 FTP/SCP 로 /flash/working/boot.cfg 를 가져옵니다"),
    "o8": V([
        ("show configuration snapshot", "터미널 로그로 남기기"),
    ], note="파일은 PC 에서 SCP/SFTP 로 /flash/working/vcboot.cfg 를 가져옵니다"),
}, keys="백업 backup 설정 저장 tftp 파일 작업 전", rel=["backup", "show-run"], mode="show")

guide("g-check-daily", "trouble", "정기 점검 순서 (장비 상태 한 바퀴)",
      "유지보수 정기 점검 때 이 순서대로 치고 결과를 터미널 로그로 남기면 점검표 작성이 쉽습니다.", {
    "c": V([
        ("show version", "OS 버전·업타임(언제 재부팅됐는지)"),
        ("show processes cpu sorted", "CPU 사용률 (5분 평균 높으면 원인 확인)"),
        ("show memory statistics", "메모리 사용률"),
        ("show environment all", "온도·팬·전원 이상 여부"),
        ("show interfaces status", "포트 연결 상태, err-disabled 포트"),
        ("show interfaces counters errors", "에러 많이 난 포트 (CRC = 케이블·광 문제)"),
        ("show logging", "최근 로그에 경고(%)가 있는지"),
        ("show spanning-tree root", "루트가 바뀌지 않았는지"),
    ]),
    "j": V([
        ("show version", "OS 버전"),
        ("show system uptime", "업타임"),
        ("show chassis routing-engine", "CPU·메모리"),
        ("show chassis environment", "온도·팬·전원"),
        ("show chassis alarms", "하드웨어 경보"),
        ("show interfaces terse", "포트 상태"),
        ("show log messages | last 50", "최근 로그"),
    ]),
    "a": V([
        ("show system", "모델·업타임"),
        ("show cpu", "CPU"),
        ("show memory", "메모리"),
        ("show system environment", "온도·팬·전원"),
        ("show interface brief", "포트 상태"),
        ("show log", "최근 로그"),
    ]),
    "o6": V([
        ("show microcode", "OS 버전"),
        ("show system", "업타임"),
        ("show health", "CPU·메모리"),
        ("show temperature\nshow fan\nshow powersupply", "온도·팬·전원"),
        ("show interfaces status", "포트 상태"),
        ("show log swlog", "최근 로그"),
        ("show running-directory", "working·certified 가 같은지 (저장 안 한 변경이 있는지)"),
    ]),
    "o8": V([
        ("show microcode", "OS 버전"),
        ("show system", "업타임"),
        ("show health", "CPU·메모리"),
        ("show temperature\nshow fan\nshow powersupply", "온도·팬·전원"),
        ("show interfaces status", "포트 상태"),
        ("show log swlog", "최근 로그"),
        ("show running-directory", "working·certified 가 같은지"),
    ]),
}, keys="정기 점검 상태 점검 cpu 메모리 온도 로그 점검표 유지보수", rel=["show-version", "cpu", "memory", "env", "intf-status", "log-show"], mode="show")

guide("g-port-trouble", "trouble", "포트가 안 될 때 확인 순서",
      "'인터넷이 안 돼요' 하면 이 순서로 좁혀 갑니다: 링크 → 꺼짐 이유 → 에러 → VLAN → MAC.", {
    "c": V([
        ("show interfaces status", "그 포트가 connected 인지. notconnect = 케이블·단말, err-disabled = 보안 기능이 끔"),
        ("show interfaces status err-disabled", "err-disabled 면 이유(bpduguard·psecure 등)"),
        ("show interfaces <포트>", "up/up 인지, input errors·CRC 가 늘어나는지 (늘면 케이블·광)"),
        ("show interfaces <포트> switchport", "VLAN 이 맞는지"),
        ("show mac address-table interface <포트>", "단말 MAC 이 보이는지 (안 보이면 단말이 아무것도 안 보내는 것)"),
        ("show logging | include <포트>", "그 포트 관련 로그 (up/down 반복 = flapping)"),
        ("test cable-diagnostics tdr interface <포트>", "케이블 검사 (잠깐 끊김). 결과는 show cable-diagnostics tdr interface <포트>"),
    ]),
    "j": V([
        ("show interfaces terse <포트>", "up/up 인지"),
        ("show interfaces <포트> extensive | match error", "에러 카운터"),
        ("show ethernet-switching interface <포트>", "VLAN"),
        ("show ethernet-switching table interface <포트>", "단말 MAC"),
        ("show log messages | match <포트>", "관련 로그"),
    ]),
    "a": V([
        ("show interface brief", "포트 상태"),
        ("show interface <포트>", "상태와 에러 카운터"),
        ("show interface <포트> switchport", "VLAN"),
        ("show mac address-table interface <포트>", "단말 MAC"),
        ("show log | include <포트>", "관련 로그"),
    ]),
    "o6": V([
        ("show interfaces status", "포트 상태"),
        ("show interfaces <포트>", "상태"),
        ("show interfaces <포트> counters errors", "에러 카운터"),
        ("show vlan port <포트>", "VLAN"),
        ("show mac-address-table <포트>", "단말 MAC"),
    ]),
    "o8": V([
        ("show interfaces status", "포트 상태"),
        ("show interfaces port <포트>", "상태"),
        ("show interfaces port <포트> counters errors", "에러 카운터. " + VER),
        ("show vlan members port <포트>", "VLAN"),
        ("show mac-learning port <포트>", "단말 MAC"),
    ]),
}, keys="포트 장애 안됨 인터넷 안됨 링크 다운 err-disabled 에러 crc 확인 순서 트러블슈팅", rel=["intf-status", "intf-detail", "intf-errors", "mac-port", "cable-test", "errdisable"], mode="show")

guide("g-find-host", "trouble", "IP 로 단말이 꽂힌 포트 찾기",
      "IP 만 알 때: 게이트웨이(L3)에서 IP → MAC, 그 MAC 이 어느 포트인지 → 그 포트가 다른 스위치면 LLDP 로 따라가서 반복.", {
    "c": V([
        ("ping <대상IP>", "ARP 표에 올라오게 한 번 ping 합니다 (응답이 없어도 됨)"),
        ("show ip arp <대상IP>", "게이트웨이 장비에서 IP → MAC"),
        ("show mac address-table address <MAC>", "그 MAC 이 어느 포트로 배웠는지"),
        ("show lldp neighbors", "그 포트 너머가 스위치면 어느 장비인지 → 그 장비에 접속해서 위 단계를 반복 (시스코끼리는 show cdp neighbors)"),
    ]),
    "j": V([
        ("ping <대상IP> count 2", "ARP 표에 올라오게"),
        ("show arp no-resolve | match <대상IP>", "IP → MAC"),
        ("show ethernet-switching table | match <MAC>", "MAC → 포트 (MAC 형식 aa:bb:cc:dd:ee:ff)"),
        ("show lldp neighbors", "다음 스위치"),
    ]),
    "a": V([
        ("ping <대상IP>", "ARP 표에 올라오게"),
        ("show arp | include <대상IP>", "IP → MAC"),
        ("show mac address-table | include <MAC>", "MAC → 포트"),
        ("show lldp neighbors", "다음 스위치"),
    ]),
    "o6": V([
        ("ping <대상IP>", "ARP 표에 올라오게"),
        ("show arp | grep <대상IP>", "IP → MAC"),
        ("show mac-address-table | grep <MAC>", "MAC → 포트 (형식 aa:bb:cc:dd:ee:ff)"),
        ("show lldp remote-system", "다음 스위치"),
    ]),
    "o8": V([
        ("ping <대상IP>", "ARP 표에 올라오게"),
        ("show arp | grep <대상IP>", "IP → MAC"),
        ("show mac-learning mac-address <MAC>", "MAC → 포트"),
        ("show lldp remote-system", "다음 스위치"),
    ]),
}, keys="단말 찾기 위치 포트 찾기 ip mac 추적 어느 포트 arp", rel=["arp-find", "mac-find", "lldp-show"], mode="show")

guide("g-loop", "trouble", "루프(브로드캐스트 폭주) 의심될 때",
      "망 전체가 느려지고 CPU 가 치솟고 포트 불이 미친 듯 깜빡이면 루프를 의심합니다. 어느 포트인지 찾아서 끊습니다.", {
    "c": V([
        ("show processes cpu sorted", "CPU 가 높은지 (루프면 보통 90% 넘음)"),
        ("show logging | include MACFLAP|loop", "같은 MAC 이 두 포트를 오간다는 로그(MACFLAP) → 그 두 포트 사이에 루프"),
        ("show interfaces counters", "브로드캐스트·멀티캐스트 숫자가 비정상적으로 큰 포트"),
        ("show spanning-tree detail | include ieee|occurr|from", "토폴로지 변경이 계속 일어나는지, 어느 포트에서인지"),
        ("interface <포트>\n shutdown", "찾은 포트를 꺼서 확인합니다 (설정 모드). 정상이 되면 그 포트 너머 단말·허브 확인"),
    ]),
    "j": V([
        ("show chassis routing-engine", "CPU"),
        ("show log messages | match MAC", "MAC 이동 로그"),
        ("show interfaces <포트> extensive | match cast", "브로드캐스트·멀티캐스트 카운터"),
        ("show spanning-tree bridge detail", "토폴로지 변경 횟수"),
    ]),
    "a": V([
        ("show cpu", "CPU"),
        ("show log | include loop|thrash", "루프 감지(thrash) 로그"),
        ("show spanning-tree", "상태"),
    ]),
    "o6": V([
        ("show health", "CPU"),
        ("show log swlog", "로그"),
        ("show spantree", "토폴로지 변경"),
    ]),
    "o8": V([
        ("show health", "CPU"),
        ("show log swlog", "로그"),
        ("show spantree", "토폴로지 변경"),
    ]),
}, keys="루프 loop 브로드캐스트 폭주 망 느림 cpu 높음 macflap 장애", rel=["cpu", "stp-show", "storm", "log-show"], mode="show")
