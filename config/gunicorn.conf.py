import subprocess

# Creates the file that signals nginx to start handling requests
# Starts Uppy's Companion
def when_ready(server):
    open("/tmp/app-initialized", "w").close()
    subprocess.run(["mkdir", "companion/"])
    subprocess.run(["$(npm bin)/companion"], shell=True)


bind = "unix:///tmp/nginx.socket"
