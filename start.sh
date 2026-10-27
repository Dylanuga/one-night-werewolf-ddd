#!/bin/bash
set -e

echo "🐺 ========================================="
echo "    INICIANDO ONE NIGHT WEREWOLF (DDD)     "
echo "========================================="

# 1. Asegurar directorio del proyecto
cd "$(dirname "$0")"

# 2. Intentar actualizar a develop más reciente
echo "📦 Actualizando a la última versión de develop..."
git checkout develop
git pull origin develop || echo "⚠️ Continuamos con la versión local si no hay conexión a GitHub."

# 3. Asegurar configuración para HTTPS con Cloudflare
echo "VITE_SOCKET_URL=" > .env

# 4. Levantar contenedores del juego
echo "🚀 Reconstruyendo y arrancando backend y frontend..."
docker compose down
docker compose up -d --build

# 5. Reiniciar túnel de Cloudflare
echo "🔒 Levantando túnel HTTPS de Cloudflare..."
docker rm -f tunnel 2>/dev/null || true
docker run -d --name tunnel --restart unless-stopped --network host cloudflare/cloudflared:latest tunnel --url http://localhost:80

# 6. Esperar a que el túnel devuelva la URL
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
    echo "🎉 ¡TODO LISTO! Comparte este enlace para jugar:"
    echo ""
    echo "👉 $URL"
    echo ""
else
    echo "⚠️ El túnel arrancó pero la URL tarda en salir. Ejecuta:"
    echo "docker logs tunnel 2>&1 | grep -o 'https://.*\.trycloudflare\.com'"
fi
echo "================================================="
