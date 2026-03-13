// ===========================================
// tema.js - PADRÃO DO SISTEMA
// ===========================================

function atualizarRotuloTema(tema) {
    const temaSpan = document.getElementById('temaAtual');
    const botaoTema = document.getElementById('btnTemaGlobal');
    const texto = tema === 'dark' ? 'Escuro' : 'Claro';
    if (temaSpan) temaSpan.textContent = texto;
    if (botaoTema) {
        botaoTema.textContent = tema === 'dark'
            ? '🎨 Tema Global: Escuro (clique para Claro)'
            : '🎨 Tema Global: Claro (clique para Escuro)';
    }
}

function aplicarTema(tema) {
    const html = document.documentElement;
    const toggle = document.getElementById('toggleTema');
    const temaFinal = tema === 'light' ? 'light' : 'dark';
    html.setAttribute('data-theme', temaFinal);
    localStorage.setItem('tema', temaFinal);
    if (toggle) {
        toggle.checked = temaFinal === 'dark';
    }
    atualizarRotuloTema(temaFinal);
}

// Alternar entre tema claro e escuro (compatível com switch antigo)
function alternarTema() {
    const toggle = document.getElementById('toggleTema');
    if (toggle) {
        aplicarTema(toggle.checked ? 'dark' : 'light');
        return;
    }
    const atual = document.documentElement.getAttribute('data-theme') || localStorage.getItem('tema') || 'dark';
    aplicarTema(atual === 'dark' ? 'light' : 'dark');
}

function alternarTemaGlobal() {
    const atual = document.documentElement.getAttribute('data-theme') || localStorage.getItem('tema') || 'dark';
    aplicarTema(atual === 'dark' ? 'light' : 'dark');
}

// Carregar tema salvo
function carregarTema() {
    const temaSalvo = localStorage.getItem('tema') || 'dark'; // dark é padrão
    aplicarTema(temaSalvo);
}

// Carregar tema quando a página iniciar
document.addEventListener('DOMContentLoaded', carregarTema);

// Exportar função para uso global
window.alternarTema = alternarTema;
window.alternarTemaGlobal = alternarTemaGlobal;
