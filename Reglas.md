# Reglas del Juego - One Night Ultimate Werewolf (Versión Web)

Este documento describe las reglas principales de **One Night Ultimate Werewolf (ONUW)** adaptadas a la versión web.  
Sirve como **contexto** para implementar la lógica del juego en el proyecto y que se entienda la mecánica.

---

## Objetivo del Juego
- Los **Aldeanos** deben identificar y eliminar al menos a un Hombre Lobo.  
- Los **Hombres Lobo** deben sobrevivir hasta el final de la partida.  
- Otros roles especiales modifican las condiciones y generan dinámicas adicionales.  

---

## Preparación en la Versión Web
1. Cada jugador recibe un **rol inicial** asignado de forma oculta por el sistema.  
2. Existen también **roles no asignados** que quedan ocultos en el "centro virtual" (reservados por el sistema).  
3. Cada jugador solo conoce su **rol inicial** mostrado en pantalla al comienzo.  

---

## Fases del Juego

### 1. Fase Nocturna
- Todos los jugadores entran en **modo nocturno** (pantalla bloqueada salvo mensajes del narrador).  
- El **narrador digital** (actualmente un texto en la pantalla de cada jugador) anuncia los roles uno por uno en un orden fijo.  
- Cuando un rol es llamado, los jugadores con ese rol reciben instrucciones y pueden realizar su acción en la interfaz.  

### Orden completo de roles en la Noche

1. **Hombres Lobo**  
   - Si hay dos o más, se reconocen entre ellos.  
   - Si hay solo uno, puede mirar un rol del centro virtual.  

2. **Masones**  
   - Los Masones abren los ojos y se reconocen entre ellos.  

3. **Vidente**  
   - Puede mirar el rol de un jugador **o** dos roles del centro virtual.  

4. **Ladrón**  
   - Intercambia su rol con el de otro jugador.  
   - Mira su nuevo rol tras el intercambio.  

5. **Borracho**  
   - Intercambia su rol con uno del centro virtual.  
   - No puede mirar cuál es su nuevo rol.  

6. **Insomne**  
   - Al final de la fase nocturna, mira su rol actual para comprobar si cambió.  

*(Nota: algunos roles no realizan acción nocturna, pero pueden aparecer en la partida. Ejemplo: Aldeano, Cazador, Curtidor).*  

---

### 2. Fase Diurna
- Se termina la fase nocturna y todos los jugadores reciben la indicación en pantalla de que comienza la **fase de debate**.  
- Los jugadores pueden comunicarse (por chat o voz) para discutir lo que sucedió durante la noche.  
- Cada jugador puede **mentir o decir la verdad** sobre su rol y lo que vio.  
- El objetivo es descubrir quiénes son los Hombres Lobo.  

### 3. Votación
- Una vez finalizado el tiempo de discusión, cada jugador debe **emitir un voto** en la interfaz señalando a otro jugador.  
- El sistema cuenta los votos:  
  - El jugador más votado es eliminado.  
  - Si hay empate, todos los empatados son eliminados.  

---

## Condiciones de Victoria
- **Aldeanos ganan**: si al menos un Hombre Lobo es eliminado.  
- **Hombres Lobo ganan**: si ninguno es eliminado.  
- **Roles especiales**:
  - **Curtidor (Tanner)**: gana solo si él mismo es eliminado.  
  - **Cazador**: si es eliminado, el jugador al que votó también muere.  

---

## Puntos Clave para Implementación en Web
- Los **roles pueden cambiar** dinámicamente durante la noche (ej. Ladrón, Borracho).  
- El estado del juego se define en cada fase:
  - Roles iniciales asignados por el sistema.  
  - Acciones nocturnas procesadas automáticamente según las elecciones de los jugadores.  
  - Votación final registrada en la interfaz.  
- El flujo es siempre:  
  **Asignación de roles → Noche (acciones guiadas por el narrador digital) → Día (discusión) → Votación → Resolución**.  

---
