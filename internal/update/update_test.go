package update

import (
	"archive/zip"
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/x509"
	"encoding/base64"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func testKey(t *testing.T) ed25519.PrivateKey {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	der, _ := x509.MarshalPKIXPublicKey(pub)
	testPublicKey = base64.StdEncoding.EncodeToString(der)
	t.Cleanup(func() { testPublicKey = "" })
	return priv
}

func cfg(dir string) Config {
	return Config{Product: "OiNMS", Repo: "Oiterm/OiNMS-release", Current: "1.2.0", Dir: dir,
		FileNames: map[string]string{"setup": "OiNMS-Setup-%s.exe", "setup_user": "OiNMS-Setup-%s-user.exe"}}
}

func release(t *testing.T, priv ed25519.PrivateKey, ver string, payload []byte) ([]byte, string) {
	dir := t.TempDir()
	p := filepath.Join(dir, "OiNMS-Setup-"+ver+".exe")
	os.WriteFile(p, payload, 0o600)
	fi, _ := FileInfoOf(p)
	j, sig, err := Sign(Manifest{Name: "OiNMS", Version: ver, Notes: "고침", Files: map[string]FileInfo{"setup": fi}}, priv)
	if err != nil {
		t.Fatal(err)
	}
	return j, sig
}

func TestRealPublicKeyParses(t *testing.T) {
	if _, err := parsePublicKey(PublicKey); err != nil {
		t.Fatal(err)
	}
}

func TestCmpVer(t *testing.T) {
	for _, c := range []struct {
		a, b string
		w    int
	}{{"1.2.0", "1.10.0", -1}, {"2.0.0", "1.99.99", 1}, {"1.2.3", "1.2.3", 0}} {
		if CmpVer(c.a, c.b) != c.w {
			t.Errorf("%s vs %s", c.a, c.b)
		}
	}
}

func TestVerify(t *testing.T) {
	priv := testKey(t)
	c := cfg(t.TempDir())
	j, sig := release(t, priv, "1.3.0", []byte("setup"))
	m, err := c.Verify(j, sig)
	if err != nil || m.Version != "1.3.0" {
		t.Fatalf("정상: %v", err)
	}
	// 내용 한 글자만 바꿔도 거부
	bad := bytes.Replace(j, []byte("1.3.0"), []byte("1.3.1"), 1)
	if _, err := c.Verify(bad, sig); err == nil {
		t.Error("변조된 매니페스트 통과")
	}
	// 다른 키로 서명
	_, other, _ := ed25519.GenerateKey(rand.Reader)
	if _, err := c.Verify(j, base64.StdEncoding.EncodeToString(ed25519.Sign(other, j))); err == nil {
		t.Error("다른 키 서명 통과")
	}
	// 다른 제품 (OiTerm 업데이트를 OiNMS 에)
	jo, so, _ := Sign(Manifest{Name: "OiTerm", Version: "9.0.0", Files: map[string]FileInfo{}}, priv)
	if _, err := c.Verify(jo, so); err == nil {
		t.Error("다른 제품 매니페스트 통과")
	}
	// 파일 이름이 버전과 안 맞음
	jn, sn, _ := Sign(Manifest{Name: "OiNMS", Version: "1.3.0", Files: map[string]FileInfo{"setup": {Name: "evil.exe", Size: 5, SHA512: strings.Repeat("A", 86) + "=="}}}, priv)
	if _, err := c.Verify(jn, sn); err == nil {
		t.Error("이상한 파일 이름 통과")
	}
	if _, err := c.Verify(j, "!!"); err == nil {
		t.Error("깨진 서명 통과")
	}
}

func TestSignRefusesWrongKey(t *testing.T) {
	testKey(t) // 앱 공개 키 = 시험 키
	_, other, _ := ed25519.GenerateKey(rand.Reader)
	if _, _, err := Sign(Manifest{Name: "OiNMS", Version: "1.0.0"}, other); err == nil {
		t.Fatal("짝이 아닌 키로 서명이 됨")
	}
}

func TestCheckAndDownload(t *testing.T) {
	priv := testKey(t)
	payload := bytes.Repeat([]byte("OiNMS"), 1000)
	j, sig := release(t, priv, "1.3.0", payload)
	serve := payload
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/latest.json":
			w.Write(j)
		case "/latest.json.sig":
			w.Write([]byte(sig))
		case "/OiNMS-Setup-1.3.0.exe":
			w.Write(serve)
		default:
			http.NotFound(w, r)
		}
	}))
	defer srv.Close()
	t.Setenv("OI_UPDATE_FEED", srv.URL+"/")
	// 배포 빌드는 로컬 http 주소를 허용하지 않으므로, 이 시험은 fetch 를 직접 우회하지 않고 allowed 를 확인만 한다
	if allowed(srv.URL+"/latest.json") && !testAllowLocal() {
		t.Fatal("배포 빌드가 http 를 허용함")
	}
	if !testAllowLocal() {
		t.Skip("로컬 다운로드 시험은 -tags updatetest 로 실행")
	}
	c := cfg(t.TempDir())
	m, err := c.Check(context.Background())
	if err != nil || m == nil || m.Version != "1.3.0" {
		t.Fatalf("check: %v %v", m, err)
	}
	p, err := c.Download(context.Background(), *m, "setup")
	if err != nil {
		t.Fatal(err)
	}
	got, _ := os.ReadFile(p)
	if !bytes.Equal(got, payload) {
		t.Fatal("받은 내용이 다름")
	}
	serve = append([]byte{}, payload...)
	serve[10] ^= 1 // 바꿔치기된 설치 파일
	if _, err := c.Download(context.Background(), *m, "setup"); err == nil {
		t.Fatal("바꿔치기된 파일 통과")
	}
	c.Current = "1.3.0"
	if m, err := c.Check(context.Background()); err != nil || m != nil {
		t.Fatalf("같은 버전은 업데이트 없음이어야 함: %v %v", m, err)
	}
}

func TestAllowedHosts(t *testing.T) {
	for _, u := range []string{"https://github.com/Oiterm/OiNMS-release/releases/latest/download/latest.json", "https://objects.githubusercontent.com/x"} {
		if !allowed(u) {
			t.Errorf("%s 허용돼야 함", u)
		}
	}
	for _, u := range []string{"http://github.com/x", "https://github.com.evil.example/x", "https://evil.example/github.com", "https://user:pw@github.com/x", "file:///c:/x", "https://raw.githubusercontent.com/x"} {
		if allowed(u) && !testAllowLocal() {
			t.Errorf("%s 거부돼야 함", u)
		}
	}
}

func TestPackage(t *testing.T) {
	priv := testKey(t)
	payload := []byte("installer-bytes")
	j, sig := release(t, priv, "1.3.0", payload)
	mk := func(files map[string][]byte) []byte {
		var buf bytes.Buffer
		zw := zip.NewWriter(&buf)
		for n, b := range files {
			w, _ := zw.Create(n)
			w.Write(b)
		}
		zw.Close()
		return buf.Bytes()
	}
	c := cfg(t.TempDir())
	m, p, err := c.OpenPackage(mk(map[string][]byte{"latest.json": j, "latest.json.sig": []byte(sig), "OiNMS-Setup-1.3.0.exe": payload}), "setup")
	if err != nil || m.Version != "1.3.0" {
		t.Fatalf("정상 묶음: %v", err)
	}
	if b, _ := os.ReadFile(p); !bytes.Equal(b, payload) {
		t.Fatal("풀린 내용 다름")
	}
	if _, _, err := c.OpenPackage(mk(map[string][]byte{"latest.json": j, "latest.json.sig": []byte(sig), "OiNMS-Setup-1.3.0.exe": []byte("evil-bytes-xxxx")}), "setup"); err == nil {
		t.Error("바뀐 설치 파일 통과")
	}
	if _, _, err := c.OpenPackage(mk(map[string][]byte{"latest.json": j, "OiNMS-Setup-1.3.0.exe": payload}), "setup"); err == nil {
		t.Error("서명 없는 묶음 통과")
	}
	c.Current = "1.3.0"
	if _, _, err := c.OpenPackage(mk(map[string][]byte{"latest.json": j, "latest.json.sig": []byte(sig), "OiNMS-Setup-1.3.0.exe": payload}), "setup"); err == nil {
		t.Error("같은 버전(되돌리기) 통과")
	}
	if _, _, err := c.OpenPackage([]byte("not a zip"), "setup"); err == nil {
		t.Error("zip 아님 통과")
	}
}
