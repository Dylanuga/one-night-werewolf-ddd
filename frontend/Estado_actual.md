# 🐺 One Night Werewolf - Estado Actual (v0.2.0)

## ✅ FUNCIONALIDADES IMPLEMENTADAS:
- Crear/unirse a salas ✅
- Selección de roles ✅  
- Reconexión automática ✅
- Fase nocturna de lobos ✅
  - Caso A: 2 lobos se ven mutuamente ✅
  - Caso B: 1 lobo ve carta del centro ✅

## 🔧 ARCHIVOS CLAVE MODIFICADOS:
- `backend/domain/game_logic.py` - Distribución roles + debug
- `backend/services/game_service.py` - Reconexión + turnos nocturnos  
- `backend/main/app.py` - IDs estables de jugadores
- `backend/domain/roles.py` - Todos los roles añadidos
- `frontend/src/hooks/useSocket.js` - Reconexión automática
- `frontend/src/components/NightPhase.jsx` - Renderizado de lobos
- `frontend/src/components/RoleSelector.jsx` - Testing con múltiples lobos

## 🎯 PRÓXIMOS PASOS:
1. Implementar más roles (Seer, Robber, Troublemaker...)
2. Sistema de avance automático de turnos
3. Fase de votación
4. Cálculo de ganadores

## 🚨 PROBLEMAS CONOCIDOS:
- Ninguno crítico - base sólida ✅

## 📞 PARA NUEVA CONVERSACIÓN:
Adjuntar: ESTADO_ACTUAL.md + archivos clave modificados