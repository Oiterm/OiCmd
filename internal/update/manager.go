package update

import (
	"context"
	"errors"
	"log/slog"
	"sync"
	"time"
)

// Manager 는 하루 한 번 확인, 화면에서 확인·설치를 맡는다.
type Manager struct {
	Cfg Config
	Log *slog.Logger
	// Enabled: 설정의 "자동으로 새 버전 확인"
	Enabled func() bool
	// Plan: 이 설치 방식에서 받을 파일 종류(setup / setup_user)와 안내. 자동 설치가 안 되면(포터블 등) err.
	Plan func() (key string, err error)
	// Apply: 확인된 설치 파일을 실행한다(조용히 설치 → 다시 시작). 실행만 하고 바로 돌아온다.
	Apply func(path string) error

	mu         sync.Mutex
	checking   bool
	installing bool
	lastCheck  time.Time
	lastErr    string
	avail      *Manifest
	phase      string // 설치 진행: "", "download", "launch", "done", "error"
	phaseMsg   string
}

type Status struct {
	Current     string    `json:"current"`
	Auto        bool      `json:"auto"`
	Checking    bool      `json:"checking"`
	LastCheck   int64     `json:"last_check"`
	Error       string    `json:"error"`
	Available   *Manifest `json:"available"`
	Installable bool      `json:"installable"`
	PlanNote    string    `json:"plan_note"`
	Page        string    `json:"page"`
	Phase       string    `json:"phase"`
	PhaseMsg    string    `json:"phase_msg"`
	Package     string    `json:"package"` // 오프라인 업데이트 파일 이름 예시
}

func (m *Manager) Status() Status {
	m.mu.Lock()
	defer m.mu.Unlock()
	st := Status{Current: m.Cfg.Current, Checking: m.checking, Error: m.lastErr, Available: m.avail, Page: m.Cfg.ReleasePage(),
		Phase: m.phase, PhaseMsg: m.phaseMsg, Package: PackageName(m.Cfg.Product, "버전")}
	if m.Enabled != nil {
		st.Auto = m.Enabled()
	}
	if !m.lastCheck.IsZero() {
		st.LastCheck = m.lastCheck.Unix()
	}
	if m.Plan != nil && m.Apply != nil {
		if _, err := m.Plan(); err != nil {
			st.PlanNote = err.Error()
		} else {
			st.Installable = true
		}
	} else {
		st.PlanNote = "이 실행 방식(명령 프롬프트 등)에서는 자동 설치가 안 됩니다. 설치 프로그램을 직접 실행하세요"
	}
	return st
}

// Check 는 지금 확인한다.
func (m *Manager) Check(ctx context.Context) Status {
	m.mu.Lock()
	if m.checking {
		m.mu.Unlock()
		return m.Status()
	}
	m.checking = true
	m.mu.Unlock()
	man, err := m.Cfg.Check(ctx)
	m.mu.Lock()
	m.checking = false
	m.lastCheck = time.Now()
	if err != nil {
		m.lastErr = err.Error()
	} else {
		m.lastErr = ""
		m.avail = man
	}
	m.mu.Unlock()
	if err != nil && m.Log != nil {
		m.Log.Info("업데이트 확인 실패", "err", err)
	} else if man != nil && m.Log != nil {
		m.Log.Info("새 버전이 있습니다", "version", man.Version)
	}
	return m.Status()
}

// Run 은 켜져 있으면 시작 2분 뒤, 그다음 20시간마다 확인한다.
func (m *Manager) Run(ctx context.Context) {
	t := time.NewTimer(2 * time.Minute)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
		}
		if m.Enabled == nil || m.Enabled() {
			cctx, cancel := context.WithTimeout(ctx, 2*time.Minute)
			m.Check(cctx)
			cancel()
		}
		t.Reset(20 * time.Hour)
	}
}

var ErrBusy = errors.New("이미 업데이트를 진행 중입니다")

func (m *Manager) begin() error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if m.installing {
		return ErrBusy
	}
	m.installing = true
	m.phase, m.phaseMsg = "download", "받는 중"
	return nil
}

func (m *Manager) finish(err error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.installing = false
	if err != nil {
		m.phase, m.phaseMsg = "error", err.Error()
		if m.Log != nil {
			m.Log.Warn("업데이트 실패", "err", err)
		}
		return
	}
	m.phase, m.phaseMsg = "done", "설치 프로그램을 실행했습니다. 잠시 뒤 새 버전으로 다시 시작합니다"
}

// Install 은 확인된 새 버전을 받아서(백그라운드) 설치한다.
func (m *Manager) Install() (string, error) {
	m.mu.Lock()
	man := m.avail
	m.mu.Unlock()
	if man == nil {
		return "", errors.New("먼저 새 버전을 확인하세요")
	}
	if m.Plan == nil || m.Apply == nil {
		return "", errors.New("이 환경에서는 자동 설치가 안 됩니다")
	}
	key, err := m.Plan()
	if err != nil {
		return "", err
	}
	if err := m.begin(); err != nil {
		return "", err
	}
	go func(mf Manifest) {
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Minute)
		defer cancel()
		path, err := m.Cfg.Download(ctx, mf, key)
		if err == nil {
			m.setPhase("launch", "설치 프로그램을 실행하는 중")
			err = m.Apply(path)
		}
		m.finish(err)
	}(*man)
	return man.Version, nil
}

// InstallPackage 는 화면에서 올린 업데이트 파일(zip)로 설치한다. 확인까지는 바로 하고, 실행은 바로 시작한다.
func (m *Manager) InstallPackage(data []byte) (Manifest, error) {
	if m.Plan == nil || m.Apply == nil {
		return Manifest{}, errors.New("이 환경에서는 자동 설치가 안 됩니다")
	}
	key, err := m.Plan()
	if err != nil {
		return Manifest{}, err
	}
	if err := m.begin(); err != nil {
		return Manifest{}, err
	}
	man, path, err := m.Cfg.OpenPackage(data, key)
	if err == nil {
		m.setPhase("launch", "설치 프로그램을 실행하는 중")
		err = m.Apply(path)
	}
	m.finish(err)
	return man, err
}

func (m *Manager) setPhase(p, msg string) {
	m.mu.Lock()
	m.phase, m.phaseMsg = p, msg
	m.mu.Unlock()
}
