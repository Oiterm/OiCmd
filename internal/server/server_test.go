package server

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func start(t *testing.T) (*Server, string, string) {
	t.Helper()
	s := &Server{DataDir: t.TempDir()}
	u, err := s.Start("127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(s.Stop)
	base := strings.SplitN(u, "#", 2)[0]
	tok := strings.TrimPrefix(strings.SplitN(u, "#", 2)[1], "t=")
	return s, strings.TrimSuffix(base, "/"), tok
}

func do(t *testing.T, method, url, tok, body string, hdr map[string]string) (int, string) {
	t.Helper()
	req, _ := http.NewRequest(method, url, strings.NewReader(body))
	if tok != "" {
		req.Header.Set("X-OiCmd-Token", tok)
	}
	for k, v := range hdr {
		if k == "Host" {
			req.Host = v
		} else {
			req.Header.Set(k, v)
		}
	}
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer res.Body.Close()
	b, _ := io.ReadAll(res.Body)
	return res.StatusCode, string(b)
}

func TestTokenAndHost(t *testing.T) {
	_, base, tok := start(t)
	if c, _ := do(t, "GET", base+"/api/user", "", "", nil); c != 403 {
		t.Fatalf("토큰 없이 %d", c)
	}
	if c, _ := do(t, "GET", base+"/api/user", "wrong", "", nil); c != 403 {
		t.Fatalf("틀린 토큰 %d", c)
	}
	if c, _ := do(t, "GET", base+"/api/user", tok, "", nil); c != 200 {
		t.Fatalf("맞는 토큰 %d", c)
	}
	// DNS 리바인딩: Host 가 다르면 화면 파일도 거절
	if c, _ := do(t, "GET", base+"/", "", "", map[string]string{"Host": "evil.example:80"}); c != 403 {
		t.Fatalf("다른 Host %d", c)
	}
	if c, b := do(t, "GET", base+"/", "", "", nil); c != 200 || !strings.Contains(b, "OiCmd") {
		t.Fatalf("화면 %d", c)
	}
	if c, _ := do(t, "GET", base+"/api/nothing", tok, "", nil); c != 404 {
		t.Fatalf("없는 API %d", c)
	}
}

func TestUserData(t *testing.T) {
	s, base, tok := start(t)
	if c, b := do(t, "PUT", base+"/api/user", tok, `[1,2]`, nil); c != 400 {
		t.Fatalf("배열 %d %s", c, b)
	}
	if c, _ := do(t, "PUT", base+"/api/user", tok, `{"custom":[{"id":"u-1","t":"x"}],"settings":{"autoUpdate":false}}`, nil); c != 200 {
		t.Fatal("저장 실패")
	}
	if s.AutoUpdate() {
		t.Fatal("autoUpdate false 를 못 읽음")
	}
	if c, _ := do(t, "PUT", base+"/api/user", tok, `{"custom":[]}`, nil); c != 200 {
		t.Fatal("두 번째 저장 실패")
	}
	if _, err := os.Stat(filepath.Join(s.DataDir, "user.json.bak")); err != nil {
		t.Fatal("이전 내용(.bak)이 없음")
	}
	_, b := do(t, "GET", base+"/api/user", tok, "", nil)
	if strings.TrimSpace(b) != `{"custom":[]}` {
		t.Fatalf("읽은 내용 %s", b)
	}
	big := `{"x":"` + strings.Repeat("a", maxUserData) + `"}`
	if c, _ := do(t, "PUT", base+"/api/user", tok, big, nil); c != 413 {
		t.Fatalf("큰 데이터 %d", c)
	}
	// 망가진 파일은 옆으로 치우고 빈 데이터
	os.WriteFile(filepath.Join(s.DataDir, "user.json"), []byte("{망가짐"), 0o600)
	_, b = do(t, "GET", base+"/api/user", tok, "", nil)
	if !strings.Contains(b, "_warning") {
		t.Fatalf("망가진 파일 %s", b)
	}
	if !s.AutoUpdate() {
		t.Fatal("파일이 없으면 자동 확인은 켜짐이어야 함")
	}
}

func TestSafeExternalURL(t *testing.T) {
	ok := []string{"https://github.com/Oiterm/OiCmd/releases/latest", "https://www.juniper.net/documentation/"}
	bad := []string{"http://github.com/", "https://github.com.evil.com/", "https://evil.com/github.com", "file:///c:/windows", "https://github.com/a b", `https://github.com/"x`, "javascript:alert(1)"}
	for _, u := range ok {
		if !SafeExternalURL(u) {
			t.Errorf("열려야 함: %s", u)
		}
	}
	for _, u := range bad {
		if SafeExternalURL(u) {
			t.Errorf("막혀야 함: %s", u)
		}
	}
}

// commands.json: 형식, 중복 id, 벤더·분야가 다 있는지
func TestCommandsData(t *testing.T) {
	b, err := uiFS.ReadFile("ui/commands.json")
	if err != nil {
		t.Fatal(err)
	}
	var d struct {
		Vendors []struct{ ID, Name string } `json:"vendors"`
		Cats    []struct{ ID, Name string } `json:"cats"`
		Entries []struct {
			ID, Cat, Kind, T string
			V                map[string]struct {
				Cmd  *string `json:"cmd"`
				Note string  `json:"note"`
			} `json:"v"`
		} `json:"entries"`
		Guides []struct {
			ID, Cat, T, Mode string
			V                map[string]struct {
				None  string `json:"none"`
				Steps []struct{ C, D string } `json:"steps"`
			} `json:"v"`
		} `json:"guides"`
	}
	if err := json.Unmarshal(b, &d); err != nil {
		t.Fatal(err)
	}
	if len(d.Vendors) != 5 || len(d.Entries) < 50 {
		t.Fatalf("벤더 %d, 항목 %d", len(d.Vendors), len(d.Entries))
	}
	cats := map[string]bool{}
	for _, c := range d.Cats {
		cats[c.ID] = true
	}
	ids := map[string]bool{}
	for _, e := range d.Entries {
		if ids[e.ID] {
			t.Errorf("중복 id %s", e.ID)
		}
		ids[e.ID] = true
		if !cats[e.Cat] {
			t.Errorf("%s: 없는 분야 %s", e.ID, e.Cat)
		}
		if e.Kind != "show" && e.Kind != "exec" && e.Kind != "config" {
			t.Errorf("%s: kind %s", e.ID, e.Kind)
		}
		n := 0
		for _, v := range d.Vendors {
			x, ok := e.V[v.ID]
			if !ok {
				t.Errorf("%s: %s 빠짐", e.ID, v.ID)
				continue
			}
			if x.Cmd == nil && x.Note == "" {
				t.Errorf("%s/%s: 명령도 메모도 없음", e.ID, v.ID)
			}
			if x.Cmd != nil {
				n++
				if strings.Count(*x.Cmd, "<") != strings.Count(*x.Cmd, ">") {
					t.Errorf("%s/%s: < > 짝이 안 맞음: %s", e.ID, v.ID, *x.Cmd)
				}
			}
		}
		if n == 0 {
			t.Errorf("%s: 명령이 하나도 없음", e.ID)
		}
	}
	// 따라하기: 분야, 벤더 다 있음, 단계마다 명령과 설명
	if len(d.Guides) < 30 {
		t.Fatalf("따라하기 %d개", len(d.Guides))
	}
	for _, g := range d.Guides {
		if ids[g.ID] {
			t.Errorf("중복 id %s", g.ID)
		}
		ids[g.ID] = true
		if !cats[g.Cat] || g.T == "" {
			t.Errorf("%s: 분야·제목", g.ID)
		}
		n := 0
		for _, v := range d.Vendors {
			x, ok := g.V[v.ID]
			if !ok {
				t.Errorf("%s: %s 빠짐", g.ID, v.ID)
				continue
			}
			if x.None != "" {
				continue
			}
			n++
			for i, st := range x.Steps {
				if st.C == "" || st.D == "" {
					t.Errorf("%s/%s: %d단계 비었음", g.ID, v.ID, i+1)
				}
			}
		}
		if n == 0 {
			t.Errorf("%s: 할 수 있는 벤더가 없음", g.ID)
		}
	}
}
