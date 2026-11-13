// OiCmd: 네트워크 장비 명령어 사전 (시스코 · 주니퍼 · 얼라이드 · 알카텔)
//
//	oicmd.exe            프로그램 창 (Windows)
//	oicmd serve [-addr]  창 없이 이 PC 의 브라우저로 쓰기 / 개발·시험용 (모든 OS)
//	oicmd version
package main

import (
	"flag"
	"fmt"
	"os"
	"os/signal"

	"oicmd/internal/app"
	"oicmd/internal/server"
)

func main() {
	args := os.Args[1:]
	if len(args) > 0 {
		switch args[0] {
		case "version", "--version", "-v":
			fmt.Println(app.Product, app.Version)
			return
		case "serve":
			serve(args[1:])
			return
		}
	}
	runDefault(args)
}

// serve: 창 없이 웹 서버만 띄운다. 주소(토큰 포함)를 출력한다.
func serve(args []string) {
	fs := flag.NewFlagSet("serve", flag.ExitOnError)
	addr := fs.String("addr", "127.0.0.1:0", "들을 주소 (127.0.0.1 만 가능)")
	_ = fs.Parse(args)
	s := &server.Server{DataDir: app.DataDir()}
	u, err := s.Start(*addr)
	if err != nil {
		fmt.Fprintln(os.Stderr, "시작할 수 없습니다:", err)
		os.Exit(1)
	}
	fmt.Println(app.Product, app.Version, "— 브라우저로 여세요 (종료: Ctrl+C)")
	fmt.Println(u)
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, os.Interrupt)
	<-ch
	s.Stop()
}
