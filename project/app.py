import re
import os
import json
import yt_dlp
import shutil
import zipfile
import requests
import subprocess
import time
import threading
from tqdm import tqdm
from io import BytesIO
from flask import Flask, render_template, request, send_file, jsonify, Response

app = Flask(__name__)

# Configurações do ambiente (suporte a variáveis de ambiente para hospedagem)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER', os.path.join(BASE_DIR, "downloads"))
FFMPEG_FOLDER = os.environ.get('FFMPEG_FOLDER', os.path.join(BASE_DIR, "ffmpeg"))
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(FFMPEG_FOLDER, exist_ok=True)

# Detecta o sistema operacional
IS_WINDOWS = os.name == 'nt'

# URLs e executáveis dependendo do sistema operacional
if IS_WINDOWS:
    FFMPEG_DOWNLOAD_URL = os.environ.get('FFMPEG_DOWNLOAD_URL', "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip")
    FFMPEG_EXECUTABLE = os.path.join(FFMPEG_FOLDER, "bin", "ffmpeg.exe")
else:
    # Para Linux (Render), usa um binário diferente
    FFMPEG_DOWNLOAD_URL = os.environ.get('FFMPEG_DOWNLOAD_URL', "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz")
    FFMPEG_EXECUTABLE = os.path.join(FFMPEG_FOLDER, "bin", "ffmpeg")

MAX_STORAGE_MB = int(os.environ.get('MAX_STORAGE_MB', '500'))  # Limitado a 500MB para hospedagem no Render

MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
RETRY_DELAY = int(os.environ.get('RETRY_DELAY', '2'))
HTTP_TIMEOUT = int(os.environ.get('HTTP_TIMEOUT', '60'))
CLEANUP_THRESHOLD = int(os.environ.get('CLEANUP_THRESHOLD', '400'))  # Inicia limpeza quando o uso de disco atingir 400MB
CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', '1800'))  # Limpeza a cada 30 minutos

# Variável para controlar o agendamento da limpeza
cleanup_thread = None
cleanup_running = False

def run_scheduled_cleanup():
    """Executa limpeza periódica de arquivos antigos"""
    global cleanup_running
    
    if cleanup_running:
        return
        
    cleanup_running = True
    
    try:
        while True:
            print(f"Executando limpeza agendada a cada {CLEANUP_INTERVAL} segundos")
            cleanup_downloads()
            time.sleep(CLEANUP_INTERVAL)
    except Exception as e:
        print(f"Erro na limpeza agendada: {e}")
    finally:
        cleanup_running = False

def start_cleanup_scheduler():
    """Inicia o agendador de limpeza em uma thread separada"""
    global cleanup_thread
    
    if cleanup_thread is None or not cleanup_thread.is_alive():
        cleanup_thread = threading.Thread(target=run_scheduled_cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        print("Agendador de limpeza iniciado")

def cleanup_downloads():
    if not os.path.exists(DOWNLOAD_FOLDER):
        return
        
    try:
        total_size = 0
        files_by_time = []
        
        for file in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, file)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                total_size += file_size
                files_by_time.append((file_path, os.path.getmtime(file_path)))
            elif os.path.isdir(file_path):
                # Processa também diretórios (para playlists)
                for root, _, files in os.walk(file_path):
                    for sub_file in files:
                        sub_file_path = os.path.join(root, sub_file)
                        file_size = os.path.getsize(sub_file_path) / (1024 * 1024)
                        total_size += file_size
                        files_by_time.append((sub_file_path, os.path.getmtime(sub_file_path)))
                    
        print(f"Uso atual de armazenamento: {total_size:.2f}MB / {MAX_STORAGE_MB}MB")
        
        if total_size > CLEANUP_THRESHOLD and files_by_time:
            print(f"Iniciando limpeza. Uso atual: {total_size:.2f}MB, limite: {MAX_STORAGE_MB}MB")
            files_by_time.sort(key=lambda x: x[1])
            
            for file_path, _ in files_by_time:
                if total_size <= MAX_STORAGE_MB * 0.7:  # Reduz para 70% para ter mais margem
                    break
                    
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                os.remove(file_path)
                total_size -= file_size
                print(f"Arquivo removido para liberar espaço: {file_path}")
    except Exception as e:
        print(f"Erro ao limpar downloads: {e}")

def check_storage_space(required_mb=0):
    """Verifica se há espaço suficiente e limpa se necessário."""
    try:
        total_size = 0
        for root, _, files in os.walk(DOWNLOAD_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path) / (1024 * 1024)
        
        available = MAX_STORAGE_MB - total_size
        if available < required_mb or total_size > CLEANUP_THRESHOLD:
            cleanup_downloads()
            
        # Recalcula após limpeza
        total_size = 0
        for root, _, files in os.walk(DOWNLOAD_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path) / (1024 * 1024)
                
        available = MAX_STORAGE_MB - total_size
        return available >= required_mb
    except Exception as e:
        print(f"Erro ao verificar espaço disponível: {e}")
        return True  # Em caso de erro, assume que há espaço

def download_ffmpeg():
    if os.path.exists(FFMPEG_EXECUTABLE):
        print("FFmpeg já está instalado localmente.")
        return True
    
    try:
        print(f"Baixando FFmpeg de {FFMPEG_DOWNLOAD_URL}...")
        
        if os.path.exists(FFMPEG_FOLDER):
            try:
                for file in os.listdir(FFMPEG_FOLDER):
                    file_path = os.path.join(FFMPEG_FOLDER, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
            except Exception as e:
                print(f"Erro ao limpar pasta: {e}")
        
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        
        response = session.get(FFMPEG_DOWNLOAD_URL, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        buffer = BytesIO()
        
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Baixando FFmpeg") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)
                    pbar.update(len(chunk))
        
        buffer.seek(0)
        
        if buffer.getbuffer().nbytes < 1000000:
            print("Download incompleto. Arquivo muito pequeno.")
            return False
        
        print("Extraindo FFmpeg...")
        temp_extract = os.path.join(FFMPEG_FOLDER, "temp_extract")
        os.makedirs(temp_extract, exist_ok=True)
        
        try:
            # Extração depende do formato do arquivo (zip para Windows, tar.xz para Linux)
            if IS_WINDOWS:
                with zipfile.ZipFile(buffer) as zip_ref:
                    zip_ref.extractall(temp_extract)
            else:
                import tarfile
                import lzma
                
                # Para arquivos tar.xz no Linux
                with lzma.open(buffer) as xz:
                    with tarfile.open(fileobj=xz, mode='r:') as tar:
                        tar.extractall(path=temp_extract)
            
            extracted_folders = [f for f in os.listdir(temp_extract) if os.path.isdir(os.path.join(temp_extract, f))]
            
            if not extracted_folders:
                print("Nenhuma pasta encontrada no arquivo extraído.")
                return False
            
            root_folder = next((folder for folder in extracted_folders if "ffmpeg" in folder.lower()), extracted_folders[0])
            src_path = os.path.join(temp_extract, root_folder)
            
            bin_folder = None
            for root, dirs, files in os.walk(src_path):
                executable_name = "ffmpeg.exe" if IS_WINDOWS else "ffmpeg"
                if executable_name in files:
                    bin_folder = root
                    break
            
            if not bin_folder:
                print("FFmpeg executável não encontrado no arquivo baixado")
                return False
            
            bin_dest = os.path.join(FFMPEG_FOLDER, "bin")
            os.makedirs(bin_dest, exist_ok=True)
            
            if IS_WINDOWS:
                executables = ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]
            else:
                executables = ["ffmpeg", "ffprobe", "ffplay"]
                
            for exe in executables:
                if exe in os.listdir(bin_folder):
                    src_exe = os.path.join(bin_folder, exe)
                    dst_exe = os.path.join(bin_dest, exe)
                    shutil.copy2(src_exe, dst_exe)
                    # No Linux, precisamos tornar os arquivos executáveis
                    if not IS_WINDOWS:
                        os.chmod(dst_exe, 0o755)
            
            shutil.rmtree(temp_extract)
            
            if os.path.exists(FFMPEG_EXECUTABLE):
                print(f"FFmpeg instalado com sucesso em {FFMPEG_EXECUTABLE}")
                return True
            else:
                print("FFmpeg não encontrado após instalação")
                return False
            
        except zipfile.BadZipFile:
            print("Arquivo ZIP inválido ou corrompido")
            return False
        except Exception as e:
            print(f"Erro ao extrair FFmpeg: {str(e)}")
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar FFmpeg: {str(e)}")
        return False
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return False

def is_ffmpeg_installed():
    print("Verificando se FFmpeg está instalado...")
    if os.path.exists(FFMPEG_EXECUTABLE):
        try:
            print(f"FFmpeg encontrado em: {FFMPEG_EXECUTABLE}, testando...")
            result = subprocess.run(
                [FFMPEG_EXECUTABLE, "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                timeout=5
            )
            if result.returncode == 0:
                print(f"FFmpeg local encontrado e funcionando em {FFMPEG_EXECUTABLE}")
                return True
            else:
                print(f"FFmpeg local encontrado mas retornou código {result.returncode}")
                print(f"Stderr: {result.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"FFmpeg local encontrado mas com erro: {type(e).__name__}: {e}")
    else:
        print(f"FFmpeg não encontrado em {FFMPEG_EXECUTABLE}")
    
    try:
        print("Tentando encontrar FFmpeg no sistema...")
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode == 0:
            print("FFmpeg encontrado no sistema")
            return True
        else:
            print(f"FFmpeg não encontrado no sistema (código {result.returncode})")
            print(f"Stderr: {result.stderr.decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"FFmpeg não encontrado no sistema: {type(e).__name__}: {e}")
    
    print("FFmpeg não encontrado em nenhum lugar")
    return False

def get_ffmpeg_path():
    if os.path.exists(FFMPEG_EXECUTABLE):
        return FFMPEG_EXECUTABLE
    return 'ffmpeg'

def sanitize_filename(title):
    if not title:
        return f"video_{int(time.time())}"
    
    # Remove caracteres inválidos para nomes de arquivo
    cleaned_title = re.sub(r'[\\/*?:"<>|\'.,!]', "", title)
    # Substitui espaços por underscore
    cleaned_title = cleaned_title.replace(" ", "_")
    # Remove pontos duplicados
    cleaned_title = re.sub(r'\.{2,}', '.', cleaned_title)
    # Remove caracteres no início e fim
    cleaned_title = cleaned_title.strip('.')
    
    # Limita o tamanho do nome para evitar problemas de caminho longo
    if len(cleaned_title) > 50:
        cleaned_title = cleaned_title[:47] + "..."
        
    # Se o nome ficou vazio após a limpeza, usa um nome genérico
    if not cleaned_title:
        cleaned_title = f"video_{int(time.time())}"
        
    return cleaned_title

def format_file_size(size_bytes):
    if size_bytes is None or size_bytes == 0:
        return "Desconhecido"
    
    size_kb = size_bytes / 1024
    if size_kb < 1000:
        return f"{size_kb:.1f} KB"
    
    size_mb = size_kb / 1024
    if size_mb < 1000:
        return f"{size_mb:.1f} MB"
    
    size_gb = size_mb / 1024
    return f"{size_gb:.2f} GB"

def with_retry(func, *args, max_retries=MAX_RETRIES, retry_delay=RETRY_DELAY, **kwargs):
    last_error = None
    
    print(f"Iniciando com_retry para função {func.__name__}, máx tentativas: {max_retries}")
    for attempt in range(max_retries):
        try:
            print(f"Tentativa {attempt+1}/{max_retries} para {func.__name__}")
            result = func(*args, **kwargs)
            print(f"Tentativa {attempt+1}/{max_retries} para {func.__name__} bem-sucedida")
            return result
        except Exception as e:
            last_error = e
            print(f"Tentativa {attempt+1}/{max_retries} falhou: {type(e).__name__}: {str(e)}")
            
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)
                print(f"Aguardando {wait_time}s antes da próxima tentativa...")
                time.sleep(wait_time)
    
    print(f"Todas as {max_retries} tentativas para {func.__name__} falharam. Último erro: {type(last_error).__name__}: {str(last_error)}")
    raise last_error

@app.route('/')
def homepage():
    cleanup_downloads()
    
    if not is_ffmpeg_installed():
        download_ffmpeg()
    
    ffmpeg_available = is_ffmpeg_installed()
    return render_template('homepage.html', ffmpeg_available=ffmpeg_available)

@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    url = request.form.get("url")
    
    if not url:
        return jsonify({"error": "URL inválida!"}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'skip_download': True,
            'socket_timeout': HTTP_TIMEOUT,
            'retries': MAX_RETRIES,
            'fragment_retries': MAX_RETRIES,
        }
        
        def extract_video_info(url, options):
            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(url, download=False)
        
        info = with_retry(extract_video_info, url, ydl_opts)
        
        if 'entries' in info:
            return jsonify({
                "is_playlist": True,
                "title": info.get('title', 'Playlist'),
                "video_count": len(info['entries']),
                "playlist_id": info.get('id', ''),
                "ffmpeg_available": is_ffmpeg_installed()
            })
        
        formats = []
        ffmpeg_available = is_ffmpeg_installed()
        
        progressive_formats = []
        for f in info['formats']:
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                height = f.get('height', 0) or 0
                if height > 0:
                    progressive_formats.append({
                        'format_id': f['format_id'],
                        'ext': f['ext'],
                        'resolution': f'{height}p',
                        'filesize': f.get('filesize', 0),
                        'filesize_formatted': format_file_size(f.get('filesize', 0)),
                        'fps': f.get('fps', 0),
                        'is_progressive': True
                    })
        
        video_only_formats = []
        if ffmpeg_available:
            best_audio = None
            for f in info['formats']:
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    current_tbr = f.get('tbr', 0) or 0
                    best_tbr = best_audio.get('tbr', 0) or 0 if best_audio else 0
                    
                    if best_audio is None or current_tbr > best_tbr:
                        best_audio = f
            
            if best_audio:
                for f in info['formats']:
                    if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                        height = f.get('height', 0) or 0
                        if height > 0:
                            format_id = f"{f['format_id']}+{best_audio['format_id']}"
                            video_size = f.get('filesize', 0) or 0
                            audio_size = best_audio.get('filesize', 0) or 0
                            total_size = video_size + audio_size
                            
                            video_only_formats.append({
                                'format_id': format_id,
                                'ext': 'mp4',
                                'resolution': f'{height}p',
                                'filesize': total_size,
                                'filesize_formatted': format_file_size(total_size),
                                'fps': f.get('fps', 0),
                                'is_progressive': False
                            })
        
        formats = progressive_formats + video_only_formats
        formats.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)
        
        unique_formats = {}
        for fmt in formats:
            resolution = fmt['resolution']
            if resolution not in unique_formats or (not unique_formats[resolution]['is_progressive'] and fmt['is_progressive']):
                unique_formats[resolution] = fmt
        
        formats = list(unique_formats.values())
        formats.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)
        
        resolutions = {}
        resolutions_info = {}
        for fmt in formats:
            resolution = fmt['resolution']
            resolutions[resolution] = fmt['format_id']
            resolutions_info[resolution] = {
                'format_id': fmt['format_id'],
                'filesize': fmt['filesize_formatted'],
                'fps': fmt.get('fps', 0),
                'requires_ffmpeg': not fmt.get('is_progressive', True)
            }
        
        return jsonify({
            "title": info['title'],
            "thumbnail": info.get('thumbnail', ''),
            "duration": info.get('duration', 0),
            "uploader": info.get('uploader', ''),
            "view_count": info.get('view_count', 0),
            "resolutions": resolutions,
            "resolutions_info": resolutions_info,
            "is_playlist": False,
            "ffmpeg_available": ffmpeg_available
        })
    
    except Exception as e:
        print(f"Erro ao obter info do vídeo: {str(e)}")
        return jsonify({
            "error": str(e),
            "message": "Falha ao obter informações do vídeo. Por favor, verifique sua conexão e tente novamente."
        }), 500

@app.route('/download', methods=['POST'])
def download_video():
    cleanup_downloads()
    
    url = request.form.get("url")
    format_id = request.form.get("itag")
    
    if not url or not format_id:
        return "Parâmetros inválidos!", 400

    try:
        if "+" in format_id and not is_ffmpeg_installed():
            if not download_ffmpeg():
                return "Este formato requer FFmpeg para mesclar áudio e vídeo. Por favor, escolha uma resolução mais baixa.", 400

        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Sanitiza o título do vídeo para usar como nome de arquivo
            original_title = info.get('title', 'video')
            title = sanitize_filename(original_title)
            print(f"Título original: {original_title}")
            print(f"Título sanitizado: {title}")
            
            # Garante que o diretório de downloads existe
            os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
            
            # Cria um nome de arquivo mais simples para evitar problemas
            unique_id = str(int(time.time()))
            safe_filename = f"video_{unique_id}"
            output_path = os.path.join(DOWNLOAD_FOLDER, f"{safe_filename}.mp4")
            print(f"Caminho de saída: {output_path}")
            
            # Configurações simplificadas para o youtube-dl
            ydl_opts = {
                'format': format_id,
                'outtmpl': output_path,
                'quiet': False,
                'verbose': True,
                'no_warnings': False,
                'nocheckcertificate': True,
                'socket_timeout': HTTP_TIMEOUT,
                'retries': MAX_RETRIES,
                'fragment_retries': MAX_RETRIES,
                'nooverwrites': False,
                'ignoreerrors': True,
                'noprogress': False,
                'postprocessors': [],
                'progress_hooks': [],
                'ignorecertificate': True,
                'socket_timeout': 60
            }
            
            # Tenta usar FFmpeg do sistema em vez de procurar localmente
            try:
                result = subprocess.run(
                    ["ffmpeg", "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                if result.returncode == 0:
                    print("FFmpeg encontrado no sistema, usando caminho padrão")
                else:
                    # Tenta usar o caminho local
                    if os.path.exists(FFMPEG_EXECUTABLE):
                        print(f"Usando FFmpeg em: {FFMPEG_EXECUTABLE}")
                        ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_EXECUTABLE)
                    else:
                        print("FFmpeg não encontrado, usando formato simples")
                        ydl_opts['format'] = 'best'
            except Exception as e:
                print(f"Erro ao verificar FFmpeg: {e}, usando formato simples")
                ydl_opts['format'] = 'best'
            
            def download_with_retry(url, options):
                try:
                    print(f"Tentando baixar: {url}")
                    print(f"Opções de download: {options}")
                    
                    with yt_dlp.YoutubeDL(options) as ydl:
                        ydl.download([url])
                    
                    print(f"Download concluído! Verificando arquivo: {output_path}")
                    if os.path.exists(output_path):
                        file_size = os.path.getsize(output_path) / (1024 * 1024)
                        print(f"Arquivo criado com sucesso! Tamanho: {file_size:.2f} MB")
                    return True
                    
                except Exception as e:
                    print(f"Erro detalhado no download: {type(e).__name__}: {str(e)}")
                    if isinstance(e, yt_dlp.utils.DownloadError):
                        print("Erro de download do yt-dlp. Tentando formato alternativo...")
                        options['format'] = 'best'  # Tenta o melhor formato disponível
                        with yt_dlp.YoutubeDL(options) as ydl:
                            ydl.download([url])
                        return True
                    raise e
                
            with_retry(download_with_retry, url, ydl_opts)
            
            if os.path.exists(output_path):
                print(f"Arquivo baixado com sucesso: {output_path}")
                file_size = os.path.getsize(output_path)
                
                # Retorna apenas o ID do arquivo para o frontend fazer o download direto
                return jsonify({
                    "success": True,
                    "file_id": unique_id,
                    "title": title,
                    "size": file_size
                })
            else:
                print(f"ERRO: Arquivo não encontrado após download: {output_path}")
                return jsonify({
                    "success": False,
                    "error": "Arquivo não foi criado"
                }), 500

    except Exception as e:
        print(f"Erro ao baixar vídeo: {type(e).__name__}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/get_file/<file_id>', methods=['GET'])
def get_file(file_id):
    try:
        # Sanitiza o file_id para evitar ataque de traversal
        safe_id = re.sub(r'[^0-9]', '', file_id)
        if not safe_id:
            return "ID de arquivo inválido", 400
            
        file_path = os.path.join(DOWNLOAD_FOLDER, f"video_{safe_id}.mp4")
        
        if not os.path.exists(file_path):
            return "Arquivo não encontrado", 404
            
        file_size = os.path.getsize(file_path)
        title = request.args.get('title', f'video_{safe_id}')
        
        # Enviar o arquivo com o método mais simples e com os cabeçalhos adequados
        response = send_file(
            file_path, 
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f"{title}.mp4"
        )
        
        # Adiciona cabeçalhos essenciais
        response.headers['Content-Length'] = str(file_size)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        print(f"Erro ao enviar arquivo: {type(e).__name__}: {str(e)}")
        return f"Erro ao enviar o arquivo: {str(e)}", 500

@app.route('/download_playlist', methods=['POST'])
def download_playlist():
    cleanup_downloads()
    
    url = request.form.get("url")
    quality = request.form.get("quality", "best")
    
    if not url:
        return "URL inválida!", 400

    if int(quality) > 720 and not is_ffmpeg_installed():
        if not download_ffmpeg():
            return "Qualidades acima de 720p requerem FFmpeg. Por favor, escolha uma qualidade menor.", 400

    try:
        # Verifica se há espaço suficiente para uma playlist
        # Playlists podem ser grandes, então verifica se há pelo menos 100MB disponíveis
        if not check_storage_space(100):
            return "Espaço de armazenamento insuficiente para baixar a playlist. Por favor, tente novamente mais tarde.", 507

        # Limita o número de vídeos da playlist para poupar espaço
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'playlist/%(playlist_title)s/%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'nooverwrites': True,
            'socket_timeout': HTTP_TIMEOUT,
            'retries': MAX_RETRIES,
            'fragment_retries': MAX_RETRIES,
            'playlistend': 10  # Limita a 10 vídeos por playlist para economizar espaço
        }
        
        if os.path.exists(FFMPEG_EXECUTABLE):
            ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_EXECUTABLE)
        elif not is_ffmpeg_installed():
            ydl_opts['format'] = f'best[height<={quality}]'
        
        def download_playlist_with_retry(url, options):
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
            return True
            
        with_retry(download_playlist_with_retry, url, ydl_opts)
            
        return "Playlist baixada com sucesso!", 200

    except Exception as e:
        print(f"Erro ao baixar playlist: {str(e)}")
        return f"Erro ao baixar a playlist: {str(e)}", 500

@app.route('/install-instructions', methods=['GET'])
def install_instructions():
    return render_template('install_ffmpeg.html')

@app.route('/check-ffmpeg', methods=['GET'])
def check_ffmpeg():
    if is_ffmpeg_installed():
        return jsonify({"status": "available", "message": "FFmpeg está instalado e pronto para uso."})
    
    success = download_ffmpeg()
    if success:
        return jsonify({"status": "installed", "message": "FFmpeg foi baixado e configurado com sucesso!"})
    else:
        return jsonify({"status": "failed", "message": "Falha ao baixar o FFmpeg automaticamente."})

if __name__ == '__main__':
    if not is_ffmpeg_installed():
        print("FFmpeg não encontrado. Tentando baixar automaticamente...")
        if download_ffmpeg():
            print("FFmpeg instalado com sucesso!")
        else:
            print("Não foi possível baixar o FFmpeg automaticamente. As resoluções altas não estarão disponíveis.")
    
    ffmpeg_status = "disponível" if is_ffmpeg_installed() else "não encontrado"
    print(f"Status do FFmpeg: {ffmpeg_status}")
    
    # Inicia o agendador de limpeza automaticamente
    start_cleanup_scheduler()
    
    # Configuração para ambiente de desenvolvimento ou produção (Render)
    is_prod = os.environ.get('RENDER', False)
    port = int(os.environ.get('PORT', 5000))
    
    if is_prod:
        # Em produção (Render), não usar o modo debug
        print(f"Iniciando servidor em modo produção na porta {port}")
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    else:
        # Em desenvolvimento, usar o modo debug
        print("Iniciando servidor em modo desenvolvimento")
        app.run(debug=True, threaded=True)
