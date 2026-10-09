Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Set working directory to TEMP so Windows DLL loader doesn't collide with local directory DLLs
tempDir = WshShell.ExpandEnvironmentStrings("%TEMP%")
WshShell.CurrentDirectory = tempDir

pyScript = scriptDir & "\control_center.py"

Dim pyExe
If fso.FileExists("C:\Python314\pythonw.exe") Then
    pyExe = "C:\Python314\pythonw.exe"
ElseIf fso.FileExists("C:\Python312\pythonw.exe") Then
    pyExe = "C:\Python312\pythonw.exe"
ElseIf fso.FileExists("C:\Python311\pythonw.exe") Then
    pyExe = "C:\Python311\pythonw.exe"
Else
    pyExe = "pythonw.exe"
End If

cmd = """" & pyExe & """ """ & pyScript & """"

On Error Resume Next
WshShell.Run cmd, 0, False

If Err.Number <> 0 Then
    ' Fallback to python.exe if pythonw.exe failed
    Err.Clear
    WshShell.Run "python """ & pyScript & """", 1, False
    If Err.Number <> 0 Then
        MsgBox "Failed to launch Scrcpy Live Control Center." & vbCrLf & _
               "Please ensure Python and PyQt6 are installed." & vbCrLf & _
               "Error: " & Err.Description, vbCritical, "Scrcpy Launcher Error"
    End If
End If
