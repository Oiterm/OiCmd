// mkrelease: 릴리즈용 latest.json 을 만들고 업데이트 서명 키로 서명한다 (OiTerm 의 make-update-manifest 와 같은 역할).
//
//	go run ./tools/mkrelease -product OiCmd -version 1.0.0 -dist dist
//
// 서명 키: 환경 변수 OITERM_UPDATE_KEY (PEM, GitHub Secrets) 또는 -key 파일.
// 만드는 것 (dist 안):
//
//	latest.json, latest.json.sig       프로그램이 확인하는 업데이트 정보
//	<제품>-update-<버전>.zip           인터넷이 안 되는 곳에서 화면에 올리는 업데이트 파일
//	RELEASE_NOTES.md                   릴리즈 설명 (CHANGELOG.md 의 그 버전 부분)
package main

import (
	"archive/zip"
	"crypto/ed25519"
	"crypto/x509"
	"encoding/pem"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"oicmd/internal/update"
)

func main() {
	product := flag.String("product", "", "제품 이름 (OiCmd)")
	version := flag.String("version", "", "버전")
	dist := flag.String("dist", "dist", "설치 파일 폴더")
	keyFile := flag.String("key", "", "서명 키 PEM 파일 (없으면 OITERM_UPDATE_KEY)")
	changelog := flag.String("changelog", "CHANGELOG.md", "변경 내역")
	flag.Parse()
	if *product == "" || !update.ValidVersion(*version) {
		fail("사용법: mkrelease -product OiCmd -version 1.0.0 [-dist dist] [-key 키.pem]")
	}
	pemText := os.Getenv("OITERM_UPDATE_KEY")
	if *keyFile != "" {
		b, err := os.ReadFile(*keyFile)
		if err != nil {
			fail(err.Error())
		}
		pemText = string(b)
	}
	priv := parseKey(pemText)

	v, p := *version, *product
	// OiCmd 는 관리자 권한이 필요 없는 사용자 설치판 하나 + 포터블
	files := map[string]string{
		"setup": fmt.Sprintf("%s-Setup-%s.exe", p, v),
		"zip":   fmt.Sprintf("%s-%s-portable.zip", p, v),
	}
	m := update.Manifest{Name: p, Version: v, Date: time.Now().UTC().Format(time.RFC3339), Notes: notes(*changelog, v), Files: map[string]update.FileInfo{}}
	for key, name := range files {
		fi, err := update.FileInfoOf(filepath.Join(*dist, name))
		if err != nil {
			fail("파일이 없습니다: " + name)
		}
		m.Files[key] = fi
	}
	j, sig, err := update.Sign(m, priv) // 앱에 박힌 공개 키로 다시 확인까지
	if err != nil {
		fail(err.Error())
	}
	write(filepath.Join(*dist, "latest.json"), j)
	write(filepath.Join(*dist, "latest.json.sig"), []byte(sig+"\n"))

	// 오프라인 업데이트 묶음: 서명된 정보 + 설치 파일
	pkg := filepath.Join(*dist, update.PackageName(p, v))
	out, err := os.Create(pkg)
	if err != nil {
		fail(err.Error())
	}
	zw := zip.NewWriter(out)
	add := func(name string, data []byte) {
		w, err := zw.CreateHeader(&zip.FileHeader{Name: name, Method: zip.Deflate, Modified: time.Now()})
		if err != nil {
			fail(err.Error())
		}
		if _, err := w.Write(data); err != nil {
			fail(err.Error())
		}
	}
	add("latest.json", j)
	add("latest.json.sig", []byte(sig+"\n"))
	for _, key := range []string{"setup"} {
		b, err := os.ReadFile(filepath.Join(*dist, files[key]))
		if err != nil {
			fail(err.Error())
		}
		add(files[key], b)
	}
	if err := zw.Close(); err != nil {
		fail(err.Error())
	}
	out.Close()

	n := m.Notes
	if n == "" {
		n = p + " " + v
	}
	rel := fmt.Sprintf("%s\n\n---\n- **설치**: `%s` (관리자 권한 필요 없음)\n- **포터블**: `%s` (압축 풀고 oicmd.exe 실행)\n- **인터넷이 안 되는 곳**: `%s` 를 받아서 프로그램의 [설정] → 업데이트 → \"업데이트 파일로 설치\"에 올리세요.\n- 업데이트 정보(latest.json)는 서명 키로 서명되어 있고, 프로그램은 서명과 SHA-512 가 맞는 파일만 설치합니다.\n",
		n, files["setup"], files["zip"], update.PackageName(p, v))
	write(filepath.Join(*dist, "RELEASE_NOTES.md"), []byte(rel))
	fmt.Printf("%s %s 서명 완료 (setup %d B, zip %d B)\n", p, v, m.Files["setup"].Size, m.Files["zip"].Size)
}

func parseKey(pemText string) ed25519.PrivateKey {
	blk, _ := pem.Decode([]byte(pemText))
	if blk == nil || !strings.Contains(blk.Type, "PRIVATE KEY") {
		fail("업데이트 서명 키가 없습니다 (OITERM_UPDATE_KEY 또는 -key)")
	}
	k, err := x509.ParsePKCS8PrivateKey(blk.Bytes)
	if err != nil {
		fail("서명 키를 읽을 수 없습니다: " + err.Error())
	}
	priv, ok := k.(ed25519.PrivateKey)
	if !ok {
		fail("Ed25519 키가 아닙니다")
	}
	return priv
}

// notes: CHANGELOG.md 의 "## 1.3.0" 부분
func notes(path, v string) string {
	b, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	re := regexp.MustCompile(`(?ms)^## ` + regexp.QuoteMeta(v) + `\b[^\n]*\n(.*?)(?:^## |\z)`)
	if m := re.FindSubmatch(b); m != nil {
		return strings.TrimSpace(string(m[1]))
	}
	return ""
}

func write(path string, b []byte) {
	if err := os.WriteFile(path, b, 0o644); err != nil {
		fail(err.Error())
	}
}

func fail(msg string) {
	fmt.Fprintln(os.Stderr, "mkrelease:", msg)
	os.Exit(1)
}
