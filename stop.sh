#!/bin/bash

echo "🛑 ========================================="
echo "    DETENIENDO ONE NIGHT WEREWOLF (DDD)    "
echo "========================================="

cd "$(dirname "$0")"

docker compose down
docker rm -f tunnel 2>/dev/null || true

echo ""
echo "✅ Todo apagado correctamente."
echo "Ya puedes detener la instancia en la consola de AWS."
echo "========================================="
