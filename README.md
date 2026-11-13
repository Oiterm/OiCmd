# OiCmd

네트워크 장비 명령어 사전 — **시스코 · 주니퍼 · 얼라이드 · 알카텔** 명령어를 하는 일별로 나란히 보고, 다른 벤더 명령어로 바꾸고, VLAN·포트 설정문을 만들어 주는 Windows 프로그램입니다.

| 벤더 | OS |
|---|---|
| 시스코 | IOS / IOS-XE |
| 주니퍼 | Junos (EX, ELS) |
| 얼라이드텔레시스 | AlliedWare Plus |
| 알카텔-루슨트 엔터프라이즈 | OmniSwitch AOS 6, AOS 8 |

## 할 수 있는 것

- **명령어 사전**: 기본 정보, 인터페이스, VLAN, MAC·ARP·LLDP, LACP, 스패닝 트리, IP·라우팅, 관리·보안, 로그·장애, 미러링, 저장·백업 — 77개 항목을 벤더별로 나란히. 한글(맥 주소, 트렁크)이나 명령어 줄임말(`sh int status`)로 찾습니다.
- **명령어 변환**: 아는 명령어를 넣으면 다른 벤더 명령어로. 포트 이름(`Gi1/0/5` → `ge-0/0/4` → `port1.0.5` → `1/5` → `1/1/5`), MAC 형식, 마스크↔프리픽스도 바꿔 채웁니다.
- **설정 만들기**: VLAN, access/trunk 포트, LACP, 관리 IP, NTP·syslog·SNMP·SSH 를 넣으면 벤더별 설정문.
- **내 명령어**: 직접 추가하고, 기본 명령어를 고치고, 실제 장비에서 확인한 것은 ✓ 표시.

## 설치

[Releases](https://github.com/Oiterm/OiCmd/releases/latest) 에서 `OiCmd-Setup-<버전>.exe` (관리자 권한 필요 없음) 또는 포터블 zip.
자동 업데이트는 서명(Ed25519)이 맞는 파일만 설치합니다.

## 주의

기본 명령어는 각 벤더 공식 문서를 기준으로 넣었지만 장비 모델·OS 버전에 따라 다를 수 있습니다. 설정을 넣기 전에 꼭 확인하고, 가능하면 랩이나 콘솔로 붙은 장비에서 먼저 시험하세요. 프로그램 안에서 확인한 명령어는 ✓ 표시로 구분됩니다.

틀린 명령어를 찾으면 [Issues](https://github.com/Oiterm/OiCmd/issues) 로 알려 주세요.

개발: [DEVELOP.md](DEVELOP.md)

라이선스: MIT ([LICENSE.txt](LICENSE.txt)). 들어 있는 오픈소스는 [THIRD_PARTY_LICENSES.txt](internal/server/ui/THIRD_PARTY_LICENSES.txt).
