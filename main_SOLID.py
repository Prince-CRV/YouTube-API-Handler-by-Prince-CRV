import os
import re
import json
import pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from abc import ABC, abstractmethod


# --- 1. CLASE DE AUTENTICACIÓN (Single Responsibility) ---
class YouTubeAuth:
    def __init__(self, secrets_file, scopes):
        self.secrets_file = secrets_file
        self.scopes = scopes
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    def authenticate(self):
        print("🔑 [Auth] Iniciando autenticación...")
        creds = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
                print("📂 [Auth] Sesión recuperada desde token.pickle")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 [Auth] Token expirado, refrescando acceso...")
                creds.refresh(Request())
            else:
                print("🌐 [Auth] Login necesario. Abriendo navegador...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.secrets_file, self.scopes
                )
                creds = flow.run_local_server(
                    host="localhost", port=8080, open_browser=False
                )

            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
                print("💾 [Auth] Nueva sesión guardada.")

        return build("youtube", "v3", credentials=creds)


# --- 2. CLASE DE SERVICIOS API (Interface para YouTube) ---
class YouTubeAPI:
    def __init__(self, service):
        """
        Clase encargada exclusivamente de la comunicación con la API de YouTube.
        Sigue el principio de Responsabilidad Única (SRP).
        """
        self.service = service

    def get_uploads_playlist_id(self):
        """Obtiene el ID de la lista automática de videos subidos del canal."""
        print("📡 [API] Obteniendo ID de la lista 'Uploads'...")
        res = self.service.channels().list(mine=True, part="contentDetails").execute()
        return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def fetch_videos(self, playlist_id):
        """Lista los videos de una playlist (por defecto trae los últimos 100)."""
        print(f"📡 [API] Listando videos de la playlist: {playlist_id}")
        return (
            self.service.playlistItems()
            .list(playlistId=playlist_id, part="snippet", maxResults=100)
            .execute()
            .get("items", [])
        )

    def get_full_video_data(self, video_id):
        """Obtiene todos los detalles (snippet, status, contentDetails) de un video específico."""
        res = (
            self.service.videos()
            .list(id=video_id, part="status,snippet,contentDetails")
            .execute()
        )
        return res["items"][0] if res["items"] else None

    def update_video_content(self, body):
        """Actualiza metadatos (título, descripción, fecha programación, video relacionado)."""
        print(f"📡 [API] Enviando actualización para video ID: {body['id']}")
        return (
            self.service.videos()
            .update(part="snippet,status,contentDetails", body=body)
            .execute()
        )

    # --- NUEVOS MÉTODOS PARA GESTIÓN DE LISTAS ---

    def fetch_playlist_items(self, playlist_id):
        """
        Obtiene los IDs de los videos que ya están dentro de una playlist específica.
        Útil para evitar duplicados.
        """
        print(f"📡 [API] Verificando videos existentes en playlist {playlist_id}...")
        items = (
            self.service.playlistItems()
            .list(playlistId=playlist_id, part="snippet", maxResults=100)
            .execute()
            .get("items", [])
        )

        # Extraemos solo el videoId del recurso interno
        return [item["snippet"]["resourceId"]["videoId"] for item in items]

    def add_to_playlist(self, video_id, target_playlist_id):
        """Inserta un video en una lista de reproducción."""
        print(f"📡 [API] Insertando video {video_id} en playlist {target_playlist_id}")
        body = {
            "snippet": {
                "playlistId": target_playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        }
        return self.service.playlistItems().insert(part="snippet", body=body).execute()
    

# --- 3. CLASE DE LÓGICA DE CALENDARIO (Business Logic) ---
class CalendarStrategy:
    @staticmethod
    def generate_schedule(quantity):
        print(f"📅 [Calendar] Generando {quantity} espacios de publicación...")
        slots = [
            (0, 7, 30),  # Lunes: 07:30 (Motivación inicio de semana)
            (1, 13, 0),  # Martes: 13:00 (Pico almuerzo)
            (2, 13, 0),  # Miércoles: 13:00 (Pico almuerzo)
            (3, 13, 0),  # Jueves: 13:00 (Pico almuerzo)
            (4, 19, 0),  # Viernes: 19:00 (Desconexión fin de semana)
            (5, 10, 0),  # Sábado: 10:00 (Mañana tranquila)
            (6, 20, 0),  # Domingo: 20:00 (Cierre de día/reflexión)
        ]
        dates = []
        current = datetime.now()
        while len(dates) < quantity:
            day_now = current.weekday()
            for s_day, hr, mnt in slots:
                if day_now == s_day:
                    possible = current.replace(
                        hour=hr, minute=mnt, second=0, microsecond=0
                    )
                    if possible > datetime.now() and len(dates) < quantity:
                        dates.append(possible.strftime("%Y-%m-%dT%H:%M:%SZ"))
            current += timedelta(days=1)
            current = current.replace(hour=0, minute=0)
        print("✅ [Calendar] Fechas listas.")
        return dates


# --- 4 CLAVE DEL OCP: LA INTERFAZ PARA TAREAS ---
class YouTubeTask(ABC):
    """
    Cualquier nueva funcionalidad debe heredar de aquí.
    Esto permite que el Automator ejecute cualquier tarea sin saber qué hace por dentro.
    """

    @abstractmethod
    def execute(self, api: YouTubeAPI):
        pass


# ------------------------------------INICIO DE LAS TAREAS CONCRETAS-------------------------

# --- 4.1 TAREA: PROGRAMACIÓN COMPLETA (Tu lógica original) ---
class FullAutomationTask(YouTubeTask):
    def __init__(self, target_playlist, description):
        self.target_playlist = target_playlist
        self.description = description

    def execute(self, api: YouTubeAPI):
        print("\n🚀 [Task] Iniciando Automatización Completa...")

        # --- REUTILIZACIÓN: Buscamos y ordenamos los videos privados ---
        search_task = ListPrivateVideosTask()
        to_program_data = search_task.execute(api)

        if not to_program_data:
            print("⚠️ No hay videos privados para programar. Abortando.")
            return

        # --- NUEVO: Obtener videos que ya están en la playlist para evitar duplicados ---
        videos_ya_en_playlist = api.fetch_playlist_items(self.target_playlist)

        # 1. Mapear videos principales para referencias
        uploads_id = api.get_uploads_playlist_id()
        all_items = api.fetch_videos(uploads_id)
        ref_map = {}

        for item in all_items:
            title = item["snippet"]["title"].upper()
            v_id = item["snippet"]["resourceId"]["videoId"]
            if "GÉNESIS - CAPÍTULO" in title:
                match = re.search(r"CAPÍTULO\s+(\d+)", title)
                if match:
                    ref_map[match.group(1)] = v_id

        # 2. Obtener fechas estratégicas
        dates = CalendarStrategy.generate_schedule(len(to_program_data))

        # 3. Ejecución final
        for vid_info, publish_date in zip(to_program_data, dates):
            title = vid_info["title"]
            v_id = vid_info["id"]

            print(f"\n⚙️ [Procesando] {title}")

            # Lógica de video relacionado
            match = re.search(r"Capítulo\s+(\d+)", title, re.IGNORECASE)
            related_id = ref_map.get(match.group(1)) if match else None

            # Formatear título (evitar duplicar hashtags si ya existen)
            new_title = title if "#biblia" in title.lower() else f"{title} #biblia"

            body = {
                "id": v_id,
                "snippet": {
                    "title": new_title,
                    "description": self.description,
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": "private",
                    "publishAt": publish_date,
                    "selfDeclaredMadeForKids": False,
                },
            }

            if related_id:
                body["contentDetails"] = {"relatedVideoId": related_id}
                print(f"   🔗 [Relación] Vinculando al capítulo {match.group(1)}")

            try:
                # PASO A: Siempre actualizamos metadatos (título y fecha de programación)
                api.update_video_content(body)
                print(f"   ✔️ Programado para: {publish_date}")

                # PASO B: Añadir a playlist SOLO si no está ya dentro
                if v_id not in videos_ya_en_playlist:
                    api.add_to_playlist(v_id, self.target_playlist)
                    print("   ✅ Añadido a la lista de reproducción.")
                else:
                    print("   ⏭️ El video ya existe en la playlist. Saltando inserción.")

            except Exception:
                print(f"   ❌ [Error] Falló video {v_id}")

        print("\n🏁 [Automator] ¡Proceso completado con éxito!")

# --- 4.2 TAREA: LISTAR VIDEOS PRIVADOS ---
class ListPrivateVideosTask(YouTubeTask):
    def execute(self, api: YouTubeAPI):
        print("\n🔍 [Task] Buscando y organizando videos privados...")

        # 1. Obtener todos los videos
        uploads_id = api.get_uploads_playlist_id()
        items = api.fetch_videos(uploads_id)

        private_videos = []

        # 2. Filtrar
        for item in items:
            v_id = item["snippet"]["resourceId"]["videoId"]
            details = api.get_full_video_data(v_id)

            if details["status"]["privacyStatus"] == "private":
                # Guardamos tupla (Título, ID, DetallesCompletos) por si los necesitamos luego
                private_videos.append(
                    {
                        "title": details["snippet"]["title"],
                        "id": v_id,
                        "details": details,
                    }
                )

        # 3. Ordenar alfabéticamente por título (como pediste)
        private_videos.sort(key=lambda x: x["title"])

        # 4. Mostrar en consola
        for vid in private_videos:
            print(f"   📌 Privado Ordenado: {vid['title']} (ID: {vid['id']})")

        return private_videos  # <--- IMPORTANTE: Retornamos la lista

# --- 4.3 TAREA: TEST DE SHORTS (Investigación) ---
class TestShortsRelatedFieldTask(YouTubeTask):
    def __init__(self, short_id):
        self.short_id = short_id

    def execute(self, api: YouTubeAPI):
        print(f"\n🧪 [Task] Testeando campo 'relatedVideoId' en Short: {self.short_id}")
        try:
            details = api.get_full_video_data(self.short_id)
            # Intentamos ver si existe en contentDetails
            content_details = details.get("contentDetails", {})
            related = content_details.get("relatedVideoId", "NO ENCONTRADO")
            print(f"📊 Resultado: relatedVideoId = {related}")
        except Exception as e:
            print(f"❌ Error en test de Shorts: {e}")

# --- 4.4 TAREA: LIMPIAR PLAYLIST (Investigación) ---
class ClearPlaylistTask(YouTubeTask):
    def __init__(self, playlist_id):
        self.playlist_id = playlist_id

    def execute(self, api: YouTubeAPI):
        print(f"\n🗑️ [ClearTask] Iniciando limpieza de la lista: {self.playlist_id}")

        # 1. Obtener los IDs de los elementos de la lista (no del video, sino del item en la lista)
        items = (
            api.service.playlistItems()
            .list(playlistId=self.playlist_id, part="id", maxResults=100)
            .execute()
            .get("items", [])
        )

        if not items:
            print("✨ La lista ya está vacía.")
            return

        print(f"⚠️ Eliminando {len(items)} elementos...")
        for item in items:
            try:
                api.service.playlistItems().delete(id=item["id"]).execute()
                print(f"   🗑️ Item {item['id']} eliminado.")
            except Exception as e:
                print(f"   ❌ Error al eliminar item: {e}")

        print("✅ Limpieza completada.")

# --- 4.5 TAREA: LISTAR SHORTS PÚBLICOS ---
class AddPublicShortsExtendedTask(YouTubeTask):
    """
    Filtra videos PÚBLICOS con duración < 120 segundos.
    Los organiza de la Z a la A y los añade a la playlist.
    """

    def __init__(self, target_playlist):
        self.target_playlist = target_playlist

    def execute(self, api: YouTubeAPI):
        print(
            f"\n📱 [Task] Filtrando videos públicos (<120s) para: {self.target_playlist}"
        )

        # 1. Obtener duplicados para no repetir videos en la lista
        videos_ya_en_playlist = api.fetch_playlist_items(self.target_playlist)

        # 2. Obtener todos los videos subidos del canal
        uploads_id = api.get_uploads_playlist_id()
        all_items = api.fetch_videos(uploads_id)

        videos_seleccionados = []

        print("   🔍 Analizando metadatos y duración...")

        for item in all_items:
            v_id = item["snippet"]["resourceId"]["videoId"]
            title = item["snippet"]["title"]

            # Consultamos datos completos para ver privacidad y duración
            details = api.get_full_video_data(v_id)

            # Filtro de Privacidad: Solo Públicos
            if details["status"]["privacyStatus"] != "public":
                continue

            # Filtro de Duración: Menos de 120 segundos
            duration_iso = details["contentDetails"].get("duration", "")
            if self._check_duration(duration_iso, max_seconds=120):
                videos_seleccionados.append({"title": title, "id": v_id})

        # 3. Ordenar alfabéticamente INVERSO (Z -> A)
        videos_seleccionados.sort(key=lambda x: x["title"].lower(), reverse=True)

        # 4. Inserción en la Playlist
        print(
            f"   🎯 Se encontraron {len(videos_seleccionados)} videos que cumplen el criterio."
        )

        count = 0
        for vid in videos_seleccionados:
            if vid["id"] not in videos_ya_en_playlist:
                try:
                    api.add_to_playlist(vid["id"], self.target_playlist)
                    print(f"   ✅ Añadido: {vid['title']}")
                    count += 1
                except Exception as e:
                    print(f"   ❌ Error al añadir {vid['title']}: {e}")
            else:
                print(f"   ⏭️ Saltado (ya existe): {vid['title']}")

        print(f"\n🏁 [Task] ¡Completado! {count} videos nuevos añadidos a la lista.")

    def _check_duration(self, duration_str, max_seconds=120):
        """
        Convierte el formato ISO 8601 (PT#M#S) a segundos totales
        y valida si es menor al límite.
        """
        if "H" in duration_str:
            return False  # Si tiene horas, supera los 120s

        minutes = re.search(r"(\d+)M", duration_str)
        seconds = re.search(r"(\d+)S", duration_str)

        total_seconds = 0
        if minutes:
            total_seconds += int(minutes.group(1)) * 60
        if seconds:
            total_seconds += int(seconds.group(1))

        return 0 < total_seconds <= max_seconds

# ------------------------------------FIN DE LAS TAREAS CONCRETAS-------------------------


# --- 5 EL AUTOMATOR (Ahora cumple OCP) ---
class YouTubeAutomator:
    def __init__(self, api_handler: YouTubeAPI):
        self.api = api_handler

    def run(self, task: YouTubeTask):
        """
        Este método está CERRADO a modificaciones.
        No importa qué nueva tarea inventes, este método siempre funciona igual.
        """
        print("\n--- Ejecutando acción en YouTube ---")
        task.execute(self.api)


def cargar_configuracion():
    ruta_config = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(ruta_config, 'r', encoding='utf-8') as f:
        return json.load(f)

# --- INICIO DEL PROGRAMA ---
if __name__ == "__main__":
    # Cargar los datos desde el JSON
    config = cargar_configuracion()
    
    # Acceder a los valores del config.json:
    MIS_SCOPES = config["MIS_SCOPES"]
    RUTA_SECRET = config["RUTA_SECRET"]
    PLAYLIST_ID = config["PLAYLIST_ID"]
    DESC = config["DESC"]

    # 1. Autenticar
    auth = YouTubeAuth(RUTA_SECRET, MIS_SCOPES)
    service_token = auth.authenticate()

    # 2. Inyectar servicio en la API
    api = YouTubeAPI(service_token)

    # 3. Inyectar API en el Bot
    bot = YouTubeAutomator(api)

    # 4. Definir las tareas deseadas
    listar_videos = ListPrivateVideosTask()
    probar_videos_relacionados = TestShortsRelatedFieldTask("zZi381IEpKE")
    limpiar_playlist = ClearPlaylistTask(PLAYLIST_ID)
    añadir_shorts_publicos = AddPublicShortsExtendedTask(PLAYLIST_ID)
    automatizacion_completa = FullAutomationTask(PLAYLIST_ID, DESC)

    # 5. Ejecutar la tarea deseada
    bot.run(listar_videos)
    # bot.run(probar_videos_relacionados)
    # bot.run(limpiar_playlist)
    # bot.run(añadir_shorts_publicos)
    # bot.run(automatizacion_completa)
