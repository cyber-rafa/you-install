import re
import os
import json
import yt_dlp
import shutil
import zipfile
import requests
import subprocess
import time  # Para pausas entre tentativas
from tqdm import tqdm
from io import BytesIO
from flask import Flask, render_template, request, send_file, jsonify, Response

# Inicialização da aplicação Flask
app = Flask(__name__)

# ===== CONFIGURAÇÕES GLOBAIS =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")
FFMPEG_FOLDER = os.path.join(BASE_DIR, "ffmpeg")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(FFMPEG_FOLDER, exist_ok=True)

# Configurações para Windows
FFMPEG_DOWNLOAD_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
FFMPEG_EXECUTABLE = os.path.join(FFMPEG_FOLDER, "bin", "ffmpeg.exe")
MAX_STORAGE_MB = 1000  # 1GB para uso local

# Configurações para requisições
MAX_RETRIES = 3        # Número máximo de tentativas
RETRY_DELAY = 2        # Segundos entre tentativas
HTTP_TIMEOUT = 60      # Timeout mais generoso para requisições HTTP

# ===== FUNÇÕES DE GERENCIAMENTO DE ARMAZENAMENTO =====
def cleanup_downloads():
    """
    Limpa downloads antigos para manter o uso de armazenamento abaixo do limite.
    Remove arquivos mais antigos primeiro, até atingir 80% do limite.
    """
    if not os.path.exists(DOWNLOAD_FOLDER):
        return
        
    try:
        # Coletar informações de tamanho e data de modificação
        total_size = 0
        files_by_time = []
        
        for file in os.listdir(DOWNLOAD_FOLDER):
            file_path = os.path.join(DOWNLOAD_FOLDER, file)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                total_size += file_size
                files_by_time.append((file_path, os.path.getmtime(file_path)))
        
        # Remover arquivos se espaço usado exceder o limite
        if total_size > MAX_STORAGE_MB and files_by_time:
            files_by_time.sort(key=lambda x: x[1])  # Ordenar por data (mais antigos primeiro)
            
            for file_path, _ in files_by_time:
                if total_size <= MAX_STORAGE_MB * 0.8:  # Parar quando atingir 80% do limite
                    break
                    
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                os.remove(file_path)
                total_size -= file_size
                print(f"Arquivo removido para liberar espaço: {file_path}")
    except Exception as e:
        print(f"Erro ao limpar downloads: {e}")

# ===== FUNÇÕES DE GESTÃO DO FFMPEG =====
def download_ffmpeg():
    """
    Baixa e configura o FFmpeg automaticamente.
    Retorna True se bem-sucedido, False caso contrário.
    """
    # Verificar se já está instalado localmente
    if os.path.exists(FFMPEG_EXECUTABLE):
        print("FFmpeg já está instalado localmente.")
        return True
    
    try:
        print(f"Baixando FFmpeg de {FFMPEG_DOWNLOAD_URL}...")
        
        # Limpar diretório para instalação limpa
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
        
        # Configurar sessão de download com retentativas
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        
        # Baixar arquivo
        response = session.get(FFMPEG_DOWNLOAD_URL, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        buffer = BytesIO()
        
        # Download com barra de progresso
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Baixando FFmpeg") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)
                    pbar.update(len(chunk))
        
        buffer.seek(0)
        
        # Verificar integridade do download
        if buffer.getbuffer().nbytes < 1000000:  # < 1MB provavelmente é erro
            print("Download incompleto. Arquivo muito pequeno.")
            return False
        
        # Extrair arquivo
        print("Extraindo FFmpeg...")
        temp_extract = os.path.join(FFMPEG_FOLDER, "temp_extract")
        os.makedirs(temp_extract, exist_ok=True)
        
        try:
            with zipfile.ZipFile(buffer) as zip_ref:
                zip_ref.extractall(temp_extract)
            
            # Localizar pasta principal da extração
            extracted_folders = [f for f in os.listdir(temp_extract) if os.path.isdir(os.path.join(temp_extract, f))]
            
            if not extracted_folders:
                print("Nenhuma pasta encontrada no arquivo extraído.")
                return False
            
            # Buscar pasta que contenha "ffmpeg" no nome, ou usar a primeira
            root_folder = next((folder for folder in extracted_folders if "ffmpeg" in folder.lower()), extracted_folders[0])
            src_path = os.path.join(temp_extract, root_folder)
            
            # Localizar executáveis
            bin_folder = None
            for root, dirs, files in os.walk(src_path):
                if "ffmpeg.exe" in files:
                    bin_folder = root
                    break
            
            if not bin_folder:
                print("FFmpeg executável não encontrado no arquivo baixado")
                return False
            
            # Copiar executáveis para destino final
            bin_dest = os.path.join(FFMPEG_FOLDER, "bin")
            os.makedirs(bin_dest, exist_ok=True)
            
            executables = ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]
            for exe in executables:
                if exe in os.listdir(bin_folder):
                    src_exe = os.path.join(bin_folder, exe)
                    dst_exe = os.path.join(bin_dest, exe)
                    shutil.copy2(src_exe, dst_exe)
            
            # Limpar arquivos temporários
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
    """
    Verifica se o FFmpeg está disponível no sistema ou localmente.
    Retorna True se encontrado e funcional, False caso contrário.
    """
    # Verificar instalação local
    if os.path.exists(FFMPEG_EXECUTABLE):
        try:
            result = subprocess.run(
                [FFMPEG_EXECUTABLE, "-version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                timeout=5
            )
            if result.returncode == 0:
                print(f"FFmpeg local encontrado e funcionando em {FFMPEG_EXECUTABLE}")
                return True
        except Exception as e:
            print(f"FFmpeg local encontrado mas com erro: {e}")
    
    # Verificar instalação no sistema
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode == 0:
            print("FFmpeg encontrado no sistema")
            return True
    except Exception as e:
        print(f"FFmpeg não encontrado no sistema: {e}")
    
    return False

def get_ffmpeg_path():
    """Retorna o caminho para o executável do FFmpeg"""
    if os.path.exists(FFMPEG_EXECUTABLE):
        return FFMPEG_EXECUTABLE
    return 'ffmpeg'  # Usar o FFmpeg do sistema, se disponível

# ===== FUNÇÕES DE UTILIDADE =====
def sanitize_filename(title):
    """Remove caracteres inválidos do nome do arquivo"""
    cleaned_title = re.sub(r'[\\/*?:"<>|\'.,!]', "", title)
    cleaned_title = cleaned_title.replace(" ", "_")
    cleaned_title = re.sub(r'\.{2,}', '.', cleaned_title)
    return cleaned_title.strip('.')

def format_file_size(size_bytes):
    """
    Formata o tamanho do arquivo de bytes para uma unidade legível (KB, MB, GB).
    Retorna string formatada.
    """
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
    """
    Executa uma função com sistema de retry automático.
    Útil para operações que podem falhar temporariamente como requisições HTTP.
    
    Args:
        func: A função a ser executada
        *args: Argumentos posicionais para a função
        max_retries: Número máximo de tentativas (padrão: definido na configuração global)
        retry_delay: Tempo de espera entre tentativas em segundos
        **kwargs: Argumentos nomeados para a função
        
    Returns:
        O resultado da função ou levanta a última exceção após todas as tentativas
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            print(f"Tentativa {attempt+1}/{max_retries} falhou: {str(e)}")
            
            if attempt < max_retries - 1:
                # Espera progressiva entre tentativas (aumenta o tempo a cada falha)
                wait_time = retry_delay * (attempt + 1)
                print(f"Aguardando {wait_time}s antes da próxima tentativa...")
                time.sleep(wait_time)
    
    # Se chegou aqui, todas as tentativas falharam
    raise last_error

# ===== ROTAS DA APLICAÇÃO =====
@app.route('/')
def homepage():
    """Página inicial da aplicação"""
    # Garantir espaço disponível
    cleanup_downloads()
    
    # Verificar disponibilidade do FFmpeg
    if not is_ffmpeg_installed():
        download_ffmpeg()
    
    ffmpeg_available = is_ffmpeg_installed()
    return render_template('homepage.html', ffmpeg_available=ffmpeg_available)

@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    """
    Obtém informações de um vídeo ou playlist do YouTube.
    Retorna dados como título, miniaturas, formatos disponíveis.
    """
    url = request.form.get("url")
    
    if not url:
        return jsonify({"error": "URL inválida!"}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'skip_download': True,
            'socket_timeout': HTTP_TIMEOUT,     # Usar timeout configurado globalmente
            'retries': MAX_RETRIES,            # Configurar retries na yt-dlp
            'fragment_retries': MAX_RETRIES,   # Configurar retries para fragmentos de vídeo
        }
        
        # Função a ser executada com retry
        def extract_video_info(url, options):
            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(url, download=False)
        
        # Usar sistema de retry para obter informações do vídeo
        info = with_retry(extract_video_info, url, ydl_opts)
        
        # Verificar se é uma playlist
        if 'entries' in info:
            return jsonify({
                "is_playlist": True,
                "title": info.get('title', 'Playlist'),
                "video_count": len(info['entries']),
                "playlist_id": info.get('id', ''),
                "ffmpeg_available": is_ffmpeg_installed()
            })
        
        # Processar vídeo único
        formats = []
        ffmpeg_available = is_ffmpeg_installed()
        
        # Processar formatos progressivos (áudio+vídeo juntos)
        progressive_formats = []
        for f in info['formats']:
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                height = f.get('height', 0)
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
        
        # Processar formatos de alta resolução (se FFmpeg disponível)
        video_only_formats = []
        if ffmpeg_available:
            # Encontrar o melhor formato de áudio
            best_audio = None
            for f in info['formats']:
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    current_tbr = f.get('tbr', 0) or 0
                    best_tbr = best_audio.get('tbr', 0) or 0 if best_audio else 0
                    
                    if best_audio is None or current_tbr > best_tbr:
                        best_audio = f
            
            # Combinar com formatos de vídeo
            if best_audio:
                for f in info['formats']:
                    if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                        height = f.get('height', 0)
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
        
        # Combinar e classificar formatos
        formats = progressive_formats + video_only_formats
        formats.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)
        
        # Remover duplicatas de resolução (priorizar formatos progressivos)
        unique_formats = {}
        for fmt in formats:
            resolution = fmt['resolution']
            if resolution not in unique_formats or (not unique_formats[resolution]['is_progressive'] and fmt['is_progressive']):
                unique_formats[resolution] = fmt
        
        formats = list(unique_formats.values())
        formats.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)
        
        # Formatar para resposta
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
    """
    Baixa um vídeo único do YouTube no formato especificado.
    Retorna o arquivo para download pelo navegador.
    """
    # Limpar downloads antigos para garantir espaço
    cleanup_downloads()
    
    url = request.form.get("url")
    format_id = request.form.get("itag")  # Mantemos "itag" para compatibilidade
    
    if not url or not format_id:
        return "Parâmetros inválidos!", 400

    try:
        # Verificar requisitos de FFmpeg
        if "+" in format_id and not is_ffmpeg_installed():
            if not download_ffmpeg():
                return "Este formato requer FFmpeg para mesclar áudio e vídeo. Por favor, escolha uma resolução mais baixa.", 400

        # Obter informações e configurar download
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = sanitize_filename(info['title'])
            output_path = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp4")
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'noplaylist': True,
                'socket_timeout': HTTP_TIMEOUT,     # Usar timeout configurado globalmente
                'retries': MAX_RETRIES,            # Configurar retries na yt-dlp
                'fragment_retries': MAX_RETRIES,   # Configurar retries para fragmentos de vídeo
                'postprocessors': [{
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }]
            }
            
            # Configurar FFmpeg se disponível
            if os.path.exists(FFMPEG_EXECUTABLE):
                ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_EXECUTABLE)
            
            # Realizar download com retry
            def download_with_retry(url, options):
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download([url])
                return True
                
            with_retry(download_with_retry, url, ydl_opts)
            
            # Entregar arquivo
            if os.path.exists(output_path):
                return send_file(output_path, as_attachment=True, download_name=f"{title}.mp4")
            else:
                return "Erro ao baixar o vídeo. O arquivo não foi criado.", 500

    except Exception as e:
        print(f"Erro ao baixar vídeo: {str(e)}")
        return f"Erro ao baixar o vídeo: {str(e)}", 500

@app.route('/download_playlist', methods=['POST'])
def download_playlist():
    """
    Baixa uma playlist completa do YouTube na qualidade especificada.
    Organiza os vídeos em pastas por playlist.
    """
    # Limpar downloads antigos para garantir espaço
    cleanup_downloads()
    
    url = request.form.get("url")
    quality = request.form.get("quality", "best")
    
    if not url:
        return "URL inválida!", 400

    # Verificar requisitos de FFmpeg para alta qualidade
    if int(quality) > 720 and not is_ffmpeg_installed():
        if not download_ffmpeg():
            return "Qualidades acima de 720p requerem FFmpeg. Por favor, escolha uma qualidade menor.", 400

    try:
        # Configurar download da playlist
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'playlist/%(playlist_title)s/%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'nooverwrites': True,
            'socket_timeout': HTTP_TIMEOUT,     # Usar timeout configurado globalmente
            'retries': MAX_RETRIES,            # Configurar retries na yt-dlp
            'fragment_retries': MAX_RETRIES,   # Configurar retries para fragmentos de vídeo
        }
        
        # Configurar FFmpeg se disponível
        if os.path.exists(FFMPEG_EXECUTABLE):
            ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_EXECUTABLE)
        elif not is_ffmpeg_installed():
            # Usar formato progressivo se FFmpeg não estiver disponível
            ydl_opts['format'] = f'best[height<={quality}]'
        
        # Realizar download com retry
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
    """Página com instruções para instalar o FFmpeg"""
    return render_template('install_ffmpeg.html')

@app.route('/check-ffmpeg', methods=['GET'])
def check_ffmpeg():
    """
    Verifica o status do FFmpeg e tenta instalá-lo se necessário.
    Retorna o status atual em formato JSON.
    """
    if is_ffmpeg_installed():
        return jsonify({"status": "available", "message": "FFmpeg está instalado e pronto para uso."})
    
    # Tentar instalação
    success = download_ffmpeg()
    if success:
        return jsonify({"status": "installed", "message": "FFmpeg foi baixado e configurado com sucesso!"})
    else:
        return jsonify({"status": "failed", "message": "Falha ao baixar o FFmpeg automaticamente."})

# ===== INICIALIZAÇÃO DA APLICAÇÃO =====
if __name__ == '__main__':
    # Verificar FFmpeg na inicialização
    if not is_ffmpeg_installed():
        print("FFmpeg não encontrado. Tentando baixar automaticamente...")
        if download_ffmpeg():
            print("FFmpeg instalado com sucesso!")
        else:
            print("Não foi possível baixar o FFmpeg automaticamente. As resoluções altas não estarão disponíveis.")
    
    ffmpeg_status = "disponível" if is_ffmpeg_installed() else "não encontrado"
    print(f"Status do FFmpeg: {ffmpeg_status}")
    
    # Iniciar servidor na porta 5000 (padrão do Flask)
    app.run(debug=True, threaded=True)  # Usar modo threaded para melhor desempenho com múltiplas requisições
