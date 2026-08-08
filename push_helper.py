import os
import winreg
import subprocess
import sys

def get_env_var(name):
    val = os.environ.get(name)
    if val: return val
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            val, _ = winreg.QueryValueEx(key, name)
            if val: return val
    except WindowsError:
        pass
    return None

def main():
    token = get_env_var("GH_PAT")
    git_exe = r"C:\Users\takut\.gemini\antigravity\scratch\git\cmd\git.exe"
    push_url = f"https://x-access-token:{token}@github.com/hakutaku-blog/logic-nodes.git"
    
    subprocess.run([git_exe, "add", "."], check=True)
    subprocess.run([git_exe, "commit", "-m", "fix: remove hallucinated episode numbering from 8/7 and 8/8 articles"], capture_output=True)
    subprocess.run([git_exe, "push", push_url, "main"])

if __name__ == "__main__":
    main()
