const INDEX_LOGO_PADRAO = '/static/images/picapau4.png';
const INDEX_TITULO_PADRAO = 'SISTEMA DE GERENCIAMENTO OFICINA 39';

async function carregarPersonalizacaoIndex() {
    try {
        const response = await fetch('/api/config/contador');
        const config = await response.json().catch(() => ({}));
        if (!response.ok || !config) return;

        const titulo = document.getElementById('indexTituloSistema');
        const imagem = document.getElementById('indexLogoImagem');
        const container = document.querySelector('.imagem-container');
        const stage = document.getElementById('indexLogoStage');

        if (titulo) {
            titulo.textContent = (config.nome_exibicao_sistema || '').trim()
                || (config.empresa_nome || '').trim()
                || INDEX_TITULO_PADRAO;
        }

        if (imagem) {
            imagem.src = (config.logo_index_path || '').trim() || INDEX_LOGO_PADRAO;
        }

        if (container) {
            const formato = (config.logo_index_formato || 'circulo').trim();
            container.classList.toggle('logo-shape-square', formato === 'quadrado');
            if (stage) {
                stage.classList.toggle('logo-shape-square', formato === 'quadrado');
            }
        }
    } catch (error) {
        console.error('Falha ao carregar personalização da index:', error);
    }
}

document.addEventListener('DOMContentLoaded', carregarPersonalizacaoIndex);
