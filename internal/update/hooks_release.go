//go:build !updatetest

package update

// 배포용 빌드: 업데이트 주소·공개 키는 고정 (환경 변수로 못 바꿈).
func testFeed() string     { return "" }
func testAllowLocal() bool { return false }
