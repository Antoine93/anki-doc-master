import subprocess

# Config
target_dir = r"C:\Users\Antoine\Desktop\anki-doc-master"
# On lance la commande de base
ps_cmd = f"cd '{target_dir}'; claude --resume"

# Lancement propre d'une nouvelle fenêtre
subprocess.Popen([
    "powershell.exe",
    "-NoExit",
    "-Command",
    ps_cmd
], creationflags=subprocess.CREATE_NEW_CONSOLE)
