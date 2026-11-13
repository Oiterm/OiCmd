#!/usr/bin/env python3
"""오픈소스 라이선스 고지 파일(internal/server/ui/THIRD_PARTY_LICENSES.txt)을 다시 만든다.
   의존 모듈을 바꾸면 아래 목록을 고치고 저장소 맨 위에서:  python3 tools/mknotice.py"""
import os, glob
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOROOT = os.popen("go env GOROOT").read().strip()
def rd(p): return open(p, encoding="utf-8").read().strip("\n")
def lic(d): return rd(sorted(glob.glob(os.path.join(R, d, "LICENSE*")))[0])
items = [
 ("Go 표준 라이브러리 (The Go Programming Language)", "https://go.dev", "BSD-3-Clause", rd(os.path.join(GOROOT, "LICENSE"))),
 ("go-webview2 (프로그램 창)", "https://github.com/jchv/go-webview2", "MIT", lic("third_party/go-webview2")),
 ("Microsoft Edge WebView2 SDK — WebView2Loader.dll (go-webview2 안에 들어 있음)", "https://developer.microsoft.com/microsoft-edge/webview2/", "BSD-3-Clause",
  rd(os.path.join(R, "third_party/go-webview2/webviewloader/sdk/LICENSE.txt"))),
 ("go-winloader", "https://github.com/jchv/go-winloader", "ISC", lic("third_party/go-winloader")),
 ("golang.org/x/sys", "https://go.googlesource.com/sys", "BSD-3-Clause", lic("third_party/sys")),
]
out = ["OiCmd 에 들어 있는 오픈소스 소프트웨어와 라이선스", "=" * 44, "",
       "OiCmd(oicmd.exe)는 아래 오픈소스 소프트웨어를 포함합니다. 각 소프트웨어의 저작권은 해당 저작자에게 있습니다.",
       "모두 상업적 사용·재배포가 허용되는 라이선스이며, 라이선스 조건에 따라 저작권 표시와 라이선스 전문을 함께 싣습니다.",
       "프로그램 창은 PC 에 설치된 Microsoft Edge WebView2 런타임을 씁니다(런타임은 Windows 에 포함, 이 프로그램에는 불러오는 부분(WebView2Loader)만 들어 있음).",
       "설치 프로그램은 NSIS(zlib/libpng 라이선스)로 만듭니다.", "", "목록", "-" * 4]
for i, (n, u, l, _) in enumerate(items, 1):
    out.append(f"{i:2}. {n} — {l} — {u}")
out.append("")
for i, (n, u, l, t) in enumerate(items, 1):
    out += ["", "=" * 72, f"{i}. {n}", f"   {u}", f"   라이선스: {l}", "=" * 72, "", t]
open(os.path.join(R, "internal/server/ui/THIRD_PARTY_LICENSES.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(len(items), "개")
