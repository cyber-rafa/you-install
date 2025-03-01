/**
 * YouTube Downloader - Favicon Animado
 * Este script cria um favicon animado dinâmico para o YouTube Downloader
 */

// Configurações da animação
const FRAMES = 8;               // Número de frames da animação
const FRAME_DELAY = 300;       // Tempo entre frames em milissegundos
const SIZE = 32;                // Tamanho do ícone
const BG_COLOR = '#FF0000';     // Cor de fundo (vermelho do YouTube)
const ARROW_COLOR = '#FFFFFF';  // Cor da seta de download

let currentFrame = 0;
let faviconLink = document.querySelector('link[rel="shortcut icon"]') || 
                 document.querySelector('link[rel="icon"]');

// Se não existir um elemento link para o favicon, cria um novo
if (!faviconLink) {
    faviconLink = document.createElement('link');
    faviconLink.rel = 'icon';
    document.head.appendChild(faviconLink);
}

// Função principal de animação
function animateFavicon() {
    // Cria um elemento canvas para desenhar o favicon
    const canvas = document.createElement('canvas');
    canvas.width = SIZE;
    canvas.height = SIZE;
    const ctx = canvas.getContext('2d');
    
    // Limpa o canvas
    ctx.clearRect(0, 0, SIZE, SIZE);
    
    // Desenha o círculo de fundo
    ctx.beginPath();
    ctx.arc(SIZE/2, SIZE/2, SIZE/2, 0, Math.PI * 2);
    ctx.fillStyle = BG_COLOR;
    ctx.fill();
    
    // Calcula a posição da animação
    const progress = currentFrame / FRAMES;
    
    // Desenha o triângulo do "play" do YouTube
    ctx.beginPath();
    ctx.fillStyle = '#FFFFFF';
    
    if (progress < 0.5) {
        // Primeira metade da animação: mostra o triângulo de play
        const triangleSize = SIZE * 0.3;
        ctx.moveTo(SIZE/2 - triangleSize/2, SIZE/2 - triangleSize/2);
        ctx.lineTo(SIZE/2 + triangleSize/2, SIZE/2);
        ctx.lineTo(SIZE/2 - triangleSize/2, SIZE/2 + triangleSize/2);
        ctx.closePath();
        ctx.fill();
    } else {
        // Segunda metade da animação: mostra a seta de download
        ctx.fillStyle = ARROW_COLOR;
        const arrowWidth = SIZE * 0.4;
        const arrowHeight = SIZE * 0.4;
        const arrowX = SIZE/2 - arrowWidth/2;
        const arrowY = SIZE/2 - arrowHeight/2 - 2 + (progress - 0.5) * 8;
        
        // Desenha a haste da seta
        ctx.fillRect(
            SIZE/2 - arrowWidth/6, 
            arrowY, 
            arrowWidth/3, 
            arrowHeight * 0.7
        );
        
        // Desenha a ponta da seta
        ctx.beginPath();
        ctx.moveTo(arrowX, arrowY + arrowHeight * 0.5);
        ctx.lineTo(arrowX + arrowWidth, arrowY + arrowHeight * 0.5);
        ctx.lineTo(SIZE/2, arrowY + arrowHeight);
        ctx.closePath();
        ctx.fill();
    }
    
    // Atualiza o favicon com o canvas
    faviconLink.href = canvas.toDataURL('image/png');
    
    // Avança para o próximo frame
    currentFrame = (currentFrame + 1) % FRAMES;
    
    // Agenda o próximo frame
    setTimeout(animateFavicon, FRAME_DELAY);
}

// Inicia a animação quando a página é carregada
document.addEventListener('DOMContentLoaded', function() {
    console.log('Iniciando animação do favicon...');
    animateFavicon();
}); 