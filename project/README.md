# YouTube Downloader

Aplicação web para download de vídeos do YouTube, otimizada para hospedagem no Render (plano gratuito).

## Recursos

- Download de vídeos do YouTube em diversas qualidades
- Download de playlists (limitado a 10 vídeos)
- Interface amigável e responsiva
- Gerenciamento automático de armazenamento

## Limitações

- Armazenamento limitado a 500MB (limpeza automática quando atingir 400MB)
- Vídeos antigos são removidos automaticamente quando o limite de armazenamento é atingido
- Playlists são limitadas a 10 vídeos para economizar espaço
- Videos muito longos ou em alta resolução podem falhar devido à limitação de armazenamento

## Configurações Técnicas

- FFmpeg é baixado automaticamente quando necessário
- Verificação de espaço disponível antes de cada download
- Limpeza automática de arquivos antigos a cada 30 minutos
- Estimativa de tamanho de arquivo antes do download

## Implantação no Render

1. Crie uma conta no [Render](https://render.com/)
2. Clique em "New +" e selecione "Web Service"
3. Conecte seu repositório GitHub ou use a opção de deploy manual
4. Configure o serviço:
   - Nome: `youtube-downloader` (ou outro de sua escolha)
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Plano: selecione o plano gratuito

5. Defina as seguintes variáveis de ambiente (opcional):
   - `MAX_STORAGE_MB`: 500 (padrão)
   - `CLEANUP_THRESHOLD`: 400 (padrão)
   - `CLEANUP_INTERVAL`: 1800 (padrão, em segundos)

6. Clique em "Create Web Service"

## Desenvolvimento Local

```bash
# Clone o repositório
git clone <seu-repositorio>

# Navegue até a pasta do projeto
cd project

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
python app.py
```

## Licença

Este projeto é distribuído sob a licença MIT. 