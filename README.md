# 📺 YouTube Downloader para Windows

<div align="center">

![Versão](https://img.shields.io/badge/versão-1.0.0-blue?style=for-the-badge&logo=github&logoColor=white&color=228B22)
![Python](https://img.shields.io/badge/Python-3.6+-blue?style=for-the-badge&logo=python&logoColor=white&color=3776AB)
![Flask](https://img.shields.io/badge/Flask-2.0+-blue?style=for-the-badge&logo=flask&logoColor=white&color=000000)
[![Licença](https://img.shields.io/badge/Licença-MIT-blue?style=for-the-badge&color=A31F34)](LICENSE)

<img src="project/static/ico.png" alt="YouTube Downloader Logo" width="150px" height="150px" />

**Um aplicativo web elegante para baixar vídeos e playlists do YouTube em múltiplas resoluções, incluindo 4K.**

[Funcionalidades](#-funcionalidades) • 
[Instalação](#-instalação) • 
[Como Usar](#-como-usar) • 
[Resolução de Problemas](#️-resolução-de-problemas) • 
[Observações](#-observações)

</div>

<br>

## ✨ Funcionalidades

<details open>
<summary><b>Clique para expandir/colapsar</b></summary>
<br>

<table>
  <tr>
    <td>
      <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExeTl6Y2t0cmRhaXcwbHptanBxbjJ0d2FiZHh4dTdvYW0xYXZkMGZneSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/YRzQnWzbn4WIxd3LYd/giphy.gif" width="280px">
    </td>
    <td>
      <ul>
        <li>📥 <b>Vídeos em alta qualidade</b> - Baixe em 720p, 1080p, 2K e até 4K!</li>
        <li>🎵 <b>Compatibilidade perfeita</b> - Áudio e vídeo sincronizados automaticamente</li>
        <li>📋 <b>Suporte para playlists</b> - Baixe coleções inteiras de vídeos facilmente</li>
        <li>🧰 <b>Instalação automática</b> - FFmpeg instalado automaticamente se necessário</li>
        <li>💾 <b>Gerenciamento inteligente</b> - Controle automático de armazenamento</li>
        <li>🌐 <b>Interface amigável</b> - Design intuitivo e responsivo</li>
      </ul>
    </td>
  </tr>
</table>

</details>

## 🚀 Instalação

<details open>
<summary><b>Clique para expandir/colapsar</b></summary>
<br>

<div align="center">

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/youtube-downloader.git

# Entre no diretório
cd youtube-downloader

# Instale as dependências
pip install -r requirements.txt

# Execute o aplicativo
python project/app.py
```

<img src="https://i.imgur.com/vzKHTuA.gif" alt="Instalação" width="600px">

</div>

</details>

## 📱 Como Usar

<details open>
<summary><b>Clique para expandir/colapsar</b></summary>
<br>

<div align="center">

### <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Hand%20gestures/Backhand%20Index%20Pointing%20Right.png" alt="Pointing" width="25" height="25" /> Acesse o aplicativo em seu navegador: `http://localhost:5000`

### <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Hand%20gestures/Backhand%20Index%20Pointing%20Right.png" alt="Pointing" width="25" height="25" /> Cole a URL do vídeo ou playlist do YouTube

### <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Hand%20gestures/Backhand%20Index%20Pointing%20Right.png" alt="Pointing" width="25" height="25" /> Selecione a qualidade desejada e clique em "Baixar"

<img src="https://i.imgur.com/LXJ1HkZ.gif" alt="Demonstração de Uso" width="70%">

</div>

</details>

## 🛠️ Resolução de Problemas

<details>
<summary><b>Clique para expandir/colapsar</b></summary>
<br>

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Objects/Wrench.png" alt="Wrench" width="90px" height="90px" />
</div>

### Erros comuns e soluções:

| Problema | Possíveis Soluções |
|----------|-------------------|
| **"Failed to fetch"** | • Timeout nas requisições - O app agora usa timeouts maiores<br>• Verifique sua conexão com a internet<br>• Problemas de firewall/proxy - Verifique suas configurações<br>• Limitação do YouTube - Aguarde alguns minutos |
| **Vídeo sem áudio** | • Certifique-se que o FFmpeg está instalado<br>• Clique em "Instalar automaticamente" na interface |
| **Erro 403/Forbidden** | • O YouTube pode estar bloqueando requisições frequentes<br>• Aguarde alguns minutos antes de tentar novamente |
| **Pasta "downloads" não encontrada** | • Será criada automaticamente na primeira execução<br>• Verifique as permissões da pasta do aplicativo |

</details>

## 📝 Observações

<details>
<summary><b>Clique para expandir/colapsar</b></summary>
<br>

> ⚠️ **Aviso Legal**: Este aplicativo é apenas para fins educacionais. O download de conteúdo protegido por direitos autorais pode violar os Termos de Serviço do YouTube.

<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Warning.png" alt="Warning" width="90px" height="90px" />
</div>

### Requisitos do Sistema:

- Python 3.6 ou superior
- Espaço em disco suficiente para downloads
- Conexão com a Internet
- FFmpeg (instalado automaticamente se necessário)

</details>

## 🙏 Créditos

<details>
<summary><b>Clique para expandir/colapsar</b></summary>
<br>

Este aplicativo utiliza as seguintes tecnologias:

<div align="center">
  
  <a href="https://flask.palletsprojects.com/"><img src="https://i.imgur.com/bv59Mxn.png" alt="Flask" height="60"></a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://github.com/yt-dlp/yt-dlp"><img src="https://i.imgur.com/Ry3tjzI.png" alt="yt-dlp" height="60"></a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://ffmpeg.org/"><img src="https://i.imgur.com/Wov7tg5.png" alt="FFmpeg" height="60"></a>
  
</div>

</details>

<div align="center">

<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Star.png" alt="Star" width="25" height="25" /> 
**Não se esqueça de deixar uma estrela se gostou do projeto!** 
<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Symbols/Star.png" alt="Star" width="25" height="25" />

</div>
