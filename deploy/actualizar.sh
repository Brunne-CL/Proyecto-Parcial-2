#!/bin/bash
# Lo ejecuta GitHub Actions, ya parado en /opt/gestion-usuarios y con el código nuevo.
set -eu

if ! sudo docker compose version >/dev/null 2>&1; then
  echo "Falta docker compose. Ejecute deploy/bootstrap-ec2.sh en la instancia." >&2
  exit 1
fi

sudo docker compose --profile servidor up -d --build

for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
  if curl -fsS http://127.0.0.1:8080/salud; then
    echo
    exit 0
  fi
  sleep 2
done

echo "La aplicación no respondió en /salud. El despliegue queda como fallo." >&2
exit 1
