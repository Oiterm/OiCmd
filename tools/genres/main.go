// genres builds rsrc_windows_amd64.syso (icon, manifest, version info) for
// oicmd.exe. Usage: go run . <version> <ico> <out.syso>
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/tc-hib/winres"
	"github.com/tc-hib/winres/version"
)

func main() {
	if len(os.Args) != 4 {
		fmt.Fprintln(os.Stderr, "usage: genres <version> <icon.ico> <out.syso>")
		os.Exit(2)
	}
	ver, icoPath, out := os.Args[1], os.Args[2], os.Args[3]
	var v4 [4]uint16
	for i, p := range strings.Split(ver, ".") {
		if i < 4 {
			n, _ := strconv.Atoi(p)
			v4[i] = uint16(n)
		}
	}
	rs := &winres.ResourceSet{}

	f, err := os.Open(icoPath)
	must(err)
	icon, err := winres.LoadICO(f)
	f.Close()
	must(err)
	must(rs.SetIcon(winres.ID(1), icon)) // ID 1 = app icon (window, tray, Explorer)

	rs.SetManifest(winres.AppManifest{
		Identity:            winres.AssemblyIdentity{Name: "OiCmd", Version: v4},
		Description:         "OiCmd network command dictionary",
		Compatibility:       winres.Win10AndAbove,
		ExecutionLevel:      winres.AsInvoker,
		DPIAwareness:        winres.DPIPerMonitorV2,
		UseCommonControlsV6: true,
		LongPathAware:       true,
	})

	vi := version.Info{}
	vi.SetFileVersion(ver)
	vi.SetProductVersion(ver)
	const ko = 0x0412
	must(vi.Set(ko, version.ProductName, "OiCmd"))
	must(vi.Set(ko, version.FileDescription, "OiCmd - 네트워크 장비 명령어 사전"))
	must(vi.Set(ko, version.CompanyName, "OiCmd"))
	must(vi.Set(ko, version.InternalName, "oicmd"))
	must(vi.Set(ko, version.OriginalFilename, "oicmd.exe"))
	must(vi.Set(ko, version.LegalCopyright, "OiCmd"))
	rs.SetVersionInfo(vi)

	w, err := os.Create(out)
	must(err)
	must(rs.WriteObject(w, winres.ArchAMD64))
	must(w.Close())
	fmt.Println("wrote", out)
}

func must(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
