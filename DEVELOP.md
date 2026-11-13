# OiCmd 개발 메모

## 빌드

Go 1.27 이상. 외부 C 라이브러리가 없어서 어느 OS 에서든 윈도우 exe 를 만들 수 있습니다.

```
./build.sh                       # dist/ 에 OiCmd-Setup-<버전>.exe + 포터블 zip (makensis, python3, zip 필요)
go run ./cmd/oicmd serve          # 창 없이 화면만 (모든 OS). 출력된 주소를 브라우저로 열기
go test ./... && node tools/jstest/run.js
```

- `third_party/`: OiNMS 와 같은 go-webview2(+go-winloader), golang.org/x/sys. `replace` 로 씀.
- `OICMD_HOME` 환경 변수로 데이터 폴더를 바꿀 수 있습니다(시험용).

## 구조

```
cmd/oicmd             진입점. gui_windows.go: WebView2 창(하나만 뜸), 업데이트 설치. other.go: 윈도우 외는 serve
internal/app          버전, 데이터 폴더(%APPDATA%\OiCmd), 캐시 폴더(%LOCALAPPDATA%\OiCmd)
internal/server       127.0.0.1 웹 서버 + 화면(ui/, embed). /api/ 는 실행할 때마다 바뀌는 토큰 필요, Host 확인
  ui/commands.json    기본 명령어 데이터 (tools/gendata/commands.py 로 만듦 — 직접 고치지 말 것)
  ui/js/core.js       공통, 내 데이터(user.json) 읽기·저장
  ui/js/match.js      명령어 맞추기(줄임말), 값 바꾸기(포트·MAC·마스크)
  ui/js/gen.js        설정 만들기 (벤더별)
  ui/js/app.js        화면
internal/update       OiNMS 의 것과 같음 (서명 확인 자동 업데이트)
tools/gendata         명령어 데이터 원본
tools/jstest          화면 JS 시험 (node)
tools/mkrelease       latest.json 서명, 오프라인 업데이트 묶음
tools/genres          exe 아이콘·버전 리소스
tools/mknotice.py     오픈소스 라이선스 고지 다시 만들기
```

## 명령어 데이터 고치기

`tools/gendata/commands.py` 의 `add(...)` 를 고치고 `python3 tools/gendata/commands.py`.
CI 가 commands.json 이 원본과 같은지, 형식이 맞는지(go test) 검사합니다.

- 벤더 키: `c` 시스코, `j` 주니퍼, `a` 얼라이드, `o6` 알카텔 AOS6, `o8` 알카텔 AOS8
- 값: `"명령"`, `("명령", "메모")`, `(None, "없는 이유")`
- 바꿀 자리는 `<포트>` `<VLAN번호>` `<IP>` `<마스크>` `<프리픽스>` `<게이트웨이>` `<MAC>` `<이름>` `<설명>` …
  변환에서 이 이름으로 값을 옮기므로 같은 뜻이면 같은 이름을 씁니다. `<포트>`·`<받는포트>`·`<MAC>` 은 벤더 형식으로 바꿉니다.
- 명령어 글자가 바뀌면 그 칸의 사용자 [확인됨] 표시는 자동으로 풀립니다(글자 해시로 비교).
- 확실하지 않은 것은 메모에 "버전별 확인 필요"를 붙이거나 `(None, ...)` 으로 둡니다. 틀린 명령은 현장에서 사고가 납니다.

## 릴리즈 (자동 업데이트)

1. `internal/app/app.go` 의 `Version` 을 올리고 `CHANGELOG.md` 에 `## <버전>` 을 쓴다
2. GitHub **Actions → release → Run workflow** (또는 `v1.0.0` 태그 push)
3. Actions 가 빌드 → `tools/mkrelease` 로 latest.json 서명 → 이 저장소의 Releases 에 올린다

필요한 Secrets: `OITERM_UPDATE_KEY` (OiTerm·OiNMS 와 같은 업데이트 서명 개인 키). 릴리즈는 GITHUB_TOKEN 으로 만든다.
프로그램은 `https://github.com/Oiterm/OiCmd/releases/latest/download/latest.json` 을 확인한다.
