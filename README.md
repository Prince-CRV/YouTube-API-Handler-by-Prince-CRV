# YouTube API Handler by Prince-CRV

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![YouTube API](https://img.shields.io/badge/YouTube_API-v3-red.svg)
![Architecture](https://img.shields.io/badge/Design_Pattern-Task_Strategy-green.svg)
![SOLID](https://img.shields.io/badge/Principles-SOLID-orange.svg)

Una potente herramienta de automatización para YouTube construida en Python, diseñada bajo principios de arquitectura limpia (**SOLID**). Este handler permite gestionar la programación de contenido, organización de listas de reproducción y optimización de metadatos de forma masiva y estratégica.



## 🎯 Propósito del Proyecto
Este repositorio no es solo un script; es un **framework extensible** para creadores de contenido. Gracias al cumplimiento del principio **Open/Closed (OCP)**, el sistema permite añadir nuevas tareas de automatización (como análisis de métricas o gestión de comentarios) sin necesidad de modificar el código base del motor de ejecución.

## ✨ Características Principales
* **Autenticación OAuth2 Robusta:** Manejo de sesiones mediante `token.pickle` con sistema de refresco automático para evitar logins manuales constantes.
* **Arquitectura Orientada a Tareas:** Implementación de la interfaz abstracta `YouTubeTask`, permitiendo una extensibilidad infinita.
* **Calendario Estratégico de Publicación:** Generación automática de slots de tiempo basados en picos de audiencia (almuerzos, fines de semana y cierres de día).
* **Gestión Inteligente de Shorts:** Filtrado automático de videos por duración (< 120s) y organización alfabética inversa.
* **Vinculación Dinámica:** Uso de expresiones regulares (Regex) para vincular automáticamente "Videos Relacionados" y formatear títulos con hashtags.

## 🛠️ Stack Técnico
* **Lenguaje:** Python 3.x
* **Librerías de Google:** `google-api-python-client`, `google-auth-oauthlib`.
* **Patrones de Diseño:** Strategy Pattern, Interface-based Programming.

---

## 🚀 1. Instalación y Configuración

 **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/Prince-CRV/YouTube-API-Handler-by-Prince-CRV.git](https://github.com/Prince-CRV/YouTube-API-Handler-by-Prince-CRV.git)
   cd YouTube-API-Handler-by-Prince-CRV
   ```

## 🔐 2. Configurar Credenciales

* ### 📥 Descargar credenciales de Google
Descarga tu archivo **`client_secrets.json`** desde la **Google Cloud Console**, asegurándote de que la **YouTube Data API v3** esté habilitada para tu proyecto.


* ### 🛠️ Crear archivo de configuración
Crea un archivo **`config.json`** en la raíz del proyecto con la siguiente estructura:

```json
{
  "MIS_SCOPES": ["https://www.googleapis.com/auth/youtube.force-ssl"],
  "RUTA_SECRET": "tu_archivo_secrets.json",
  "PLAYLIST_ID": "ID_DE_TU_PLAYLIST",
  "DESC": "Tu descripción predeterminada"
}
```

## 📂 3. Estructura del Proyecto

```plaintext
├── main_SOLID.py        # Motor principal y lógica de tareas
├── config.json          # Configuración privada (Scopes, IDs, Descripciones)
├── token.pickle         # Sesión de autenticación generada (Ignorado en Git)
├── client_secrets.json  # Credenciales de Google Cloud (Ignorado en Git)
└── README.md            # Documentación del proyecto
```

## 🔧 4. Uso y Extensibilidad

El motor principal (**`YouTubeAutomator`**) ejecuta cualquier objeto que herede de la clase base **`YouTubeTask`**.  
Esto garantiza un flujo de ejecución uniforme, independientemente de la complejidad de la tarea.


## ➕ 5. Cómo añadir una nueva funcionalidad

Basta con crear una clase que herede de la interfaz `YouTubeTask` y pasarla al bot:

```python
class MiTareaPersonalizada(YouTubeTask):
    def execute(self, api: YouTubeAPI):
        # Tu lógica usando api.service
        print("Ejecutando nueva automatización...")

# Ejecución
bot.run(MiTareaPersonalizada())
```
---

## ⚖️ Licencia

Este proyecto está bajo la **Licencia MIT**.  
Siéntete libre de usarlo, modificarlo y distribuirlo para tus propios canales.



## 👤 Autor

**Prince-CRV**  
*Desarrollo y Arquitectura*


