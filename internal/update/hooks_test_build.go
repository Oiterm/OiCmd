//go:build updatetest

package update

// 시험 빌드(-tags updatetest) 전용: 로컬 시험 서버(http://127.0.0.1)와 시험 키를 쓸 수 있다.
// 배포 파일은 이 태그 없이 빌드한다 (build.sh, release.yml).
//
//	환경 변수 OI_UPDATE_FEED / OI_UPDATE_PUBKEY, 또는 서비스 시험용으로
//	-ldflags "-X oicmd/internal/update.testFeedURL=http://127.0.0.1:8765/ -X oinms/internal/update.testKeyB64=..."

import "os"

var testFeedURL, testKeyB64 string

func init() {
	if k := os.Getenv("OI_UPDATE_PUBKEY"); k != "" {
		testPublicKey = k
	} else if testKeyB64 != "" {
		testPublicKey = testKeyB64
	}
}

func testFeed() string {
	if f := os.Getenv("OI_UPDATE_FEED"); f != "" {
		return f
	}
	return testFeedURL
}

func testAllowLocal() bool { return testFeed() != "" }
