// Package server 는 OiCmd 화면(ui/)을 이 PC 안(127.0.0.1)에서만 열리는 웹 서버로 내보낸다.
//
//   - 주소: 127.0.0.1:<빈 포트>. 다른 PC 에서는 접속할 수 없다.
//   - 화면 파일은 누구나 받을 수 있지만, /api/ 는 실행할 때마다 새로 만드는 토큰(X-OiCmd-Token)이 있어야 한다.
//     (같은 PC 의 다른 프로그램이나 웹 페이지가 내 명령어를 바꾸지 못하게)
//   - Host 머리말이 127.0.0.1:<포트> 가 아니면 거절한다 (DNS 리바인딩 막기).
//
// 사용자 데이터(내 명령어, 확인 표시, 설정)는 user.json 하나에 통째로 저장한다. 내용은 화면(JS)이 정하고
// 서버는 JSON 객체인지, 크기가 넘지 않는지만 본다.
package server

import (
	"context"
	"crypto/rand"
	"crypto/subtle"
	"embed"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"io/fs"
	"log"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"oicmd/internal/app"
	"oicmd/internal/update"
)

//go:embed ui
var uiFS embed.FS

const maxUserData = 4 << 20 // user.json 최대 4MB

type Server struct {
	DataDir string
	Update  *update.Manager
	// OpenURL 은 바깥 주소(릴리즈 페이지)를 기본 브라우저로 연다. nil 이면 화면이 직접 연다.
	OpenURL func(string) error

	token string
	addr  string
	mu    sync.Mutex // user.json 쓰기
	srv   *http.Server
}

// Start 는 addr(예: "127.0.0.1:0")에서 듣기 시작하고, 화면을 여는 주소(토큰 포함)를 돌려준다.
func (s *Server) Start(addr string) (string, error) {
	if err := os.MkdirAll(s.DataDir, 0o700); err != nil {
		return "", err
	}
	b := make([]byte, 24)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	s.token = hex.EncodeToString(b)
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return "", err
	}
	tcp, ok := ln.Addr().(*net.TCPAddr)
	if !ok || !tcp.IP.IsLoopback() {
		ln.Close()
		return "", errors.New("127.0.0.1 에서만 열 수 있습니다")
	}
	s.addr = ln.Addr().String()
	s.srv = &http.Server{
		Handler:           s.routes(),
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       2 * time.Minute,
		WriteTimeout:      2 * time.Minute,
	}
	go func() {
		if err := s.srv.Serve(ln); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Printf("웹 서버: %v", err)
		}
	}()
	return "http://" + s.addr + "/#t=" + s.token, nil
}

func (s *Server) Stop() {
	if s.srv != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()
		_ = s.srv.Shutdown(ctx)
	}
}

func (s *Server) routes() http.Handler {
	ui, _ := fs.Sub(uiFS, "ui")
	files := http.FileServer(http.FS(ui))
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/info", s.api(s.hInfo))
	mux.HandleFunc("GET /api/user", s.api(s.hUserGet))
	mux.HandleFunc("PUT /api/user", s.api(s.hUserPut))
	mux.HandleFunc("GET /api/update", s.api(s.hUpdateStatus))
	mux.HandleFunc("POST /api/update/check", s.api(s.hUpdateCheck))
	mux.HandleFunc("POST /api/update/install", s.api(s.hUpdateInstall))
	mux.HandleFunc("POST /api/update/package", s.api(s.hUpdatePackage))
	mux.HandleFunc("POST /api/open", s.api(s.hOpen))
	mux.HandleFunc("/api/", func(w http.ResponseWriter, r *http.Request) { writeErr(w, 404, "없는 기능입니다") })
	mux.Handle("/", files)
	return s.guard(mux)
}

// guard: Host 확인, 기본 보안 머리말.
func (s *Server) guard(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Host != s.addr {
			http.Error(w, "forbidden", http.StatusForbidden)
			return
		}
		h := w.Header()
		h.Set("X-Content-Type-Options", "nosniff")
		h.Set("X-Frame-Options", "DENY")
		h.Set("Referrer-Policy", "no-referrer")
		h.Set("Cache-Control", "no-store")
		h.Set("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
		next.ServeHTTP(w, r)
	})
}

func (s *Server) api(fn http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		t := r.Header.Get("X-OiCmd-Token")
		if t == "" || subtle.ConstantTimeCompare([]byte(t), []byte(s.token)) != 1 {
			writeErr(w, 403, "화면을 다시 열어 주세요 (토큰이 맞지 않음)")
			return
		}
		fn(w, r)
	}
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	_ = json.NewEncoder(w).Encode(v)
}

func writeErr(w http.ResponseWriter, code int, msg string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": msg})
}

func (s *Server) hInfo(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, map[string]any{"product": app.Product, "version": app.Version, "data_dir": s.DataDir, "can_open": s.OpenURL != nil})
}

func (s *Server) userPath() string { return filepath.Join(s.DataDir, "user.json") }

func (s *Server) hUserGet(w http.ResponseWriter, r *http.Request) {
	b, err := os.ReadFile(s.userPath())
	if errors.Is(err, os.ErrNotExist) {
		writeJSON(w, map[string]any{})
		return
	}
	if err != nil {
		writeErr(w, 500, "내 데이터를 읽을 수 없습니다: "+err.Error())
		return
	}
	if !json.Valid(b) {
		// 망가진 파일은 옆에 남겨두고 빈 데이터로 시작
		_ = os.Rename(s.userPath(), s.userPath()+".broken-"+time.Now().Format("20060102-150405"))
		writeJSON(w, map[string]any{"_warning": "내 데이터 파일이 망가져 있어 옆에 따로 두고 새로 시작합니다"})
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	_, _ = w.Write(b)
}

func (s *Server) hUserPut(w http.ResponseWriter, r *http.Request) {
	b, err := io.ReadAll(io.LimitReader(r.Body, maxUserData+1))
	if err != nil {
		writeErr(w, 400, "읽을 수 없습니다")
		return
	}
	if len(b) > maxUserData {
		writeErr(w, 413, "내 데이터가 너무 큽니다 (4MB 까지)")
		return
	}
	var obj map[string]json.RawMessage
	if err := json.Unmarshal(b, &obj); err != nil {
		writeErr(w, 400, "JSON 객체가 아닙니다")
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if err := writeAtomic(s.userPath(), b); err != nil {
		writeErr(w, 500, "저장하지 못했습니다: "+err.Error())
		return
	}
	writeJSON(w, map[string]bool{"ok": true})
}

// AutoUpdate 는 설정의 "새 버전 자동 확인" (기본 켜짐).
func (s *Server) AutoUpdate() bool {
	b, err := os.ReadFile(s.userPath())
	if err != nil {
		return true
	}
	var v struct {
		Settings struct {
			AutoUpdate *bool `json:"autoUpdate"`
		} `json:"settings"`
	}
	if json.Unmarshal(b, &v) != nil || v.Settings.AutoUpdate == nil {
		return true
	}
	return *v.Settings.AutoUpdate
}

func writeAtomic(path string, b []byte) error {
	tmp, err := os.CreateTemp(filepath.Dir(path), ".user-*.tmp")
	if err != nil {
		return err
	}
	name := tmp.Name()
	if _, err := tmp.Write(b); err != nil {
		tmp.Close()
		os.Remove(name)
		return err
	}
	if err := tmp.Sync(); err != nil {
		tmp.Close()
		os.Remove(name)
		return err
	}
	if err := tmp.Close(); err != nil {
		os.Remove(name)
		return err
	}
	// 이전 내용 하나는 남겨 둔다 (실수로 지웠을 때)
	if _, err := os.Stat(path); err == nil {
		_ = copyFile(path, path+".bak")
	}
	return os.Rename(name, path)
}

func copyFile(src, dst string) error {
	b, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, b, 0o600)
}

// ---- 업데이트 ----

func (s *Server) hUpdateStatus(w http.ResponseWriter, r *http.Request) {
	if s.Update == nil {
		writeJSON(w, map[string]any{"current": app.Version, "plan_note": "이 실행 방식에서는 업데이트를 쓸 수 없습니다"})
		return
	}
	writeJSON(w, s.Update.Status())
}

func (s *Server) hUpdateCheck(w http.ResponseWriter, r *http.Request) {
	if s.Update == nil {
		writeErr(w, 400, "이 실행 방식에서는 업데이트를 쓸 수 없습니다")
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 90*time.Second)
	defer cancel()
	writeJSON(w, s.Update.Check(ctx))
}

func (s *Server) hUpdateInstall(w http.ResponseWriter, r *http.Request) {
	if s.Update == nil {
		writeErr(w, 400, "이 실행 방식에서는 업데이트를 쓸 수 없습니다")
		return
	}
	v, err := s.Update.Install()
	if err != nil {
		writeErr(w, 400, err.Error())
		return
	}
	writeJSON(w, map[string]string{"version": v})
}

func (s *Server) hUpdatePackage(w http.ResponseWriter, r *http.Request) {
	if s.Update == nil {
		writeErr(w, 400, "이 실행 방식에서는 업데이트를 쓸 수 없습니다")
		return
	}
	b, err := io.ReadAll(io.LimitReader(r.Body, 100<<20+1))
	if err != nil || len(b) > 100<<20 {
		writeErr(w, 400, "파일이 너무 크거나 읽을 수 없습니다")
		return
	}
	m, err := s.Update.InstallPackage(b)
	if err != nil {
		writeErr(w, 400, err.Error())
		return
	}
	writeJSON(w, map[string]string{"version": m.Version})
}

// hOpen: 정해진 바깥 주소만 기본 브라우저로 연다 (https 이고 github.com 또는 벤더 문서 사이트).
func (s *Server) hOpen(w http.ResponseWriter, r *http.Request) {
	var in struct {
		URL string `json:"url"`
	}
	if err := json.NewDecoder(io.LimitReader(r.Body, 4096)).Decode(&in); err != nil || !SafeExternalURL(in.URL) {
		writeErr(w, 400, "열 수 없는 주소입니다")
		return
	}
	if s.OpenURL == nil {
		writeErr(w, 400, "이 실행 방식에서는 화면에서 직접 엽니다")
		return
	}
	if err := s.OpenURL(in.URL); err != nil {
		writeErr(w, 500, err.Error())
		return
	}
	writeJSON(w, map[string]bool{"ok": true})
}

var allowedOpenHosts = []string{"github.com", "www.cisco.com", "www.juniper.net", "www.alliedtelesis.com", "www.al-enterprise.com", "myportal.al-enterprise.com"}

// SafeExternalURL: https 이고 정해진 사이트만.
func SafeExternalURL(u string) bool {
	if len(u) > 2000 || !strings.HasPrefix(u, "https://") || strings.ContainsAny(u, " \t\r\n\"'<>\\^`{|}") {
		return false
	}
	rest := strings.TrimPrefix(u, "https://")
	host := rest
	if i := strings.IndexAny(rest, "/?#"); i >= 0 {
		host = rest[:i]
	}
	for _, h := range allowedOpenHosts {
		if host == h {
			return true
		}
	}
	return false
}
