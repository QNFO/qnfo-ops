' DeepChat boot guard launcher.
' Clears volatile Chromium/Electron profile state (lockfile, DIPS/DIPS-wal,
' SharedStorage, Session Storage, caches, DevToolsActivePort) and THEN launches
' DeepChat.exe. This is the permanent fix for the blank-window-on-startup bug:
' a dirty profile can no longer reach the app. Runs hidden (window style 0).
Set sh = CreateObject("WScript.Shell")
sh.Run """C:\Users\LENOVO\AppData\Local\Programs\Python\Python312\pythonw.exe"" ""C:\Users\LENOVO\DeepChatData\dotdeepchat\scripts\deepchat_boot_guard.py""", 0, False
