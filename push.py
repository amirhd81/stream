import subprocess

def run(cmd, cwd=None):
    """Run a shell command safely."""
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

if __name__ == "__main__":
    run("git add .")
    run("git commit -m 'somthing'")
    run("git push origin master")
