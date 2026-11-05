#!/usr/bin/env bash
# One-time setup on CachyOS/Arch. Asks for your sudo password. Safe to rerun.
set -euo pipefail
cd "$(dirname "$0")"

sudo pacman -S --needed --noconfirm terraform docker
sudo systemctl enable --now docker.service

if ! id -nG "$USER" | grep -qw docker; then
  sudo usermod -aG docker "$USER"
  echo ">>> Added you to the docker group. Log out and back in, then rerun ./setup.sh to finish."
  exit 0
fi

terraform version | head -1
docker version --format 'Docker client {{.Client.Version}}, server {{.Server.Version}}'
python3 --version

[ -f terraform/lab.auto.tfvars.json ] || cp terraform/lab.auto.tfvars.example.json terraform/lab.auto.tfvars.json
terraform -chdir=terraform init -input=false
terraform -chdir=terraform validate
docker pull nginx:1.27-alpine
python3 tests/test_scripts.py
echo ">>> Setup complete. Start the lab at the 0:10 Launch step of the run sheet."
