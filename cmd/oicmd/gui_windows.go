//go:build windows

package main

// 프로그램 창 (OiNMS·OiLog 와 같은 WebView2 창, 트레이 없음)
//
//   - 화면은 이 프로그램이 127.0.0.1 의 빈 포트에 띄운 웹 서버(토큰 필요)를 연다.
//   - 하나만 뜬다: 이미 열려 있으면 그 창을 앞으로 가져온다.
//   - WebView2 가 없는 PC 는 기본 브라우저로 열고, 확인 창을 닫으면 끝난다.
//   - 업데이트: 설치판은 "나만 사용" 설치 파일을 /S /UPDATE /RELAUNCH 로 실행하고 창을 닫는다. 포터블은 안내만.

import (
	"context"
	"errors"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"time"
	"unsafe"

	webview2 "github.com/jchv/go-webview2"
	"github.com/jchv/go-webview2/webviewloader"
	"golang.org/x/sys/windows"
	"golang.org/x/sys/windows/registry"

	"oicmd/internal/app"
	"oicmd/internal/server"
	"oicmd/internal/update"
)

// WebView2 와 메시지 루프는 메인 스레드에서 돌아야 한다.
func init() { runtime.LockOSThread() }

const (
	appIconID   = 1 // tools/genres 가 넣는 아이콘 리소스 번호
	windowTitle = "OiCmd"
	regKey      = `Software\OiCmd`

	wmApp     = 0x8000
	wmRestore = wmApp + 2
	wmClose   = 0x0010

	swShow, swRestore = 5, 9

	mbOK, mbIconErr, mbIconW = 0x0, 0x10, 0x30
)

var (
	user32         = windows.NewLazySystemDLL("user32.dll")
	pShowWindow    = user32.NewProc("ShowWindow")
	pSetForeground = user32.NewProc("SetForegroundWindow")
	pIsIconic      = user32.NewProc("IsIconic")
	pPostMessage   = user32.NewProc("PostMessageW")
	pFindWindow    = user32.NewProc("FindWindowW")
	pSetWindowLong = user32.NewProc("SetWindowLongPtrW")
	pCallWindowPrc = user32.NewProc("CallWindowProcW")
)

var origProc uintptr

func wndProc(hwnd, msg, wp, lp uintptr) uintptr {
	if msg == wmRestore {
		pShowWindow.Call(hwnd, swShow)
		if r, _, _ := pIsIconic.Call(hwnd); r != 0 {
			pShowWindow.Call(hwnd, swRestore)
		}
		pSetForeground.Call(hwnd)
		return 0
	}
	r, _, _ := pCallWindowPrc.Call(origProc, hwnd, msg, wp, lp)
	return r
}

func runDefault(args []string) {
	setupLog()
	name, _ := windows.UTF16PtrFromString(`Local\OiCmdGUI`)
	h, err := windows.CreateMutex(nil, false, name)
	if err == windows.ERROR_ALREADY_EXISTS {
		cls, _ := windows.UTF16PtrFromString("webview")
		title, _ := windows.UTF16PtrFromString(windowTitle)
		if hwnd, _, _ := pFindWindow.Call(uintptr(unsafe.Pointer(cls)), uintptr(unsafe.Pointer(title))); hwnd != 0 {
			pPostMessage.Call(hwnd, wmRestore, 0, 0)
		}
		return
	}
	defer windows.CloseHandle(h)

	var hwnd uintptr
	closeWindow := func() {
		if hwnd != 0 {
			pPostMessage.Call(hwnd, wmClose, 0, 0)
		}
	}
	srv := &server.Server{DataDir: app.DataDir()}
	srv.Update = newUpdater(srv, closeWindow)
	srv.OpenURL = func(u string) error {
		if !server.SafeExternalURL(u) {
			return errors.New("열 수 없는 주소")
		}
		openInBrowser(u)
		return nil
	}
	navURL, err := srv.Start("127.0.0.1:0")
	if err != nil {
		msgBox("OiCmd를 시작할 수 없습니다:\n"+err.Error(), mbOK|mbIconErr)
		return
	}
	defer srv.Stop()
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	go autoCheck(ctx, srv)

	if ver, err := webviewloader.GetInstalledVersion(); err != nil || ver == "" {
		openInBrowser(navURL)
		msgBox("이 PC에 WebView2가 없어 기본 브라우저로 열었습니다.\n이 창을 닫으면 OiCmd가 끝납니다.", mbOK|mbIconW)
		return
	}
	w := webview2.NewWithOptions(webview2.WebViewOptions{
		Debug:     false,
		AutoFocus: true,
		DataPath:  filepath.Join(app.LocalDir(), "WebView2"),
		WindowOptions: webview2.WindowOptions{
			Title:  windowTitle,
			Width:  1360,
			Height: 860,
			IconId: appIconID,
			Center: true,
		},
	})
	if w == nil {
		openInBrowser(navURL)
		msgBox("프로그램 창을 만들지 못해 기본 브라우저로 열었습니다.\n이 창을 닫으면 OiCmd가 끝납니다.", mbOK|mbIconW)
		return
	}
	defer w.Destroy()
	hwnd = uintptr(w.Window())
	w.SetSize(900, 600, webview2.HintMin)
	origProc, _, _ = pSetWindowLong.Call(hwnd, ^uintptr(3) /*GWLP_WNDPROC = -4*/, windows.NewCallback(wndProc))
	w.Navigate(navURL)
	w.Run()
}

// autoCheck: 시작하고 20초 뒤, 그다음 20시간마다 (설정에서 끄지 않았으면).
func autoCheck(ctx context.Context, srv *server.Server) {
	t := time.NewTimer(20 * time.Second)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
		}
		if srv.AutoUpdate() {
			cctx, cancel := context.WithTimeout(ctx, 2*time.Minute)
			srv.Update.Check(cctx)
			cancel()
		}
		t.Reset(20 * time.Hour)
	}
}

func regInstallDir() string {
	k, err := registry.OpenKey(registry.CURRENT_USER, regKey, registry.QUERY_VALUE)
	if err != nil {
		return ""
	}
	defer k.Close()
	v, _, _ := k.GetStringValue("InstallDir")
	return v
}

func newUpdater(srv *server.Server, onLaunched func()) *update.Manager {
	exe, _ := os.Executable()
	installed := false
	if d := regInstallDir(); d != "" && samePath(d, filepath.Dir(exe)) {
		installed = true
	}
	m := &update.Manager{Cfg: update.Config{
		Product:   app.Product,
		Repo:      "Oiterm/OiCmd",
		Current:   app.Version,
		Dir:       filepath.Join(app.LocalDir(), "update"),
		FileNames: map[string]string{"setup": "OiCmd-Setup-%s.exe", "zip": "OiCmd-%s-portable.zip"},
	}}
	m.Enabled = srv.AutoUpdate
	m.Plan = func() (string, error) {
		if !installed {
			return "", errors.New("포터블(zip) 버전은 자동 설치가 안 됩니다. 다운로드 페이지에서 새 zip 을 받아 oicmd.exe 를 바꾸세요 (내 명령어는 그대로 남습니다)")
		}
		return "setup", nil
	}
	m.Apply = func(path string) error {
		cmd := exec.Command(path, "/S", "/UPDATE", "/RELAUNCH")
		cmd.SysProcAttr = &syscall.SysProcAttr{
			HideWindow:    true,
			CreationFlags: windows.DETACHED_PROCESS | windows.CREATE_NEW_PROCESS_GROUP,
		}
		if err := cmd.Start(); err != nil {
			return errors.New("설치 프로그램을 실행할 수 없습니다: " + err.Error())
		}
		_ = cmd.Process.Release()
		log.Printf("업데이트 설치 프로그램 실행: %s", filepath.Base(path))
		go func() {
			time.Sleep(800 * time.Millisecond) // 화면이 "설치 중" 응답을 받을 시간
			onLaunched()
		}()
		return nil
	}
	return m
}

func samePath(a, b string) bool { return strings.EqualFold(filepath.Clean(a), filepath.Clean(b)) }

func msgBox(text string, flags uint32) int32 {
	t, _ := windows.UTF16PtrFromString(text)
	c, _ := windows.UTF16PtrFromString(windowTitle)
	r, _ := windows.MessageBox(0, t, c, flags)
	return r
}

func openInBrowser(url string) {
	u, _ := windows.UTF16PtrFromString(url)
	op, _ := windows.UTF16PtrFromString("open")
	_ = windows.ShellExecute(0, op, u, nil, nil, swShow)
}

func setupLog() {
	dir := app.LocalDir()
	_ = os.MkdirAll(dir, 0o700)
	if f, err := os.OpenFile(filepath.Join(dir, "oicmd.log"), os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600); err == nil {
		if st, _ := f.Stat(); st != nil && st.Size() > 1<<20 {
			_ = f.Truncate(0)
		}
		log.SetOutput(f)
	}
}
