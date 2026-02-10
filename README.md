# One Night Werewolf - DDD Edition

Este proyecto es una implementación del juego "One Night Ultimate Werewolf" utilizando Domain-Driven Design (DDD) y una arquitectura moderna full-stack.

## 🎮 Descripción del Proyecto

One Night Werewolf es un juego de roles social donde los jugadores intentan identificar quiénes son los hombres lobo entre ellos en una única noche. Esta implementación digital mantiene la esencia del juego de mesa original mientras aprovecha las ventajas de la tecnología moderna.

## 🏗 Arquitectura

El proyecto está estructurado siguiendo los principios de Domain-Driven Design (DDD):

### Backend (Python)
- `domain/`: Contiene la lógica central del juego y las entidades principales
  - `game_logic.py`: Mecánicas principales del juego
  - `player.py`: Gestión de jugadores
  - `roles.py`: Definición de roles del juego

- `infrastructure/`: Capa de infraestructura
  - `room_repository.py`: Gestión de salas de juego

- `services/`: Servicios de aplicación
  - `game_service.py`: Coordinación de la lógica del juego

- `main/`: Punto de entrada de la aplicación
  - `app.py`: Configuración y rutas principales

### Frontend (React)
- `components/`: Componentes React reutilizables
  - `Lobby.jsx`: Sala de espera
  - `RoleSelector.jsx`: Selector de roles
  - `GameLog.jsx`: Registro de eventos del juego
  - `NightPhase.jsx`: Fase nocturna del juego

- `hooks/`: Custom hooks de React
  - `useSocket.js`: Gestión de conexiones WebSocket

- `store/`: Estado global de la aplicación
  - `gameStore.js`: Estado del juego usando Zustand

## 🚀 Tecnologías Utilizadas

### Backend
- Python
- Flask
- SocketIO
- Domain-Driven Design

### Frontend
- React
- Zustand (Gestión de estado)
- Socket.io-client
- Tailwind CSS

## 📦 Instalación

### Backend
1. Navega al directorio backend
```bash
cd backend
```

2. Instala las dependencias
```bash
pip install -r requirements.txt
```

3. Inicia el servidor
```bash
python run.py
```

### Frontend
1. Navega al directorio frontend
```bash
cd frontend
```

2. Instala las dependencias
```bash
npm install
```

3. Inicia la aplicación
```bash
npm start
```

## 🌐 Estado Actual del Desarrollo

El proyecto se encuentra actualmente en desarrollo activo, con foco en:
- Mejoras en la interfaz de usuario
- Corrección de errores en el frontend
- Implementación completa de todas las mecánicas de roles
- Optimización de la comunicación en tiempo real

## 📝 Convenciones de Git

El proyecto sigue la metodología Git Flow con las siguientes ramas principales:
- `main`: Código en producción
- `develop`: Rama de desarrollo
- `feature/*`: Nuevas características
- `fix/*`: Correcciones de errores
- `release/*`: Preparación de versiones

## 👥 Contribución

Las contribuciones son bienvenidas. Por favor, asegúrate de:
1. Crear una rama desde `develop` para nuevas características
2. Seguir las convenciones de código existentes
3. Incluir pruebas cuando sea posible
4. Documentar los cambios realizados

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
