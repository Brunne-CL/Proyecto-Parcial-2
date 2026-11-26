#!/bin/bash
# Una sola vez, dentro de la EC2, antes de conectar GitHub Actions.
set -eu

if command -v dnf >/dev/null 2>&1; then
  sudo dnf update -y
  sudo dnf install -y docker git curl
elif command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y docker.io git curl
else
  echo "Instale Docker, Git y curl con el gestor de esta distribución." >&2
  exit 1
fi

sudo systemctl enable --now docker
sudo usermod -aG docker "$USER" || true

if ! docker compose version >/dev/null 2>&1 && ! sudo docker compose version >/dev/null 2>&1; then
  sudo mkdir -p /usr/libexec/docker/cli-plugins /usr/local/lib/docker/cli-plugins
  archivo=/tmp/docker-compose
  curl -fsSL "https://github.com/docker/compose/releases/download/v2.32.4/docker-compose-linux-x86_64" -o "$archivo"
  sudo install -m 755 "$archivo" /usr/libexec/docker/cli-plugins/docker-compose
  sudo install -m 755 "$archivo" /usr/local/lib/docker/cli-plugins/docker-compose
fi

sudo mkdir -p /opt/gestion-usuarios
sudo chown "$USER":"$USER" /opt/gestion-usuarios

echo "Docker quedó instalado."
echo "Clone el repositorio en /opt/gestion-usuarios, copie .env.example a .env"
echo "y levante la pila: sudo docker compose --profile servidor up -d --build"
echo "Cierre la sesión SSH y vuelva a entrar para usar docker sin sudo."
