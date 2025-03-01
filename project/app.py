import re
import os
import json
import yt_dlp
import shutil
import zipfile
import requests
import subprocess
from tqdm import tqdm
from io import BytesIO
from flask import Flask, render_template, request, send_file, jsonify, Response

app = Flask(__name__)

# Configurações de pasta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")
FFMPEG_FOLDER = os.path.join(BASE_DIR, "ffmpeg")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(FFMPEG_FOLDER, exist_ok=True)

# URL para baixar o FFmpeg para Windows (versão leve)
FFMPEG_DOWNLOAD_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
FFMPEG_EXECUTABLE = os.path.join(FFMPEG_FOLDER, "bin", "ffmpeg.exe")

def download_ffmpeg():
    """Baixa e extrai o FFmpeg automaticamente"""
    if os.path.exists(FFMPEG_EXECUTABLE):
        print("FFmpeg já está instalado localmente.")
        return True
    
    try:
        print(f"Baixando FFmpeg de {FFMPEG_DOWNLOAD_URL}...")
        
        # Limpar a pasta antes de baixar (caso haja uma instalação parcial)
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
        
        # Configurar sessão com timeout mais longo
        session = requests.Session()
        session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        
        # Baixar com timeout mais longo
        response = session.get(FFMPEG_DOWNLOAD_URL, stream=True, timeout=60)
        response.raise_for_status()
        
        # Obter o tamanho total do arquivo para a barra de progresso
        total_size = int(response.headers.get('content-length', 0))
        
        # Criar um buffer para armazenar o arquivo
        buffer = BytesIO()
        
        # Mostrar o progresso do download
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Baixando FFmpeg") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)
                    pbar.update(len(chunk))
        
        buffer.seek(0)
        
        # Verificar se o download foi completo
        if buffer.getbuffer().nbytes < 1000000:  # Menos de 1MB provavelmente significa erro
            print("Download incompleto. Arquivo muito pequeno.")
            return False
        
        # Criar pasta temporária para extração
        print("Extraindo FFmpeg...")
        temp_extract = os.path.join(FFMPEG_FOLDER, "temp_extract")
        os.makedirs(temp_extract, exist_ok=True)
        
        # Extrair o arquivo ZIP
        try:
            with zipfile.ZipFile(buffer) as zip_ref:
                zip_ref.extractall(temp_extract)
            
            # Identificar a pasta raiz extraída (geralmente contém "ffmpeg" no nome)
            extracted_folders = [f for f in os.listdir(temp_extract) if os.path.isdir(os.path.join(temp_extract, f))]
            
            if not extracted_folders:
                print("Nenhuma pasta encontrada no arquivo extraído.")
                return False
            
            root_folder = None
            for folder in extracted_folders:
                if "ffmpeg" in folder.lower():
                    root_folder = folder
                    break
            
            if not root_folder:
                root_folder = extracted_folders[0]  # Usar a primeira pasta se nenhuma contiver "ffmpeg"
            
            # Mover arquivos para a pasta ffmpeg
            src_path = os.path.join(temp_extract, root_folder)
            
            # Encontrar a pasta bin dentro da extração
            bin_folder = None
            for root, dirs, files in os.walk(src_path):
                if "ffmpeg.exe" in files:
                    bin_folder = root
                    break
            
            if not bin_folder:
                print("FFmpeg executável não encontrado no arquivo baixado")
                return False
            
            # Verificar o caminho para bin_folder relativo a src_path
            rel_path = os.path.relpath(bin_folder, src_path)
            
            # Criar pasta bin no destino final
            bin_dest = os.path.join(FFMPEG_FOLDER, "bin")
            os.makedirs(bin_dest, exist_ok=True)
            
            # Copiar executáveis para pasta bin
            executables = ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]
            for exe in executables:
                if exe in os.listdir(bin_folder):
                    src_exe = os.path.join(bin_folder, exe)
                    dst_exe = os.path.join(bin_dest, exe)
                    shutil.copy2(src_exe, dst_exe)
            
            # Limpar pasta temporária
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
    """Verifica se o FFmpeg está instalado no sistema ou localmente"""
    # Verificar se temos a versão local
    if os.path.exists(FFMPEG_EXECUTABLE):
        try:
            # Testar se o executável é válido
            result = subprocess.run([FFMPEG_EXECUTABLE, "-version"], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   timeout=5)
            if result.returncode == 0:
                print(f"FFmpeg local encontrado e funcionando em {FFMPEG_EXECUTABLE}")
                return True
        except Exception as e:
            print(f"FFmpeg local encontrado mas com erro: {e}")
            # Continua para verificar a versão do sistema
    
    # Verificar se está disponível no sistema
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               timeout=5)
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

def sanitize_filename(title):
    """Remove caracteres inválidos do nome do arquivo"""
    cleaned_title = re.sub(r'[\\/*?:"<>|\'.,!]', "", title)
    cleaned_title = cleaned_title.replace(" ", "_")
    cleaned_title = re.sub(r'\.{2,}', '.', cleaned_title)
    return cleaned_title.strip('.')

def format_file_size(size_bytes):
    """Formata o tamanho do arquivo de bytes para uma unidade legível"""
    if size_bytes is None or size_bytes == 0:
        return "Desconhecido"
    
    # Converte para KB, MB, GB conforme necessário
    size_kb = size_bytes / 1024
    if size_kb < 1000:
        return f"{size_kb:.1f} KB"
    
    size_mb = size_kb / 1024
    if size_mb < 1000:
        return f"{size_mb:.1f} MB"
    
    size_gb = size_mb / 1024
    return f"{size_gb:.2f} GB"

@app.route('/')
def homepage():
    # Tentar baixar o FFmpeg automaticamente se não estiver instalado
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
            'skip_download': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Verifica se é uma playlist
            if 'entries' in info:
                # Retorna informações da playlist
                return jsonify({
                    "is_playlist": True,
                    "title": info.get('title', 'Playlist'),
                    "video_count": len(info['entries']),
                    "playlist_id": info.get('id', ''),
                    "ffmpeg_available": is_ffmpeg_installed()
                })
            
            # É um vídeo único
            formats = []
            ffmpeg_available = is_ffmpeg_installed()
            
            # Primeiro adicionar formatos progressivos (com áudio e vídeo juntos)
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
            
            # Adicionar formatos de alta resolução apenas se o FFmpeg estiver disponível
            video_only_formats = []
            if ffmpeg_available:
                best_audio = None
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        # Obtenha o valor tbr, usando 0 se for None
                        current_tbr = f.get('tbr', 0) or 0  # Garante que None seja convertido para 0
                        best_tbr = best_audio.get('tbr', 0) or 0 if best_audio else 0  # Garante que None seja convertido para 0
                        
                        if best_audio is None or current_tbr > best_tbr:
                            best_audio = f
                
                if best_audio:
                    for f in info['formats']:
                        if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                            height = f.get('height', 0)
                            if height > 0:
                                format_id = f"{f['format_id']}+{best_audio['format_id']}"
                                # Calcular tamanho total com segurança
                                video_size = f.get('filesize', 0) or 0  # Converte None para 0
                                audio_size = best_audio.get('filesize', 0) or 0  # Converte None para 0
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
            
            # Combinar todos os formatos
            formats = progressive_formats + video_only_formats
            
            # Ordenar por resolução (maior primeiro)
            formats.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)
            
            # Remover duplicatas de resolução, priorizando formatos progressivos
            unique_formats = {}
            for fmt in formats:
                resolution = fmt['resolution']
                if resolution not in unique_formats or (not unique_formats[resolution]['is_progressive'] and fmt['is_progressive']):
                    unique_formats[resolution] = fmt
            
            formats = list(unique_formats.values())
            formats.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)
            
            # Preparar dicionários para retornar
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
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['POST'])
def download_video():
    url = request.form.get("url")
    format_id = request.form.get("itag")  # Mantemos "itag" para compatibilidade
    
    if not url or not format_id:
        return "Parâmetros inválidos!", 400

    try:
        # Verifica se o formato requer FFmpeg
        if "+" in format_id and not is_ffmpeg_installed():
            # Tentar baixar automaticamente
            if not download_ffmpeg():
                return "Este formato requer FFmpeg para mesclar áudio e vídeo. Por favor, escolha uma resolução mais baixa.", 400

        # Obtém informações do vídeo primeiro
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = sanitize_filename(info['title'])
            output_path = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp4")
            
            # Configurações avançadas para o download
            ydl_opts = {
                'format': format_id,
                'outtmpl': output_path,
                'quiet': True,
                'no_warnings': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'noplaylist': True,
                'postprocessors': [{
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }]
            }
            
            # Se tivermos o FFmpeg local, configurá-lo
            if os.path.exists(FFMPEG_EXECUTABLE):
                ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_EXECUTABLE)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(output_path):
                return send_file(output_path, as_attachment=True, download_name=f"{title}.mp4")
            else:
                return "Erro ao baixar o vídeo. O arquivo não foi criado.", 500

    except Exception as e:
        print(f"Erro ao baixar vídeo: {str(e)}")
        return f"Erro ao baixar o vídeo: {str(e)}", 500

@app.route('/download_playlist', methods=['POST'])
def download_playlist():
    url = request.form.get("url")
    quality = request.form.get("quality", "best")
    
    if not url:
        return "URL inválida!", 400

    # Verifica se a qualidade requer FFmpeg
    if int(quality) > 720 and not is_ffmpeg_installed():
        # Tentar baixar automaticamente
        if not download_ffmpeg():
            return "Qualidades acima de 720p requerem FFmpeg. Por favor, escolha uma qualidade menor.", 400

    try:
        # Configurações para o download de playlist
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, 'playlist/%(playlist_title)s/%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'nooverwrites': True
        }
        
        # Se tivermos o FFmpeg local, configurá-lo
        if os.path.exists(FFMPEG_EXECUTABLE):
            ydl_opts['ffmpeg_location'] = os.path.dirname(FFMPEG_EXECUTABLE)
        # Se não tiver FFmpeg, ajusta o formato para evitar mesclagem
        elif not is_ffmpeg_installed():
            ydl_opts['format'] = f'best[height<={quality}]'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        return "Playlist baixada com sucesso!", 200

    except Exception as e:
        print(f"Erro ao baixar playlist: {str(e)}")
        return f"Erro ao baixar a playlist: {str(e)}", 500

@app.route('/install-instructions', methods=['GET'])
def install_instructions():
    return render_template('install_ffmpeg.html')

@app.route('/check-ffmpeg', methods=['GET'])
def check_ffmpeg():
    """Verifica o status do FFmpeg e inicia o download se necessário"""
    if is_ffmpeg_installed():
        return jsonify({"status": "available", "message": "FFmpeg está instalado e pronto para uso."})
    
    # Tenta baixar automaticamente
    success = download_ffmpeg()
    if success:
        return jsonify({"status": "installed", "message": "FFmpeg foi baixado e configurado com sucesso!"})
    else:
        return jsonify({"status": "failed", "message": "Falha ao baixar o FFmpeg automaticamente."})

if __name__ == '__main__':
    # Tentar baixar o FFmpeg na inicialização, se necessário
    if not is_ffmpeg_installed():
        print("FFmpeg não encontrado. Tentando baixar automaticamente...")
        if download_ffmpeg():
            print("FFmpeg instalado com sucesso!")
        else:
            print("Não foi possível baixar o FFmpeg automaticamente. As resoluções altas não estarão disponíveis.")
    
    ffmpeg_status = "disponível" if is_ffmpeg_installed() else "não encontrado"
    print(f"Status do FFmpeg: {ffmpeg_status}")
    app.run(debug=True)
