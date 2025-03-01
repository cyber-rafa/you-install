/**
 * YouTube Downloader - Animação de Carregamento
 * Este script cria uma animação durante o download dos vídeos
 */

class LoadingAnimation {
    constructor(container) {
        // Elemento onde a animação será inserida
        this.container = container;
        // Estado da animação
        this.isActive = false;
        // Referência ao elemento da animação
        this.element = null;
        // Cores da animação
        this.colors = [
            '#FF0000', // Vermelho (YouTube)
            '#FF5722', // Laranja profundo
            '#FF9800', // Laranja
            '#FFC107', // Âmbar
            '#FFEB3B'  // Amarelo
        ];
    }

    /**
     * Inicia a animação de carregamento
     * @param {string} message - Mensagem a ser exibida durante o carregamento
     */
    start(message = 'Baixando vídeo...') {
        if (this.isActive) return;
        this.isActive = true;

        // Cria o elemento para a animação
        this.element = document.createElement('div');
        this.element.className = 'loading-animation';
        
        // Estiliza o elemento como um modal compacto e moderno
        const style = this.element.style;
        style.position = 'fixed';
        style.top = '50%';
        style.left = '50%';
        style.width = '320px';
        style.maxWidth = '90%';
        style.transform = 'translate(-50%, -50%) scale(0.9)';
        style.backgroundColor = 'rgba(30, 41, 59, 0.95)';
        style.borderRadius = '12px';
        style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.5)';
        style.padding = '25px';
        style.display = 'flex';
        style.flexDirection = 'column';
        style.justifyContent = 'center';
        style.alignItems = 'center';
        style.zIndex = '900';
        style.fontFamily = 'Segoe UI, Arial, sans-serif';
        style.color = 'white';
        style.backdropFilter = 'blur(5px)';
        style.transition = 'all 0.3s ease';
        style.opacity = '0';
        
        // Estrutura interna da animação
        this.element.innerHTML = `
            <div class="animation-container" style="position: relative; width: 80px; height: 80px; margin-bottom: 20px;">
                <div class="animation-circles"></div>
            </div>
            <div class="loading-message" style="font-size: 16px; font-weight: bold; margin-bottom: 8px; text-align: center;">${message}</div>
            <div class="loading-progress" style="font-size: 14px; opacity: 0.8; text-align: center;">Iniciando...</div>
        `;
        
        // Cria um overlay semi-transparente para o fundo (não bloqueia toda a tela)
        this.overlay = document.createElement('div');
        this.overlay.style.position = 'fixed';
        this.overlay.style.top = '0';
        this.overlay.style.left = '0';
        this.overlay.style.width = '100%';
        this.overlay.style.height = '100%';
        this.overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.3)';
        this.overlay.style.backdropFilter = 'blur(3px)';
        this.overlay.style.zIndex = '899';
        this.overlay.style.opacity = '0';
        this.overlay.style.transition = 'opacity 0.3s ease';
        
        // Cria os círculos da animação
        const circlesContainer = this.element.querySelector('.animation-circles');
        circlesContainer.style.width = '100%';
        circlesContainer.style.height = '100%';
        circlesContainer.style.position = 'relative';
        
        // Adiciona os círculos com animação
        for (let i = 0; i < 4; i++) {
            const circle = document.createElement('div');
            circle.style.position = 'absolute';
            circle.style.top = '50%';
            circle.style.left = '50%';
            circle.style.width = '60px';
            circle.style.height = '60px';
            circle.style.marginLeft = '-30px';
            circle.style.marginTop = '-30px';
            circle.style.borderRadius = '50%';
            circle.style.border = `3px solid ${this.colors[i % this.colors.length]}`;
            circle.style.animation = `spin ${1.2 + i * 0.2}s linear infinite`;
            circle.style.opacity = '0.7';
            circle.style.borderTopColor = 'transparent';
            circle.style.borderLeftColor = 'transparent';
            circlesContainer.appendChild(circle);
        }
        
        // Adiciona a keyframe da animação se ainda não existir
        if (!document.querySelector('#loading-animation-keyframes')) {
            const style = document.createElement('style');
            style.id = 'loading-animation-keyframes';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                @keyframes pulse {
                    0% { transform: scale(0.95); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(0.95); }
                }
                
                @keyframes fade-in {
                    from { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
                    to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                }
                
                .loading-progress {
                    background: linear-gradient(90deg, #3b82f6, #2563eb);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-weight: 500;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Adiciona os elementos à página
        document.body.appendChild(this.overlay);
        document.body.appendChild(this.element);
        
        // Inicia a animação de aparecer gradualmente
        setTimeout(() => {
            this.overlay.style.opacity = '1';
            this.element.style.opacity = '1';
            this.element.style.transform = 'translate(-50%, -50%) scale(1)';
        }, 10);
        
        // Inicia o timer de atualização da mensagem
        this._startProgressUpdates();
    }
    
    /**
     * Atualiza a mensagem de progresso periodicamente
     */
    _startProgressUpdates() {
        if (!this.isActive) return;
        
        const progressElement = this.element.querySelector('.loading-progress');
        const tips = [
            'Buscando informações...',
            'Processando streams...',
            'Preparando download...',
            'Baixando conteúdo...',
            'Quase lá...'
        ];
        
        let currentTip = 0;
        this.progressInterval = setInterval(() => {
            if (currentTip < tips.length) {
                progressElement.textContent = tips[currentTip];
                currentTip++;
            } else {
                // Adiciona pontos para indicar que ainda está em progresso
                if (progressElement.textContent.endsWith('...')) {
                    progressElement.textContent = tips[tips.length - 1];
                } else {
                    progressElement.textContent += '.';
                }
            }
        }, 1500);
    }
    
    /**
     * Atualiza o progresso da animação com uma porcentagem específica
     * @param {number} percent - Porcentagem de conclusão (0-100)
     * @param {string} message - Mensagem opcional para mostrar
     */
    updateProgress(percent, message = null) {
        if (!this.isActive || !this.element) return;
        
        const progressElement = this.element.querySelector('.loading-progress');
        const messageElement = this.element.querySelector('.loading-message');
        
        // Atualiza a mensagem principal se fornecida
        if (message) {
            messageElement.textContent = message;
        }
        
        // Atualiza o progresso
        progressElement.textContent = `${Math.round(percent)}% concluído`;
        
        // Adiciona uma barra de progresso visual
        if (!this.element.querySelector('.progress-bar-container')) {
            const barContainer = document.createElement('div');
            barContainer.className = 'progress-bar-container';
            barContainer.style.width = '100%';
            barContainer.style.height = '4px';
            barContainer.style.backgroundColor = 'rgba(255,255,255,0.2)';
            barContainer.style.borderRadius = '2px';
            barContainer.style.marginTop = '15px';
            barContainer.style.overflow = 'hidden';
            
            const bar = document.createElement('div');
            bar.className = 'progress-bar';
            bar.style.height = '100%';
            bar.style.width = '0%';
            bar.style.backgroundColor = '#3b82f6';
            bar.style.transition = 'width 0.3s ease';
            bar.style.borderRadius = '2px';
            
            barContainer.appendChild(bar);
            this.element.appendChild(barContainer);
        }
        
        // Atualiza a largura da barra de progresso
        const bar = this.element.querySelector('.progress-bar');
        if (bar) {
            bar.style.width = `${percent}%`;
        }
    }
    
    /**
     * Para a animação de carregamento
     */
    stop() {
        if (!this.isActive) return;
        
        clearInterval(this.progressInterval);
        
        // Animação de desaparecimento
        if (this.overlay) {
            this.overlay.style.opacity = '0';
        }
        
        if (this.element) {
            this.element.style.opacity = '0';
            this.element.style.transform = 'translate(-50%, -50%) scale(0.9)';
        }
        
        // Remove os elementos após a animação terminar
        setTimeout(() => {
            if (this.overlay && this.overlay.parentNode) {
                this.overlay.parentNode.removeChild(this.overlay);
            }
            
            if (this.element && this.element.parentNode) {
                this.element.parentNode.removeChild(this.element);
            }
            
            this.overlay = null;
            this.element = null;
            this.isActive = false;
        }, 300);
    }
}

// Cria uma instância global da animação
window.loadingAnimation = new LoadingAnimation(document.body);

// Adiciona funções auxiliares ao objeto global
window.startLoading = (message) => window.loadingAnimation.start(message);
window.updateLoading = (percent, message) => window.loadingAnimation.updateProgress(percent, message);
window.stopLoading = () => window.loadingAnimation.stop(); 