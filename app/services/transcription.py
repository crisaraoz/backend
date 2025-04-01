from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from typing import Optional, List

def get_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed_url.path[1:]
    if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
    raise ValueError("Invalid YouTube URL")

async def get_video_transcript(
    video_url: str, 
    language_code: str = "es",  # Por defecto español
    transcription_type: Optional[str] = None,
    use_generated: bool = False
) -> str:
    """Get transcript from YouTube video with language options."""
    try:
        video_id = get_video_id(video_url)
        
        # Intentar obtener la lista de transcripciones disponibles
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Primero intentar con el idioma solicitado
            transcript = None
            try:
                # Intentar obtener la transcripción en el idioma solicitado
                transcript = transcript_list.find_transcript([language_code])
            except Exception as e:
                print(f"No se encontró transcripción en {language_code}, buscando alternativas: {str(e)}")
            
            # Si no hay transcripción en el idioma solicitado, buscar cualquier transcripción auto-generada
            if not transcript:
                available_transcripts = list(transcript_list)
                for t in available_transcripts:
                    if t.is_generated:
                        transcript = t
                        print(f"Usando transcripción auto-generada en {t.language_code}")
                        break
            
            # Si todavía no hay transcripción, usar la primera disponible
            if not transcript and available_transcripts:
                transcript = available_transcripts[0]
                print(f"Usando la primera transcripción disponible en {transcript.language_code}")
            
            # Si no hay ninguna transcripción disponible
            if not transcript:
                raise ValueError(f"No se encontraron transcripciones para el video {video_id}")
            
            # Obtener los datos de la transcripción
            transcript_data = transcript.fetch()
        except Exception as e:
            # Si falla al listar transcripciones, intentar directamente con get_transcript
            print(f"Error al listar transcripciones, intentando con get_transcript: {str(e)}")
            transcript_data = YouTubeTranscriptApi.get_transcript(
                video_id, 
                languages=["en", "es", "auto"],  # Intentar con inglés, español o auto-detectado
            )
        
        # Agrupar segmentos de transcripción para crear frases más largas
        grouped_transcript = []
        current_group = None
        merge_interval = 3.0  # Intervalo máximo en segundos para combinar segmentos
        
        for entry in transcript_data:
            # Acceder a los elementos como diccionario, verificando primero si es un diccionario
            # o si es un objeto con atributos
            if isinstance(entry, dict):
                timestamp = entry.get('start', 0)
                text = entry.get('text', '')
            else:
                # Si es un objeto, intentar acceder directamente a los atributos
                timestamp = getattr(entry, 'start', 0)
                text = getattr(entry, 'text', '')
            
            if not current_group:
                # Iniciar un nuevo grupo
                current_group = {
                    'start': timestamp,
                    'text': text
                }
            elif timestamp - (current_group['start'] + 5.0) <= merge_interval:
                # Si el timestamp está dentro del intervalo de fusión, añadir al grupo actual
                current_group['text'] += ' ' + text
            else:
                # Si el timestamp está fuera del intervalo, guardar el grupo actual y empezar uno nuevo
                grouped_transcript.append(current_group)
                current_group = {
                    'start': timestamp,
                    'text': text
                }
        
        # Añadir el último grupo si existe
        if current_group:
            grouped_transcript.append(current_group)
        
        # Format transcript with timestamps
        formatted_transcript = []
        for entry in grouped_transcript:
            timestamp = int(entry['start'])
            minutes = timestamp // 60
            seconds = timestamp % 60
            text = entry['text'].strip()
            
            # Asegurarse de que el texto comienza con mayúscula
            if text and len(text) > 0:
                text = text[0].upper() + text[1:]
            
            formatted_transcript.append(f"{minutes:02d}:{seconds:02d} {text}")
        
        return "\n".join(formatted_transcript)
    except Exception as e:
        raise ValueError(f"Failed to get transcript: {str(e)}") 