import os
import winreg
import urllib.request
import urllib.error
import json
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
    if not token:
        print("Error: No GH_PAT found")
        sys.exit(1)
        
    url = "https://api.github.com/repos/hakutaku-blog/logic-nodes/actions/workflows/auto-publish.yml/dispatches"
    data = json.dumps({"ref": "main"}).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    
    try:
        urllib.request.urlopen(req)
        print("Success! Workflow dispatched.")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        print(e.read().decode("utf-8"))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
