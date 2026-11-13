Target amd64-unicode ; 64-bit installer
!ifndef VERSION
  !define VERSION "0.0.0"
!endif
; OiCmd 는 서비스가 없는 도구라 관리자 권한 없이 지금 사용자에게만 설치한다.
; 프로그램 안의 업데이트가 실행할 때: /S /UPDATE /RELAUNCH

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "Sections.nsh"
!include "x64.nsh"
!include "FileFunc.nsh"

Var IsUpdate
Var Relaunch

!define UNINST "Software\Microsoft\Windows\CurrentVersion\Uninstall\OiCmd"
Name "OiCmd"
Caption "OiCmd ${VERSION} 설치"
OutFile "OiCmd-Setup-${VERSION}.exe"
InstallDir "$LOCALAPPDATA\Programs\OiCmd"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ManifestDPIAware true
BrandingText "OiCmd ${VERSION}"
ShowInstDetails show
ShowUninstDetails show

VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=1042 "ProductName" "OiCmd"
VIAddVersionKey /LANG=1042 "FileDescription" "OiCmd 설치 프로그램"
VIAddVersionKey /LANG=1042 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1042 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=1042 "CompanyName" "OiCmd"
VIAddVersionKey /LANG=1042 "LegalCopyright" "OiCmd"

!define MUI_ICON "oicmd.ico"
!define MUI_UNICON "oicmd.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "welcome.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "welcome.bmp"
!define MUI_ABORTWARNING

!define MUI_WELCOMEPAGE_TITLE "OiCmd ${VERSION} 설치"
!define MUI_WELCOMEPAGE_TEXT "시스코 · 주니퍼 · 얼라이드 · 알카텔 장비의 명령어를 나란히 찾아보고, 다른 벤더 명령어로 바꾸고, VLAN·포트 설정문을 만들어 주는 프로그램입니다.$\r$\n$\r$\n관리자 권한 없이 지금 사용자 계정에만 설치합니다. 이미 설치돼 있으면 내 명령어는 그대로 두고 새 버전으로 바꿉니다."
!insertmacro MUI_PAGE_WELCOME
!define MUI_COMPONENTSPAGE_SMALLDESC
!insertmacro MUI_PAGE_COMPONENTS
!define MUI_DIRECTORYPAGE_TEXT_TOP "OiCmd를 설치할 폴더를 고르세요 (기본값 그대로 두는 것을 권장).$\r$\n내 명령어·설정은 설치 폴더가 아니라 %APPDATA%\OiCmd 에 저장됩니다."
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE DirLeave
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TITLE "OiCmd 설치 완료"
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "OiCmd 실행"
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchApp
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "사용 설명서 보기"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Korean"

Section "OiCmd 프로그램 (필수)" SecMain
  SectionIn RO
SectionEnd

Section "바탕화면 바로가기" SecDesktop
SectionEnd

Section "-Install"
  SetShellVarContext current
  ${If} $IsUpdate == 1
    Sleep 2000 ; 업데이트: OiCmd 가 스스로 닫힐 시간
  ${EndIf}
  ; 내 계정에서 열려 있는 OiCmd 를 닫아야 파일을 바꿀 수 있다
  nsExec::Exec '"$SYSDIR\taskkill.exe" /f /fi "USERNAME eq $%USERNAME%" /im oicmd.exe'
  Pop $0
  Sleep 300
  SetOutPath "$INSTDIR"
  SetOverwrite on
  File "oicmd.exe"
  File "README.txt"
  File "THIRD_PARTY_LICENSES.txt"
  WriteRegStr HKCU "Software\OiCmd" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\OiCmd" "Version" "${VERSION}"
  WriteUninstaller "$INSTDIR\uninst.exe"
  CreateShortcut "$SMPROGRAMS\OiCmd.lnk" "$INSTDIR\oicmd.exe" "" "$INSTDIR\oicmd.exe" 0
  ${If} ${SectionIsSelected} ${SecDesktop}
    CreateShortcut "$DESKTOP\OiCmd.lnk" "$INSTDIR\oicmd.exe" "" "$INSTDIR\oicmd.exe" 0
  ${Else}
    Delete "$DESKTOP\OiCmd.lnk"
  ${EndIf}
  WriteRegStr HKCU "${UNINST}" "DisplayName" "OiCmd"
  WriteRegStr HKCU "${UNINST}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINST}" "Publisher" "OiCmd"
  WriteRegStr HKCU "${UNINST}" "DisplayIcon" "$INSTDIR\oicmd.exe,0"
  WriteRegStr HKCU "${UNINST}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINST}" "UninstallString" '"$INSTDIR\uninst.exe"'
  WriteRegStr HKCU "${UNINST}" "QuietUninstallString" '"$INSTDIR\uninst.exe" /S'
  WriteRegDWORD HKCU "${UNINST}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINST}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $1 $2 $3
  WriteRegDWORD HKCU "${UNINST}" "EstimatedSize" $1
  ${If} $Relaunch == 1
    Exec '"$INSTDIR\oicmd.exe"'
  ${EndIf}
SectionEnd

LangString DESC_Main ${LANG_KOREAN} "프로그램, 시작 메뉴 바로가기."
LangString DESC_Desktop ${LANG_KOREAN} "바탕화면에 OiCmd 아이콘을 만듭니다."
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_Main)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_Desktop)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "64비트 Windows에서만 설치할 수 있습니다." /SD IDOK
    Abort
  ${EndIf}
  SetRegView 64
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/UPDATE" $R1
  ${IfNot} ${Errors}
    StrCpy $IsUpdate 1
  ${EndIf}
  ClearErrors
  ${GetOptions} $R0 "/RELAUNCH" $R1
  ${IfNot} ${Errors}
    StrCpy $Relaunch 1
  ${EndIf}
  ; 업데이트: 이미 쓰던 폴더로 (/D= 를 주지 않았으면)
  ReadRegStr $0 HKCU "Software\OiCmd" "InstallDir"
  ${If} $0 != ""
  ${AndIf} $INSTDIR == "$LOCALAPPDATA\Programs\OiCmd"
    StrCpy $INSTDIR $0
  ${EndIf}
  SetShellVarContext current
  ${If} ${FileExists} "$DESKTOP\OiCmd.lnk"
    !insertmacro SelectSection ${SecDesktop}
  ${ElseIf} $IsUpdate == 1
    !insertmacro UnselectSection ${SecDesktop} ; 업데이트는 없던 바로가기를 만들지 않음
  ${EndIf}
FunctionEnd

Function DirLeave
  ; 이 계정으로 쓸 수 있는 폴더여야 한다
  ClearErrors
  CreateDirectory "$INSTDIR"
  FileOpen $0 "$INSTDIR\.oicmd-write-test" w
  ${If} ${Errors}
    MessageBox MB_ICONEXCLAMATION "이 폴더에는 지금 계정으로 쓸 수 없습니다.$\r$\n기본 폴더($LOCALAPPDATA\Programs\OiCmd)처럼 쓸 수 있는 곳을 고르세요."
    Abort
  ${EndIf}
  FileClose $0
  Delete "$INSTDIR\.oicmd-write-test"
FunctionEnd

Function LaunchApp
  Exec '"$INSTDIR\oicmd.exe"'
FunctionEnd

Function un.onInit
  SetRegView 64
FunctionEnd

Section "Uninstall"
  SetShellVarContext current
  MessageBox MB_YESNO|MB_ICONQUESTION "내 명령어·확인 표시·설정($APPDATA\OiCmd)도 함께 지울까요?$\r$\n$\r$\n[아니요]를 누르면 남겨두고, 다시 설치하면 그대로 이어서 씁니다." /SD IDNO IDYES purge
    Goto files
  purge:
    RMDir /r "$APPDATA\OiCmd"
  files:
  nsExec::Exec '"$SYSDIR\taskkill.exe" /f /fi "USERNAME eq $%USERNAME%" /im oicmd.exe'
  Pop $0
  Sleep 500
  Delete "$INSTDIR\oicmd.exe"
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\THIRD_PARTY_LICENSES.txt"
  Delete "$INSTDIR\uninst.exe"
  RMDir "$INSTDIR"
  RMDir /r "$LOCALAPPDATA\OiCmd" ; 창 캐시(WebView2), 받은 업데이트 파일, 로그
  Delete "$SMPROGRAMS\OiCmd.lnk"
  Delete "$DESKTOP\OiCmd.lnk"
  DeleteRegKey HKCU "${UNINST}"
  DeleteRegKey HKCU "Software\OiCmd"
SectionEnd
