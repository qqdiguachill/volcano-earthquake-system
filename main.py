import subprocess
import sys
from pathlib import Path

def run_script(script_name):
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        print(f"找不到檔案: {script_name}")
        return
    print(f"\n=== 執行 {script_name} ===")
    subprocess.run([sys.executable, str(script_path)], check=True)

if __name__ == "__main__":
    run_script("tenki_ash.py")
    run_script("jma_eqvol.py")
    run_script("jma_earthquake.py")

    print("\n全部執行完畢")