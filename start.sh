#!/bin/bash
set -e

echo "🐺 ========================================="
echo "    INICIANDO ONE NIGHT WEREWOLF (DDD)     "
echo "========================================="

cd "$(dirname "$0")"

# 1. Traer la última versión de develop limpiamente
echo "📦 Actualizando a la última versión de GitHub..."
git fetch origin develop
git checkout develop
git reset --hard origin/develop

echo "📌 Versión actual desplegada:"
git log -n 1 --oneline

# 2. Configurar variables para HTTPS
echo "VITE_SOCKET_URL=" > .env

# 3. Reconstruir los contenedores asegurando que no use caché vieja
echo "🚀 Reconstruyendo backend y frontend (sin caché)..."
docker compose build --no-cache
docker compose down
docker compose up -d

# 4. Mantener el túnel de Cloudflare si ya existe para NO cambiar la URL
if docker ps --format '{{.Names}}' | grep -q '^tunnel$'; then
    echo "🔒 Túnel HTTPS ya activo (manteniendo la misma URL sin cambios)..."
else
    echo "🔒 Levantando nuevo túnel HTTPS de Cloudflare..."
    docker rm -f tunnel 2>/dev/null || true
    docker run -d --name tunnel --restart unless-stopped --network host cloudflare/cloudflared:latest tunnel --url http://localhost:80
fi

# 5. Obtener enlace HTTPS
echo "⏳ Obteniendo enlace público..."
URL=""
for i in $(seq 1 15); do
    URL=$(docker logs tunnel 2>&1 | grep -o 'https://[a-zA-Z0-9.-]*\.trycloudflare\.com' | head -n 1 || true)
    if [ -n "$URL" ]; then
        break
    fi
    sleep 1
done

echo ""
echo "================================================="
if [ -n "$URL" ]; then
    echo "🎉 ¡TODO LISTO! Enlace de la partida:"
    echo ""
    echo "👉 $URL"
    echo ""
else
    echo "⚠️ El túnel arrancó pero la URL tarda en salir. Ejecuta:"
    echo "docker logs tunnel 2>&1 | grep -o 'https://.*\.trycloudflare\.com'"
fi
echo "================================================="
