import subprocess

commands = [
    "docker build -t urlshortner .",
    "docker run -d -p 5000:5000 urlshortner"
]

for command in commands:
    print(f"\n> {command}")
    subprocess.run(command, shell=True, check=True)