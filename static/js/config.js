// config.js

let profissionaisCadastrados = [];
const CHAVE_PROF_ENVIO_AUTO = 'config_profissional_envio_auto';

function alertErro(mensagem) {
    if (window.ui) return window.ui.error(mensagem);
    alert(`Erro: ${mensagem}`);
}

function alertSucesso(mensagem) {
    if (window.ui) return window.ui.success(mensagem);
    alert(`Sucesso: ${mensagem}`);
}

function getEl(id) {
    return document.getElementById(id);
}

function soDigitos(valor) {
    return (valor || '').replace(/\D/g, '');
}

function formatarCnpj(valor) {
    const digitos = soDigitos(valor).slice(0, 14);
    if (digitos.length <= 2) return digitos;
    if (digitos.length <= 5) return `${digitos.slice(0, 2)}.${digitos.slice(2)}`;
    if (digitos.length <= 8) return `${digitos.slice(0, 2)}.${digitos.slice(2, 5)}.${digitos.slice(5)}`;
    if (digitos.length <= 12) return `${digitos.slice(0, 2)}.${digitos.slice(2, 5)}.${digitos.slice(5, 8)}/${digitos.slice(8)}`;
    return `${digitos.slice(0, 2)}.${digitos.slice(2, 5)}.${digitos.slice(5, 8)}/${digitos.slice(8, 12)}-${digitos.slice(12, 14)}`;
}

function validarCnpj(cnpj) {
    const valor = soDigitos(cnpj);
    if (valor.length !== 14) return false;
    if (/^(\d)\1{13}$/.test(valor)) return false;

    const calcDigito = (base, pesos) => {
        const soma = base.split('').reduce((acc, n, i) => acc + (parseInt(n, 10) * pesos[i]), 0);
        const resto = soma % 11;
        return resto < 2 ? 0 : 11 - resto;
    };

    const base12 = valor.slice(0, 12);
    const d1 = calcDigito(base12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);
    const base13 = base12 + String(d1);
    const d2 = calcDigito(base13, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]);

    return valor === `${base12}${d1}${d2}`;
}

function mascararCnpjEnvio(input) {
    if (!input) return;
    input.value = formatarCnpj(input.value);
}

function validarCnpjCampo(input) {
    if (!input) return false;
    const valido = validarCnpj(input.value);
    input.style.borderColor = valido ? '' : '#e74c3c';
    input.title = valido ? '' : 'CNPJ inválido';
    return valido;
}

function getCredenciaisTela() {
    return {
        email_cliente: (getEl('emailCliente')?.value || '').trim(),
        senha_app: (getEl('senhaApp')?.value || '').replace(/\s/g, '').trim(),
        email_contador: (getEl('emailContador')?.value || '').trim()
    };
}

function validarCredenciais(credenciais, exigirSenha = true) {
    const { email_cliente, senha_app, email_contador } = credenciais;
    if (!email_cliente || !email_contador || (exigirSenha && !senha_app)) {
        alertErro('Preencha e-mail remetente, senha de app e e-mail do contador.');
        return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email_cliente) || !emailRegex.test(email_contador)) {
        alertErro('E-mail inválido.');
        return false;
    }

    if (exigirSenha && senha_app.length !== 16) {
        alertErro('Senha de app deve ter 16 caracteres.');
        return false;
    }

    return true;
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const dados = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(dados.erro || 'Falha na requisição.');
    return dados;
}

async function carregarConfig() {
    try {
        const config = await requestJson('/api/config/contador');
        preencherCampos(config || {});
    } catch (error) {
        console.error(error);
    }
}

function preencherCampos(config) {
    if (!config) return;
    if (config.email_cliente) getEl('emailCliente').value = config.email_cliente;
    if (config.email_contador) getEl('emailContador').value = config.email_contador;
    if (config.frequencia) getEl('frequenciaEnvio').value = config.frequencia;
    if (config.dia_envio) getEl('diaEnvio').value = config.dia_envio;
    if (config.ativo !== undefined) getEl('envioAtivo').checked = config.ativo;

    const selectProf = getEl('profissionalEnvioAuto');
    if (selectProf) {
        const salvoServidor = (config.profissional_envio_auto || '').trim();
        const salvoLocal = localStorage.getItem(CHAVE_PROF_ENVIO_AUTO) || '';
        const valorFinal = salvoServidor || salvoLocal;
        if (valorFinal) selectProf.value = valorFinal;
    }
}

function preencherSelectProfissionalEnvio() {
    const select = getEl('profissionalEnvioAuto');
    if (!select) return;

    const valorAtual = select.value || localStorage.getItem(CHAVE_PROF_ENVIO_AUTO) || '';
    const opcoes = [
        '<option value="">Todos os profissionais</option>',
        ...profissionaisCadastrados.map((p) => `<option value="${p.nome || ''}">${p.nome || ''}</option>`)
    ];
    select.innerHTML = opcoes.join('');

    if (valorAtual && profissionaisCadastrados.some((p) => (p.nome || '') === valorAtual)) {
        select.value = valorAtual;
    } else {
        select.value = '';
    }
}

async function salvarConfig() {
    const credenciais = getCredenciaisTela();
    if (!validarCredenciais(credenciais, true)) return;

    const payload = {
        email_cliente: credenciais.email_cliente,
        senha_app: credenciais.senha_app,
        email_contador: credenciais.email_contador,
        profissional_envio_auto: (getEl('profissionalEnvioAuto')?.value || '').trim(),
        frequencia: getEl('frequenciaEnvio').value,
        dia_envio: parseInt(getEl('diaEnvio').value, 10) || 1,
        ativo: getEl('envioAtivo').checked
    };

    try {
        await requestJson('/api/config/contador', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const profissionalEnvio = (getEl('profissionalEnvioAuto')?.value || '').trim();
        localStorage.setItem(CHAVE_PROF_ENVIO_AUTO, profissionalEnvio);
        getEl('senhaApp').value = '';
        alertSucesso('Configurações salvas com sucesso.');
        carregarHistorico();
    } catch (error) {
        alertErro(error.message);
    }
}

function renderTabelaProfissionaisCadastro(lista) {
    const tbody = getEl('tabelaProfissionaisCadastro');
    if (!tbody) return;

    if (!lista.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center mensagem-carregando">Nenhum profissional cadastrado.</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = lista.map((prof) => `
        <tr>
            <td>${prof.nome || '---'}</td>
            <td>${formatarCnpj(prof.cnpj || '')}</td>
            <td>
                <button class="btn btn-cancelar" onclick='removerProfissional(${prof.id}, ${JSON.stringify(prof.nome || "")})'>
                    🗑️ Remover
                </button>
            </td>
        </tr>
    `).join('');
}

async function carregarProfissionaisCadastrados() {
    const tbody = getEl('tabelaProfissionaisCadastro');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center mensagem-carregando">Carregando profissionais...</td>
            </tr>
        `;
    }

    try {
        const dados = await requestJson('/api/profissionais/?ativos=0');
        profissionaisCadastrados = Array.isArray(dados) ? dados : [];
        renderTabelaProfissionaisCadastro(profissionaisCadastrados);
        preencherSelectProfissionalEnvio();
    } catch (error) {
        profissionaisCadastrados = [];
        renderTabelaProfissionaisCadastro([]);
        preencherSelectProfissionalEnvio();
        alertErro(error.message);
    }
}

async function cadastrarProfissional() {
    const nomeInput = getEl('nomeProfissionalCadastro');
    const cnpjInput = getEl('cnpjProfissionalCadastro');
    const nome = (nomeInput?.value || '').trim();
    const cnpj = formatarCnpj(cnpjInput?.value || '');

    if (!nome || !cnpj) {
        alertErro('Informe nome e CNPJ do profissional.');
        return;
    }
    cnpjInput.value = cnpj;
    if (!validarCnpjCampo(cnpjInput)) {
        alertErro('Informe um CNPJ válido.');
        return;
    }

    try {
        await requestJson('/api/profissionais/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, cnpj, ativo: true })
        });
        nomeInput.value = '';
        cnpjInput.value = '';
        alertSucesso('Profissional cadastrado com sucesso.');
        await carregarProfissionaisCadastrados();
    } catch (error) {
        alertErro(error.message);
    }
}

async function removerProfissional(id, nome) {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync(`Confirma remover o profissional ${nome}?`)
        : (window.ui ? window.ui.confirm(`Confirma remover o profissional ${nome}?`) : confirm(`Confirma remover o profissional ${nome}?`));
    if (!confirmado) return;

    try {
        await requestJson(`/api/profissionais/${id}`, { method: 'DELETE' });
        alertSucesso('Profissional removido com sucesso.');
        await carregarProfissionaisCadastrados();
    } catch (error) {
        alertErro(error.message);
    }
}

async function exportarDados() {
    const tipo = getEl('tipoExportacao').value;
    const formato = getEl('formatoExportacao').value;

    if (formato === 'db' && tipo !== 'completo') {
        alertErro('Exportação em .db só é permitida para "Banco completo".');
        return;
    }

    const confirmadoExport = window.ui?.confirmAsync
        ? await window.ui.confirmAsync(`Confirma exportar dados em ${formato.toUpperCase()}?`)
        : (window.ui ? window.ui.confirm(`Confirma exportar dados em ${formato.toUpperCase()}?`) : confirm(`Confirma exportar dados em ${formato.toUpperCase()}?`));
    if (!confirmadoExport) return;

    try {
        const response = await fetch(`/api/export/exportar?tipo=${tipo}&formato=${formato}`);
        if (!response.ok) {
            const erro = await response.json().catch(() => ({}));
            throw new Error(erro.erro || 'Erro ao exportar.');
        }

        const blob = await response.blob();
        const urlBlob = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        const data = new Date().toISOString().split('T')[0];

        a.href = urlBlob;
        a.download = formato === 'db'
            ? `backup_${tipo}_${data}.db`
            : `exportacao_${tipo}_${data}.${formato}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(urlBlob);

        alertSucesso('Exportação concluída.');
    } catch (error) {
        alertErro(error.message);
    }
}

async function importarDados() {
    const fileInput = getEl('arquivoImportar');
    const tipo = getEl('tipoImportacao').value;
    const formato = getEl('formatoImportacao').value;
    const resultadoDiv = getEl('resultadoImportacao');

    if (!fileInput.files.length) {
        alertErro('Selecione um arquivo para importar.');
        return;
    }
    if (tipo === 'completo' && (formato === 'csv' || formato === 'xlsx')) {
        alertErro('Importação completa aceita apenas arquivo JSON.');
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', fileInput.files[0]);
    formData.append('tipo', tipo);
    formData.append('formato', formato);

    resultadoDiv.style.display = 'block';
    resultadoDiv.className = '';
    resultadoDiv.innerHTML = 'Processando importação...';

    try {
        const response = await fetch('/api/export/importar', { method: 'POST', body: formData });
        const resultado = await response.json().catch(() => ({}));

        if (!response.ok) throw new Error(resultado.erro || 'Erro na importação.');

        resultadoDiv.className = 'success-message';
        resultadoDiv.innerHTML = `Importação concluída. Clientes: ${resultado.clientes || 0}, Ordens: ${resultado.ordens || 0}, Saídas: ${resultado.saidas || 0}.`;
        if (tipo === 'clientes' || tipo === 'completo') {
            window.dispatchEvent(new CustomEvent('dadosAtualizados'));
        }
    } catch (error) {
        resultadoDiv.className = 'error-message';
        resultadoDiv.innerHTML = `Erro: ${error.message}`;
    }
}

async function carregarHistorico() {
    const tbody = getEl('tabelaEnvios');
    if (!tbody) return;

    try {
        const envios = await requestJson('/api/config/envios-relatorio');
        if (!envios.length) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 30px;">Nenhum envio registrado.</td></tr>`;
            return;
        }

        tbody.innerHTML = '';
        envios.slice(0, 10).forEach((envio) => {
            const statusClass = envio.status === 'enviado' ? 'status-sucesso' : 'status-erro';
            const data = new Date(envio.data_envio);
            const dataFormatada = `${data.toLocaleDateString('pt-BR')} ${data.toLocaleTimeString('pt-BR')}`;

            tbody.innerHTML += `
                <tr>
                    <td>${dataFormatada}</td>
                    <td>${envio.periodo || '---'}</td>
                    <td>${(envio.formato || 'html').toUpperCase()}</td>
                    <td>${envio.remetente || '---'}</td>
                    <td>${envio.destinatario || '---'}</td>
                    <td><span class="status-envio ${statusClass}">${envio.status}</span></td>
                </tr>
            `;
        });
    } catch (error) {
        console.error(error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    carregarConfig();
    carregarHistorico();
    carregarProfissionaisCadastrados();

    const cnpjCadastroInput = getEl('cnpjProfissionalCadastro');
    if (cnpjCadastroInput) {
        cnpjCadastroInput.addEventListener('input', () => mascararCnpjEnvio(cnpjCadastroInput));
        cnpjCadastroInput.addEventListener('blur', () => validarCnpjCampo(cnpjCadastroInput));
    }

    const selectProf = getEl('profissionalEnvioAuto');
    if (selectProf) {
        selectProf.addEventListener('change', () => {
            localStorage.setItem(CHAVE_PROF_ENVIO_AUTO, selectProf.value || '');
        });
    }

    window.addEventListener('dadosAtualizados', carregarHistorico);
});

window.salvarConfig = salvarConfig;
window.cadastrarProfissional = cadastrarProfissional;
window.removerProfissional = removerProfissional;
window.mascararCnpjEnvio = mascararCnpjEnvio;
window.validarCnpjCampo = validarCnpjCampo;
window.exportarDados = exportarDados;
window.importarDados = importarDados;
