import subprocess


def when_ready(server):
    open("/tmp/app-initialized", "w").close()
    subprocess.run(["$(npm bin)/companion", "-l"], shell=True)


bind = "unix:///tmp/nginx.socket"
