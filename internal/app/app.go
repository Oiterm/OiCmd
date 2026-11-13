// Package app 은 OiCmd 의 버전과 사용자 데이터 위치를 정한다.
package app

import (
	"os"
	"path/filepath"
	"runtime"
)

// Version 은 릴리즈 버전 (release.yml 이 이 줄을 읽는다).
const Version = "1.2.0"

const Product = "OiCmd"

// DataDir 는 사용자 데이터(내 명령어, 확인 표시, 설정) 폴더.
//
//	OICMD_HOME 환경 변수 > Windows: %APPDATA%\OiCmd > 그 밖: ~/.config/oicmd
//
// 설치판·포터블 모두 같은 곳을 쓴다(포터블을 다른 PC 로 옮길 때는 화면의 [내보내기]를 쓴다).
func DataDir() string {
	if d := os.Getenv("OICMD_HOME"); d != "" {
		return d
	}
	if runtime.GOOS == "windows" {
		if d := os.Getenv("APPDATA"); d != "" {
			return filepath.Join(d, "OiCmd")
		}
	}
	if d, err := os.UserConfigDir(); err == nil {
		return filepath.Join(d, "oicmd")
	}
	return filepath.Join(os.TempDir(), "oicmd")
}

// LocalDir 는 지울 수 있는 캐시(WebView2 데이터, 받은 업데이트 파일, 로그) 폴더.
func LocalDir() string {
	if d := os.Getenv("OICMD_HOME"); d != "" {
		return filepath.Join(d, "local")
	}
	if runtime.GOOS == "windows" {
		if d := os.Getenv("LOCALAPPDATA"); d != "" {
			return filepath.Join(d, "OiCmd")
		}
	}
	if d, err := os.UserCacheDir(); err == nil {
		return filepath.Join(d, "oicmd")
	}
	return filepath.Join(os.TempDir(), "oicmd")
}
