# YouTube Downloader para Replit

Aplicativo web que permite baixar vídeos e playlists do YouTube em diferentes resoluções, incluindo resoluções altas como 1080p, 2K e 4K.

## Como configurar no Replit

1. Faça um fork deste repositório no Replit
2. Execute o script de instalação do FFmpeg:
   ```
   bash install_ffmpeg.sh
   ```
3. Aguarde a instalação ser concluída
4. Execute o aplicativo clicando no botão "Run"

## Funcionalidades

- Baixar vídeos do YouTube em múltiplas resoluções
- Suporte para baixar playlists completas
- Gerenciamento automático de espaço (limitado a 300MB no Replit)
- Instalação automática do FFmpeg para suportar vídeos em alta resolução
- Interface web amigável

## Limitações no Replit

- O aplicativo tem um limite de armazenamento de 300MB para evitar problemas
- Arquivos antigos são automaticamente removidos quando o espaço está ficando escasso
- A velocidade de download pode ser limitada pelo ambiente Replit
- O aplicativo pode hibernar após períodos de inatividade (plano gratuito do Replit)

## Uso local

Você também pode executar este aplicativo localmente:

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute: `python project/app.py`

## Observações

Este aplicativo é apenas para fins educacionais. O download de conteúdo protegido por direitos autorais pode violar os Termos de Serviço do YouTube.

## Créditos

Este aplicativo utiliza as seguintes bibliotecas:
- Flask para a interface web
- yt-dlp para interagir com o YouTube
- FFmpeg para processar vídeos de alta resolução
