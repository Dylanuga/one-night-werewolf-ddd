# Análisis Funcional del Proyecto: One Night Werewolf DDD

## 1. Propósito del Proyecto

El objetivo principal es ofrecer una versión web, multijugador y en tiempo real del juego "One Night Ultimate Werewolf", aplicando Domain-Driven Design (DDD) para lograr una arquitectura limpia, escalable y mantenible. El sistema permite a los jugadores participar en partidas donde se asignan roles secretos, se realizan acciones nocturnas y se vota para descubrir a los personajes ocultos.

---

## 2. Arquitectura General

- **Backend**: Organizado en capas DDD (Dominio, Servicios, Infraestructura, Main), con lógica de juego, gestión de partidas y comunicación en tiempo real mediante WebSockets.
- **Frontend**: React + Zustand para la gestión de estado y componentes de interfaz, sincronizados en tiempo real con el backend.

---

## 3. Reglas de las Partidas

- Cada partida requiere un número de roles igual al número de jugadores más tres cartas centrales.
- Los roles se asignan aleatoriamente (o de forma controlada en modo test) y cada uno tiene habilidades específicas.
- El flujo de la partida sigue fases estrictas: Lobby → Selección de roles → Noche → Día → Votación → Fin de partida.

---

## 4. Explicación de los Turnos

- Durante la **fase nocturna**, los jugadores actúan en un orden predefinido según su rol (por ejemplo: hombres lobo, masones, vidente, ladrón, etc.).
- Cada rol puede realizar una acción especial (ver cartas, intercambiar roles, etc.), implementada en la lógica de dominio.
- El sistema avanza automáticamente de un turno a otro, asegurando que cada jugador actúe solo cuando corresponde.
- Tras la noche, todos los jugadores discuten y luego votan.

---

## 5. Condiciones de Victoria

- El objetivo de los jugadores depende de su rol:
  - **Equipo Aldeanos**: Ganan si al menos un hombre lobo es eliminado o si no hay hombres lobo entre los jugadores y no se elimina a un aldeano especial (según reglas).
  - **Equipo Hombres Lobo**: Ganan si ningún hombre lobo es eliminado y al menos un aldeano es eliminado.
  - **Roles especiales**: Algunos roles pueden tener condiciones de victoria alternativas (por ejemplo, el "Tanner" gana si es eliminado).
- El sistema evalúa automáticamente el resultado tras la votación y muestra el equipo ganador.

---

## 6. Detalles Adicionales

- **Identidad y Reconexión**: Cada jugador tiene un identificador estable, permitiendo reconexión sin perder su estado.
- **Sincronización en tiempo real**: El estado de la partida y las acciones se actualizan instantáneamente para todos los jugadores.
- **Modo test**: Permite crear partidas con roles predefinidos y avanzar turnos manualmente para pruebas y depuración.
- **Extensibilidad**: El sistema está preparado para añadir nuevos roles y reglas fácilmente, manteniendo la lógica de negocio separada de la infraestructura y la interfaz.

---

## 7. Roles con Acciones Nocturnas

En "One Night Ultimate Werewolf", algunos roles tienen la capacidad de realizar acciones especiales durante la fase nocturna. Estas acciones son secretas y se ejecutan en un orden específico, uno por uno, solo si el rol está presente en la partida (según la selección del host).

### Ejemplos de Roles y sus Acciones Nocturnas

- **Hombre Lobo**: Se despiertan y se reconocen entre sí. Si solo hay uno, puede mirar una carta del centro.
- **Masones**: Se despiertan y se reconocen entre sí.
- **Vidente**: Puede mirar la carta de otro jugador o dos cartas del centro.
- **Ladrón**: Puede intercambiar su rol con el de otro jugador y ve el nuevo rol que recibe.
- **Otros roles especiales**: Según la configuración, pueden existir más roles con acciones nocturnas (por ejemplo, "Tanner", "Insomniac", etc.).

### Gestión de la Fase Nocturna

- Durante la **fase de noche**, solo se muestran los turnos de los roles que tienen acción nocturna y que han sido seleccionados para la partida.
- Cada jugador ve únicamente la interfaz de su propio turno nocturno, en el momento que le corresponde, y puede realizar su acción secreta.
- Los jugadores cuyos roles no tienen acción nocturna simplemente esperan hasta la fase de día.
- El sistema avanza automáticamente de un turno a otro, asegurando la confidencialidad y el orden correcto de las acciones.

---
