# 📥 YouTube Downloader - Projeto

<div align="center">
  
![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![yt-dlp](https://img.shields.io/badge/yt--dlp-Latest-red.svg)
![Render](https://img.shields.io/badge/Render-Compatible-blueviolet.svg)

**Aplicação web para download de vídeos do YouTube, otimizada para hospedagem no Render (plano gratuito)**

[Recursos](#-recursos) • 
[Limitações](#-limitações) • 
[Configurações](#-configurações-técnicas) • 
[Implantação](#-implantação-no-render) • 
[Desenvolvimento](#-desenvolvimento-local)

</div>

## 🚀 Recursos

- 📹 Download de vídeos do YouTube em **diversas qualidades**
- 📋 Suporte para download de **playlists** (limitado a 10 vídeos)
- 🎨 Interface amigável e **totalmente responsiva**
- 💾 Gerenciamento **automático e inteligente** de armazenamento
- 🛠️ Detecção e instalação automática do **FFmpeg**
- 🌐 Compatível com ambientes de **hospedagem gratuita**

## ⚠️ Limitações

- 💽 Armazenamento limitado a **500MB** (limpeza automática quando atingir 400MB)
- 🗑️ Vídeos antigos são **removidos automaticamente** quando o limite de armazenamento é atingido
- 📑 Playlists são limitadas a **10 vídeos** para economizar espaço
- ⏱️ Vídeos muito longos ou em alta resolução podem falhar devido à limitação de armazenamento

## ⚙️ Configurações Técnicas

- 🔄 **FFmpeg** é baixado e configurado automaticamente quando necessário
- 📊 Verificação de **espaço disponível** antes de cada download
- 🧹 Limpeza **automática** de arquivos antigos a cada 30 minutos
- 📏 **Estimativa de tamanho** de arquivo antes do download
- 🔒 Sanitização de nomes de arquivos e URLs para maior segurança

## 🌩️ Implantação no Render

1. Crie uma conta no [Render](https://render.com/)
2. Clique em **"New +"** e selecione **"Web Service"**
3. Conecte seu repositório GitHub ou use a opção de deploy manual
4. Configure o serviço:
   - **Nome**: `youtube-downloader` (ou outro de sua escolha)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plano**: selecione o plano gratuito

5. Defina as seguintes **variáveis de ambiente** (opcional):
   - `MAX_STORAGE_MB`: 500 (padrão)
   - `CLEANUP_THRESHOLD`: 400 (padrão)
   - `CLEANUP_INTERVAL`: 1800 (padrão, em segundos)

6. Clique em **"Create Web Service"**

## 💻 Desenvolvimento Local

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/youtube-downloader.git

# Navegue até a pasta do projeto
cd youtube-downloader/project

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
python app.py
```

## 🔧 Estrutura do Projeto

```
project/
│
├── app.py              # Aplicação principal Flask
├── templates/          # Templates HTML
│   ├── homepage.html   # Página principal da aplicação
│   └── install_ffmpeg.html # Página de instruções para FFmpeg
│
├── static/             # Arquivos estáticos (CSS, JS, imagens)
│
├── downloads/          # Pasta onde os vídeos são salvos
│
└── ffmpeg/             # Pasta para o FFmpeg baixado automaticamente
```

## 🔍 Depuração Comum

- **Erro de memória**: Reduzir a qualidade do vídeo ou diminuir o tamanho da playlist
- **FFmpeg não encontrado**: A aplicação tentará baixar automaticamente, mas pode falhar em alguns ambientes
- **Erro de permissão**: Verifique as permissões das pastas de download e FFmpeg

## 📜 Licença

Este projeto é distribuído sob a [licença MIT](../LICENSE).

---

<div align="center">
  
**Desenvolvido com ❤️ para simplificar seus downloads do YouTube**

</div> 