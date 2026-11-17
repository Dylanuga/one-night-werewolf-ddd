---
name: simulate-role-playtest
description: Simula partidas multijugador completas (como un grupo de amigos) en dos modos: Modo Partida Aleatoria General (5 jugadores) para regresiones, o Modo Rol Específico para verificar todos los casos límite de un personaje.
---

# Simulación de Playtest Multijugador

Este skill soporta **dos modos de ejecución** según lo que pida el usuario:

---

## MODO A: Partida Aleatoria General (5 Jugadores)
*(Activar cuando el usuario pida "una partida aleatoria general", "probar cambios generales" o no especifique un rol concreto).*

1. **Configuración de sala:**
   - Crea una sala de **5 jugadores** (usando `SocketIO test_client` multi-cliente y/o 5 pestañas en el navegador integrado con `?autoJoin=1` / `TestingPanel`).
   - Selecciona un mazo estándar equilibrado de 8 cartas (5 para jugadores + 3 para el centro) mezclando roles activos y pasivos (ej. 2 Lobos, Vidente, Ladrón, Alborotadora, Insomne, Curtidor, Aldeano) repartidos **de forma totalmente aleatoria**.
2. **Ejecución completa de la partida:**
   - **Lobby:** Todos los jugadores se unen, el anfitrión inicia la partida.
   - **Noche:** Cada jugador que tenga turno activo ejecuta una acción válida aleatoria dentro de su tiempo (mirar carta, robar, intercambiar, etc.), verificando que las transiciones visuales y temporizadores fluyen sin bloqueos.
   - **Día y Votación:** Simula el fin del debate y haz que los 5 jugadores emitan votos (incluyendo algún voto cruzado).
   - **Revelación (`RevealPhase`):** Verifica que se muestran correctamente los roles iniciales, los roles finales tras intercambios, los votos recibidos y el equipo ganador según `voting_resolution.py`.
   - **Reinicio:** Pulsa jugar de nuevo (`game_reset`) y confirma que la sala vuelve limpia al Lobby.

---

## MODO B: Batería Exhaustiva de un Rol Específico
*(Activar cuando el usuario pida probar un rol nuevo o concreto, ej. "haz un playtest del rol X").*

Ejecuta 5 partidas simuladas cubriendo estos escenarios obligatorios:
1. **El rol en el centro:** 4 jugadores + el rol objetivo en las 3 cartas del centro. Verificar que su turno falso corre sin bloquear la noche y que Vidente/Borracho interactúan bien con él.
2. **Uso activo en manos de un jugador:** Forzar que le toque a un jugador, ejecutar su habilidad y validar `privateState` y efectos.
3. **El "amigo despistado" (Timeout y reconexión F5):** Dejar expirar su turno sin pulsar nada y simular una reconexión (`reconnect_session`) en mitad de la noche.
4. **Intercambio nocturno (Ladrón / Alborotadora / Insomne):** Verificar que si le cambian la carta antes de actuar, sigue actuando creyendo tener su rol inicial y `RevealPhase` refleja el cambio final.
5. **Votación, muerte y condiciones de victoria:** Forzar votación contra el portador final del rol y un empate con Lobo/Curtidor para validar efectos al morir y jerarquía de victoria.

---

## Reporte final (Obligatorio en ambos modos)
Entrega al usuario un resumen claro con ✅ o ❌ por cada fase o escenario probado, detallando qué roles tocaron, qué acciones ocurrieron en la noche y quién ganó la partida simulada.
