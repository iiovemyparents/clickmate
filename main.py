import os
import sys
import ctypes

def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        sys.exit()

run_as_admin()

from clickmate import Clickmate

def main():
    try:
        clickmate = Clickmate()
        clickmate.run()
    except Exception as e:
        print("Error:", e)
    finally:
        input("Press Enter to continue..")

if __name__ == "__main__":
    main()