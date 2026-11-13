// Package update 는 새 버전 확인·받기·검증을 한다 (OiTerm 과 같은 방식, 같은 서명 키).
//
// 믿는 것은 이 파일에 박힌 공개 키 하나뿐이다. GitHub 나 중간 네트워크가 바꿔치기해도
//  1. latest.json 의 Ed25519 서명이 안 맞으면 버림
//  2. 받은 설치 파일의 크기·SHA-512 가 서명된 값과 다르면 버림
//  3. 제품 이름이 다르거나(OiTerm 업데이트를 OiCmd 에 넣기 등), 지금 버전보다 낮거나 같으면 버림
//
// 인터넷이 안 되는 곳은 릴리즈에 같이 올라가는 업데이트 묶음(zip: latest.json + 서명 + 설치 파일)을
// 화면에서 올려서 같은 검사를 거친 뒤 설치한다.
//
// 이 파일은 OiNMS 의 internal/update 를 그대로 복사한 것이다(OiLog 도 같음, 제품 이름·저장소만 Config 로 다름).
package update

import (
	"archive/zip"
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/sha512"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

// PublicKey: OiTerm·OiNMS·OiLog·OiCmd 업데이트 서명 공개 키 (개인 키는 GitHub 저장소 Secrets 와 만든 사람 PC 에만).
const PublicKey = "MCowBQYDK2VwAyEAPLq21NWUxWR0Ar6wLMJkYobEER9YjlmZ2nI8ERhQxdc="

const (
	maxJSON    = 64 << 10
	maxSig     = 1024
	maxFile    = 300 << 20
	maxPackage = 100 << 20
)

var allowedHosts = regexp.MustCompile(`(?i)^(github\.com|objects\.githubusercontent\.com|release-assets\.githubusercontent\.com|github-releases\.githubusercontent\.com)$`)

type FileInfo struct {
	Name   string `json:"name"`
	Size   int64  `json:"size"`
	SHA512 string `json:"sha512"`
}

type Manifest struct {
	Name    string              `json:"name"`
	Version string              `json:"version"`
	Date    string              `json:"date"`
	Notes   string              `json:"notes"`
	Files   map[string]FileInfo `json:"files"`
}

// Config 는 제품마다 다른 값.
type Config struct {
	Product string // "OiCmd"
	Repo    string // 릴리즈가 올라가는 공개 저장소 "Oiterm/OiCmd"
	Current string // 지금 버전
	Dir     string // 받은 파일을 둘 폴더 (서비스면 SYSTEM·관리자 전용 data 안)
	// FileNames: 매니페스트 files 키 → 파일 이름 형식 (예: "setup" → OiCmd-Setup-%s.exe)
	FileNames map[string]string
}

var verRe = regexp.MustCompile(`^\d{1,4}\.\d{1,4}\.\d{1,4}$`)

func ValidVersion(v string) bool { return verRe.MatchString(v) }

// CmpVer 는 1.2.3 형식 비교.
func CmpVer(a, b string) int {
	pa, pb := strings.Split(a, "."), strings.Split(b, ".")
	for i := 0; i < 3; i++ {
		var x, y int
		if i < len(pa) {
			x, _ = strconv.Atoi(pa[i])
		}
		if i < len(pb) {
			y, _ = strconv.Atoi(pb[i])
		}
		if x != y {
			if x > y {
				return 1
			}
			return -1
		}
	}
	return 0
}

func parsePublicKey(b64 string) (ed25519.PublicKey, error) {
	der, err := base64.StdEncoding.DecodeString(b64)
	if err != nil {
		return nil, err
	}
	k, err := x509.ParsePKIXPublicKey(der)
	if err != nil {
		return nil, err
	}
	pk, ok := k.(ed25519.PublicKey)
	if !ok {
		return nil, errors.New("Ed25519 키가 아님")
	}
	return pk, nil
}

// testPublicKey 는 시험 빌드(-tags updatetest)에서만 바뀐다.
var testPublicKey = ""

func publicKey() ed25519.PublicKey {
	src := PublicKey
	if testPublicKey != "" {
		src = testPublicKey
	}
	k, err := parsePublicKey(src)
	if err != nil {
		panic("업데이트 공개 키가 잘못됨: " + err.Error())
	}
	return k
}

var b64sha512 = regexp.MustCompile(`^[A-Za-z0-9+/]{86}==$`)

// Verify 는 latest.json 과 서명을 확인한다. 통과하면 내용을 돌려준다.
func (c Config) Verify(jsonBytes []byte, sigText string) (Manifest, error) {
	var m Manifest
	sig, err := base64.StdEncoding.DecodeString(strings.TrimSpace(sigText))
	if err != nil || len(sig) != ed25519.SignatureSize {
		return m, errors.New("서명 형식이 잘못됐습니다")
	}
	if !ed25519.Verify(publicKey(), jsonBytes, sig) {
		return m, fmt.Errorf("업데이트 정보의 서명이 맞지 않습니다 (%s 를 만든 사람이 서명한 파일이 아님)", c.Product)
	}
	if err := json.Unmarshal(jsonBytes, &m); err != nil {
		return m, errors.New("업데이트 정보를 읽을 수 없습니다")
	}
	if m.Name != c.Product || !ValidVersion(m.Version) {
		return m, fmt.Errorf("%s 업데이트 정보가 아닙니다 (%q)", c.Product, m.Name)
	}
	for key, f := range m.Files {
		pat, ok := c.FileNames[key]
		if !ok {
			continue // 모르는 파일은 쓰지 않음
		}
		if f.Name != fmt.Sprintf(pat, m.Version) || !b64sha512.MatchString(f.SHA512) || f.Size <= 0 || f.Size > maxFile {
			return m, fmt.Errorf("설치 파일 정보가 잘못됐습니다 (%s)", key)
		}
	}
	if len(m.Notes) > 8000 {
		m.Notes = m.Notes[:8000]
	}
	return m, nil
}

// ---- 인터넷으로 받기 ----

func (c Config) feed() string {
	if f := testFeed(); f != "" {
		return f
	}
	return "https://github.com/" + c.Repo + "/releases/latest/download/"
}

// ReleasePage 는 사람이 여는 다운로드 페이지.
func (c Config) ReleasePage() string { return "https://github.com/" + c.Repo + "/releases/latest" }

func allowed(raw string) bool {
	u, err := url.Parse(raw)
	if err != nil {
		return false
	}
	if testAllowLocal() && u.Scheme == "http" && u.Hostname() == "127.0.0.1" {
		return true
	}
	return u.Scheme == "https" && u.User == nil && allowedHosts.MatchString(u.Hostname())
}

func (c Config) client() *http.Client {
	tr := http.DefaultTransport.(*http.Transport).Clone()
	tr.ResponseHeaderTimeout = 30 * time.Second
	return &http.Client{
		Transport: tr,
		Timeout:   10 * time.Minute,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if len(via) > 5 {
				return errors.New("리다이렉트가 너무 많습니다")
			}
			if !allowed(req.URL.String()) {
				return fmt.Errorf("허용되지 않은 주소로 이동하려 합니다: %s", req.URL.Hostname())
			}
			return nil
		},
	}
}

// fetch 는 크기 제한을 두고 받는다. w 가 있으면 흘려 쓰고, 없으면 메모리로.
func (c Config) fetch(ctx context.Context, rawURL string, limit int64, w io.Writer) ([]byte, int64, error) {
	if !allowed(rawURL) {
		return nil, 0, errors.New("허용되지 않은 주소입니다: " + rawURL)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, rawURL, nil)
	if err != nil {
		return nil, 0, err
	}
	req.Header.Set("User-Agent", c.Product+"/"+c.Current)
	req.Header.Set("Cache-Control", "no-cache")
	res, err := c.client().Do(req)
	if err != nil {
		return nil, 0, fmt.Errorf("업데이트 서버에 연결할 수 없습니다 (인터넷이 안 되는 곳이면 '업데이트 파일로 설치'를 쓰세요): %w", unwrapURLErr(err))
	}
	defer res.Body.Close()
	if res.StatusCode == http.StatusNotFound {
		return nil, 0, errors.New("아직 올라온 업데이트가 없습니다")
	}
	if res.StatusCode != http.StatusOK {
		return nil, 0, fmt.Errorf("업데이트 서버 응답 %d", res.StatusCode)
	}
	if res.ContentLength > limit {
		return nil, 0, errors.New("파일이 너무 큽니다")
	}
	lr := &io.LimitedReader{R: res.Body, N: limit + 1}
	if w == nil {
		b, err := io.ReadAll(lr)
		if err != nil {
			return nil, 0, fmt.Errorf("받는 중에 끊겼습니다: %w", err)
		}
		if int64(len(b)) > limit {
			return nil, 0, errors.New("파일이 너무 큽니다")
		}
		return b, int64(len(b)), nil
	}
	n, err := io.Copy(w, lr)
	if err != nil {
		return nil, n, fmt.Errorf("받는 중에 끊겼습니다: %w", err)
	}
	if n > limit {
		return nil, n, errors.New("받은 파일이 서명된 크기보다 큽니다")
	}
	return nil, n, nil
}

func unwrapURLErr(err error) error {
	var ue *url.Error
	if errors.As(err, &ue) {
		return ue.Err
	}
	return err
}

// Check 는 최신 버전 정보를 받아 확인한다. 새 버전이 없으면 (nil, nil).
func (c Config) Check(ctx context.Context) (*Manifest, error) {
	j, _, err := c.fetch(ctx, c.feed()+"latest.json", maxJSON, nil)
	if err != nil {
		return nil, err
	}
	sig, _, err := c.fetch(ctx, c.feed()+"latest.json.sig", maxSig, nil)
	if err != nil {
		return nil, err
	}
	m, err := c.Verify(j, string(sig))
	if err != nil {
		return nil, err
	}
	if CmpVer(m.Version, c.Current) <= 0 {
		return nil, nil
	}
	return &m, nil
}

// Download 는 m 의 key 파일을 c.Dir 에 받고 크기·SHA-512 를 확인한다. 확인된 파일 경로를 돌려준다.
func (c Config) Download(ctx context.Context, m Manifest, key string) (string, error) {
	f, ok := m.Files[key]
	if !ok {
		return "", fmt.Errorf("이번 업데이트에 필요한 파일(%s)이 없습니다", key)
	}
	if _, ok := c.FileNames[key]; !ok {
		return "", errors.New("알 수 없는 파일 종류")
	}
	dir, err := c.cleanDir()
	if err != nil {
		return "", err
	}
	path := filepath.Join(dir, f.Name)
	out, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil {
		return "", err
	}
	h := sha512.New()
	_, n, err := c.fetch(ctx, c.feed()+url.PathEscape(f.Name), f.Size, io.MultiWriter(out, h))
	cerr := out.Close()
	if err == nil {
		err = cerr
	}
	if err == nil && (n != f.Size || base64.StdEncoding.EncodeToString(h.Sum(nil)) != f.SHA512) {
		err = errors.New("받은 설치 파일이 서명된 정보와 다릅니다. 설치하지 않았습니다")
	}
	if err != nil {
		os.Remove(path)
		return "", err
	}
	return path, nil
}

// cleanDir: 이전에 받은 파일을 지우고 빈 폴더를 만든다.
func (c Config) cleanDir() (string, error) {
	if c.Dir == "" {
		return "", errors.New("업데이트 폴더가 지정되지 않았습니다")
	}
	_ = os.RemoveAll(c.Dir)
	if err := os.MkdirAll(c.Dir, 0o700); err != nil {
		return "", err
	}
	return c.Dir, nil
}

// ---- 업데이트 파일(zip)로 ----

// PackageName 은 릴리즈에 같이 올리는 업데이트 묶음 이름.
func PackageName(product, version string) string {
	return fmt.Sprintf("%s-update-%s.zip", product, version)
}

// OpenPackage 는 올린 업데이트 묶음(zip)을 확인하고, 안의 설치 파일 중 key 를 c.Dir 에 풀어서 경로를 돌려준다.
// 묶음 안: latest.json, latest.json.sig, 설치 파일들.
func (c Config) OpenPackage(data []byte, key string) (Manifest, string, error) {
	var m Manifest
	if len(data) > maxPackage {
		return m, "", errors.New("파일이 너무 큽니다")
	}
	zr, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	if err != nil {
		return m, "", errors.New("업데이트 파일(zip)을 열 수 없습니다. 릴리즈의 " + PackageName(c.Product, "버전") + " 파일을 올리세요")
	}
	read := func(name string, limit int64) ([]byte, *zip.File, error) {
		for _, f := range zr.File {
			if f.Name == name {
				if f.UncompressedSize64 > uint64(limit) {
					return nil, nil, errors.New(name + " 가 너무 큽니다")
				}
				rc, err := f.Open()
				if err != nil {
					return nil, nil, err
				}
				defer rc.Close()
				b, err := io.ReadAll(io.LimitReader(rc, limit+1))
				if err != nil {
					return nil, nil, err
				}
				if int64(len(b)) > limit {
					return nil, nil, errors.New(name + " 가 너무 큽니다")
				}
				return b, f, nil
			}
		}
		return nil, nil, errors.New("업데이트 파일 안에 " + name + " 이(가) 없습니다")
	}
	j, _, err := read("latest.json", maxJSON)
	if err != nil {
		return m, "", err
	}
	sig, _, err := read("latest.json.sig", maxSig)
	if err != nil {
		return m, "", err
	}
	if m, err = c.Verify(j, string(sig)); err != nil {
		return m, "", err
	}
	if CmpVer(m.Version, c.Current) <= 0 {
		return m, "", fmt.Errorf("올린 파일은 %s 이라 지금 버전(%s)보다 새 버전이 아닙니다", m.Version, c.Current)
	}
	fi, ok := m.Files[key]
	if !ok {
		return m, "", fmt.Errorf("이 업데이트 파일에는 필요한 설치 파일(%s)이 없습니다", key)
	}
	b, _, err := read(fi.Name, fi.Size)
	if err != nil {
		return m, "", err
	}
	sum := sha512.Sum512(b)
	if int64(len(b)) != fi.Size || base64.StdEncoding.EncodeToString(sum[:]) != fi.SHA512 {
		return m, "", errors.New("업데이트 파일 안의 설치 파일이 서명된 정보와 다릅니다. 설치하지 않았습니다")
	}
	dir, err := c.cleanDir()
	if err != nil {
		return m, "", err
	}
	path := filepath.Join(dir, fi.Name)
	if err := os.WriteFile(path, b, 0o600); err != nil {
		return m, "", err
	}
	return m, path, nil
}

// ---- 릴리즈 만들 때 (tools/mkrelease) ----

// Sign 은 매니페스트를 직렬화하고 서명한다. 만든 서명을 앱에 박힌 공개 키로 다시 확인한다.
func Sign(m Manifest, priv ed25519.PrivateKey) ([]byte, string, error) {
	j, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return nil, "", err
	}
	j = append(j, '\n')
	sig := base64.StdEncoding.EncodeToString(ed25519.Sign(priv, j))
	if !ed25519.Verify(publicKey(), j, mustDecode(sig)) {
		return nil, "", errors.New("서명 키가 앱에 들어 있는 공개 키와 짝이 아닙니다 (다른 키로 서명하려 함)")
	}
	return j, sig, nil
}

func mustDecode(s string) []byte {
	b, _ := base64.StdEncoding.DecodeString(s)
	return b
}

// FileInfoOf 는 릴리즈 파일 정보를 만든다.
func FileInfoOf(path string) (FileInfo, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return FileInfo{}, err
	}
	sum := sha512.Sum512(b)
	return FileInfo{Name: filepath.Base(path), Size: int64(len(b)), SHA512: base64.StdEncoding.EncodeToString(sum[:])}, nil
}
