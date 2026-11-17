---
name: add-new-role
description: Guía paso a paso para implementar un nuevo rol en One Night Ultimate Werewolf respetando la arquitectura DDD y el contrato de Socket.IO.
---

# Procedimiento para añadir un nuevo rol

Cuando el usuario pida añadir un rol nuevo (ej. Aprendiz de Vidente, Guardaespaldas, Paranormal, Cazador), sigue este orden estricto:

## 1. Capa de Dominio (`backend/domain/`)
1. **Definición del rol (`backend/domain/roles/`):**
   - Añade el identificador en `RoleType` y sus metadatos (nombre en español, equipo, prioridad nocturna) en `base.py`.
   - Crea el archivo `<nombre_rol>.py` heredando de `Role` (o añade la clase en `passive_roles.py` si no tiene acción nocturna).
   - Exporta la clase en `backend/domain/roles/__init__.py` y regístrala en `factory.py` (`RoleFactory`).
2. **Resolución de reglas:**
   - Si actúa de noche: integra su lógica en `backend/domain/night_resolution.py` respetando estrictamente el orden oficial de turnos.
   - Si altera votaciones, muertes o victorias: actualiza `backend/domain/voting_resolution.py`.

## 2. Capa de Aplicación (`backend/services/`)
- Verifica si `night_orchestrator.py`, `voting_orchestrator.py` o `state_emitter.py` necesitan enviar datos privados nuevos (`private_update` o `night_action`) para este rol.
- Asegúrate de no romper el temporizador de turnos falsos cuando el rol esté en las cartas del centro.

## 3. Frontend (`frontend/src/`)
1. **Constantes y estado:** Añade el rol, su descripción e icono en `constants.js` y verifica que `RoleSelector.jsx` permita seleccionarlo en el Lobby.
2. **Interfaz de acción:** Si tiene acción nocturna o diurna especial, crea su componente en `frontend/src/components/night-phases/<NombreRol>Phase.jsx` y conéctalo en `NightPhase.jsx`.
3. **Pantalla final:** Comprueba que `RevealPhase.jsx` muestra correctamente su rol inicial, su rol final y el motivo de victoria/derrota.

## 4. Verificación base
- Ejecuta `pytest` en `backend/` para confirmar que los roles existentes no se han roto.
- Invoca la skill `simulate-role-playtest` para probar el nuevo rol en partida.
