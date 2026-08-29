Option Explicit
Dim sh, fso, here, url, http, errN
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh = CreateObject("WScript.Shell")
here = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = here
url = "http://127.0.0.1:8766/"

On Error Resume Next
Set http = CreateObject("MSXML2.XMLHTTP")
http.Open "GET", url & "api/sante", False
http.Send
errN = Err.Number
On Error GoTo 0

If errN <> 0 Then
  Dim py
  py = here & "\.venv\Scripts\pythonw.exe"
  If Not fso.FileExists(py) Then py = "pythonw"
  sh.Run """" & py & """ -m uvicorn app.main:app --host 127.0.0.1 --port 8766", 0, False
  WScript.Sleep 1200
End If

sh.Run url
