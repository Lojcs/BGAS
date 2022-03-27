import ctypes, os, sys
ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f"{os.getcwd()}\\BGAS.py", None, 1)