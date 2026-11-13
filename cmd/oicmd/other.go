//go:build !windows

package main

// Windows 가 아니면 창 대신 serve 와 같게 동작한다.
func runDefault(args []string) { serve(args) }
