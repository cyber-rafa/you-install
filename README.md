# YouTube Downloader para Windows

Aplicativo web que permite baixar vídeos e playlists do YouTube em diferentes resoluções, incluindo resoluções altas como 1080p, 2K e 4K.

## Funcionalidades

- Baixar vídeos do YouTube em múltiplas resoluções
- Suporte para baixar playlists completas
- Gerenciamento automático de espaço
- Instalação automática do FFmpeg para suportar vídeos em alta resolução
- Interface web amigável

## Como usar

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute o aplicativo: `python project/app.py`
4. Acesse em seu navegador: `http://localhost:5000`

## Requisitos

- Python 3.6 ou superior
- FFmpeg (instalado automaticamente se não estiver presente)
- Acesso à internet para baixar vídeos e o FFmpeg

## Resolução de Problemas

Se você encontrar erros de conexão como "Failed to fetch", pode ser devido a:
1. Timeout nas requisições ao YouTube - o aplicativo agora utiliza timeouts mais generosos
2. Problemas com o firewall ou proxy - certifique-se de que o acesso ao YouTube não está bloqueado
3. Limitação temporária do YouTube - aguarde alguns minutos e tente novamente

## Observações

Este aplicativo é apenas para fins educacionais. O download de conteúdo protegido por direitos autorais pode violar os Termos de Serviço do YouTube.

## Créditos

Este aplicativo utiliza as seguintes bibliotecas:
- Flask para a interface web
- yt-dlp para interagir com o YouTube
- FFmpeg para processar vídeos de alta resolução
