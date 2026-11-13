#!/bin/sh
# dist/ 만들기: OiCmd-Setup-<버전>.exe (관리자 권한 없이 설치), OiCmd-<버전>-portable.zip
# 필요: Go 1.27 이상, makensis (NSIS 3, amd64 stub 포함), python3, zip
set -e
cd "$(dirname "$0")"
VER=$(sed -n 's/^const Version = "\(.*\)"/\1/p' internal/app/app.go)
echo "OiCmd $VER"
(cd tools/genres && go run . "$VER" ../../branding/oicmd.ico ../../cmd/oicmd/rsrc_windows_amd64.syso)
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -H windowsgui" -o installer/oicmd.exe ./cmd/oicmd
python3 - <<'PY'
for src, dst in (('dist-files/README.txt', 'installer/README.txt'), ('internal/server/ui/THIRD_PARTY_LICENSES.txt', 'installer/THIRD_PARTY_LICENSES.txt')):
    s = open(src, encoding='utf-8').read()
    open(dst, 'w', encoding='utf-8-sig', newline='').write(s.replace('\n', '\r\n'))
PY
cp branding/oicmd.ico installer/oicmd.ico
(cd installer && makensis -V2 -DVERSION="$VER" oicmd.nsi)
rm -rf dist && mkdir -p dist/portable/OiCmd
mv installer/OiCmd-Setup-"$VER".exe dist/
cp installer/oicmd.exe installer/README.txt installer/THIRD_PARTY_LICENSES.txt dist/portable/OiCmd/
(cd dist/portable && zip -qr -X ../OiCmd-"$VER"-portable.zip OiCmd)
rm -rf dist/portable installer/oicmd.exe installer/README.txt installer/THIRD_PARTY_LICENSES.txt
ls -la dist
