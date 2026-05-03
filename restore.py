
import subprocess

def run(cmd, cwd=None):
    """Run a shell command safely."""
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

if __name__ == "__main__":
    run("git fetch origin")
    run("git reset --hard origin/master")
