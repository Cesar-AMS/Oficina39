// config.js

let profissionaisCadastrados = [];
let previewLogoTemporaria = '';
let previewQrTemporario = { qrcode1: '', qrcode2: '' };
const CHAVE_PROF_ENVIO_AUTO = 'config_profissional_envio_auto';
const BRANDING_LOGO_PADRAO = '/static/images/picapau4.png';
const BRANDING_QRCODE_1_PADRAO = '/static/images/qrcodewhatsapp.jpeg';
const BRANDING_QRCODE_2_PADRAO = '/static/images/qrcodeinstagram.jpeg';

function obterEscalaLogoBranding() {
    const valor = Number(getEl('logoIndexEscala')?.value || 100);
    return Math.min(300, Math.max(70, Number.isFinite(valor) ? valor : 100));
}

function obterOffsetLogoBranding(id) {
    const valor = Number(getEl(id)?.value || 0);
    return Math.min(30, Math.max(-30, Number.isFinite(valor) ? valor : 0));
}

function definirAjusteLogoBranding({ escala = 100, offsetX = 0, offsetY = 0 } = {}) {
    const campoEscala = getEl('logoIndexEscala');
    const campoOffsetX = getEl('logoIndexOffsetX');
    const campoOffsetY = getEl('logoIndexOffsetY');
    if (campoEscala) campoEscala.value = String(Math.min(300, Math.max(70, Number(escala) || 100)));
    if (campoOffsetX) campoOffsetX.value = String(Math.min(30, Math.max(-30, Number(offsetX) || 0)));
    if (campoOffsetY) campoOffsetY.value = String(Math.min(30, Math.max(-30, Number(offsetY) || 0)));
    atualizarPreviewBranding();
}

function centralizarLogoBranding() {
    definirAjusteLogoBranding({
        escala: obterEscalaLogoBranding(),
        offsetX: 0,
        offsetY: 0
    });
}

function resetarAjusteLogoBranding() {
    definirAjusteLogoBranding({ escala: 100, offsetX: 0, offsetY: 0 });
}

function aplicarPresetLogoBranding(preset) {
    const presets = {
        ajustado: { escala: 92, offsetX: 0, offsetY: 0 },
        maior: { escala: 108, offsetX: 0, offsetY: 0 },
        topo: { escala: 100, offsetX: 0, offsetY: -12 },
        base: { escala: 100, offsetX: 0, offsetY: 12 }
    };
    definirAjusteLogoBranding(presets[preset] || presets.ajustado);
}

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

function elementoVisivelParaEnter(el) {
    if (!el || el.disabled || el.hidden) return false;
    const style = window.getComputedStyle(el);
    return style.display !== 'none' && style.visibility !== 'hidden';
}

function focarProximoCampoConfig(atual) {
    const campos = Array.from(document.querySelectorAll(
        '.config-tab-panel input:not([type="hidden"]):not([type="file"]), .config-tab-panel select, .config-tab-panel textarea, .config-tab-panel button'
    )).filter((el) => elementoVisivelParaEnter(el) && !el.readOnly);
    const indice = campos.indexOf(atual);
    if (indice === -1) return false;
    for (let i = indice + 1; i < campos.length; i += 1) {
        const proximo = campos[i];
        if (!elementoVisivelParaEnter(proximo) || proximo.readOnly) continue;
        proximo.focus();
        if (typeof proximo.select === 'function' && proximo.tagName === 'INPUT') {
            proximo.select();
        }
        return true;
    }
    return false;
}

function configurarEnterConfiguracoes() {
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        const alvo = e.target;
        if (!(alvo instanceof HTMLElement)) return;
        if (alvo.tagName === 'TEXTAREA' || alvo.tagName === 'BUTTON') return;
        if (alvo.matches('input, select')) {
            e.preventDefault();
            focarProximoCampoConfig(alvo);
        }
    });
}

function reorganizarSecaoPersonalizacao() {
    const secao = getEl('secao-personalizacao-index');
    if (!secao) return;

    const topo = secao.querySelector('.config-row');
    const campoNome = getEl('nomeExibicaoSistema')?.closest('.form-group');
    if (topo) topo.classList.add('branding-top-row');
    if (campoNome) campoNome.classList.add('branding-top-field');

    const campoFormato = getEl('logoIndexFormato')?.closest('.form-group');
    const previewCard = secao.querySelector('.branding-preview-card');
    const previewFrame = getEl('brandingPreviewFrame');

    if (campoFormato && previewCard && previewFrame) {
        let toolbar = previewCard.querySelector('.branding-preview-toolbar');
        if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.className = 'branding-preview-toolbar';
            previewCard.insertBefore(toolbar, previewFrame);
        }

        let intro = toolbar.querySelector('.branding-preview-intro');
        if (!intro) {
            intro = document.createElement('div');
            intro.className = 'branding-preview-intro';
            toolbar.prepend(intro);
        }

        const labelPreview = Array.from(previewCard.children).find((elemento) =>
            elemento.classList?.contains('branding-preview-label')
        );
        if (labelPreview) {
            intro.prepend(labelPreview);
            labelPreview.textContent = 'Pré-visualização da logo';
        }

        if (labelPreview) labelPreview.textContent = 'Preview da logo';

        let helper = intro.querySelector('.branding-preview-helper');
        if (!helper) {
            helper = document.createElement('p');
            helper.className = 'branding-preview-helper';
            helper.textContent = 'Formato e imagem ficam juntos para facilitar o ajuste visual.';
            intro.appendChild(helper);
        }

        campoFormato.classList.add('branding-toolbar-field');
        toolbar.appendChild(campoFormato);
    }

    const gridUploadsQr = secao.querySelector('.branding-qrcode-grid');
    const gridPreviewsQr = secao.querySelector('.branding-qrcode-preview-grid');
    if (gridUploadsQr && gridPreviewsQr && !secao.querySelector('.branding-qrcode-pairs')) {
        const uploads = Array.from(gridUploadsQr.children);
        const previews = Array.from(gridPreviewsQr.children);
        const pares = document.createElement('div');
        pares.className = 'branding-qrcode-pairs';

        uploads.forEach((upload, index) => {
            const item = document.createElement('div');
            item.className = 'branding-qrcode-item';
            item.appendChild(upload);
            if (previews[index]) item.appendChild(previews[index]);
            pares.appendChild(item);
        });

        gridUploadsQr.replaceWith(pares);
        gridPreviewsQr.remove();
    }
}

function alternarAbaConfig(nomeAba) {
    document.querySelectorAll('.config-tab').forEach((aba) => {
        aba.classList.toggle('active', aba.dataset.tab === nomeAba);
    });
    document.querySelectorAll('.config-tab-panel').forEach((painel) => {
        painel.classList.toggle('active', painel.id === `configTab${nomeAba.charAt(0).toUpperCase()}${nomeAba.slice(1)}`);
    });
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

function formatarWhatsapp(valor) {
    const digitos = soDigitos(valor).slice(0, 13);
    if (!digitos) return '';
    if (digitos.length <= 2) return `+${digitos}`;
    if (digitos.length <= 4) return `+${digitos.slice(0, 2)} (${digitos.slice(2)}`;
    if (digitos.length <= 9) return `+${digitos.slice(0, 2)} (${digitos.slice(2, 4)}) ${digitos.slice(4)}`;
    return `+${digitos.slice(0, 2)} (${digitos.slice(2, 4)}) ${digitos.slice(4, 9)}-${digitos.slice(9)}`;
}

function atualizarPreviewBranding() {
    const frame = getEl('brandingPreviewFrame');
    const imagem = getEl('brandingPreviewImage');
    const legenda = getEl('brandingPreviewCaption');
    if (!frame || !imagem || !legenda) return;

    const formato = (getEl('logoIndexFormato')?.value || 'circulo').trim() || 'circulo';
    const logoPath = previewLogoTemporaria || (getEl('logoIndexPath')?.value || '').trim() || BRANDING_LOGO_PADRAO;
    const escala = obterEscalaLogoBranding();
    const offsetX = obterOffsetLogoBranding('logoIndexOffsetX');
    const offsetY = obterOffsetLogoBranding('logoIndexOffsetY');
    const nome = (getEl('nomeExibicaoSistema')?.value || '').trim()
        || (getEl('empresaNome')?.value || '').trim()
        || 'Sistema de Gerenciamento Oficina 39';
    const empresaNome = (getEl('empresaNome')?.value || '').trim() || 'Oficina 39';
    const empresaTelefone = (getEl('empresaTelefone')?.value || '').trim() || '(11) 99209-2341';
    const empresaEmail = (getEl('empresaEmail')?.value || '').trim() || 'oficina39ca@gmail.com';
    const empresaNomePreview = getEl('brandingPreviewCompanyName');
    const empresaContatoPreview = getEl('brandingPreviewCompanyContact');
    const empresaEmailPreview = getEl('brandingPreviewCompanyEmail');
    const qr1 = getEl('brandingPreviewQr1');
    const qr2 = getEl('brandingPreviewQr2');
    const escalaBadge = getEl('brandingEscalaBadge');

    frame.classList.toggle('circulo', formato === 'circulo');
    frame.classList.toggle('quadrado', formato === 'quadrado');
    frame.style.setProperty('--branding-logo-scale', (escala / 100).toFixed(2));
    frame.style.setProperty('--branding-logo-offset-x', `${offsetX}%`);
    frame.style.setProperty('--branding-logo-offset-y', `${offsetY}%`);
    imagem.src = logoPath;
    legenda.textContent = nome;
    if (escalaBadge) escalaBadge.textContent = `${escala}%`;
    if (empresaNomePreview) empresaNomePreview.textContent = empresaNome;
    if (empresaContatoPreview) empresaContatoPreview.textContent = empresaTelefone;
    if (empresaEmailPreview) empresaEmailPreview.textContent = empresaEmail;
    if (qr1) qr1.src = previewQrTemporario.qrcode1 || (getEl('qrcode1Path')?.value || '').trim() || BRANDING_QRCODE_1_PADRAO;
    if (qr2) qr2.src = previewQrTemporario.qrcode2 || (getEl('qrcode2Path')?.value || '').trim() || BRANDING_QRCODE_2_PADRAO;
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
    if (config.senha_app) getEl('senhaApp').value = config.senha_app;
    if (config.email_contador) getEl('emailContador').value = config.email_contador;
    if (config.frequencia) getEl('frequenciaEnvio').value = config.frequencia;
    if (config.dia_envio) getEl('diaEnvio').value = config.dia_envio;
    if (config.ativo !== undefined) getEl('envioAtivo').checked = config.ativo;
    if (config.cep_provider_ativo) getEl('cepProviderAtivo').value = config.cep_provider_ativo;
    if (config.cep_provider_primario) getEl('cepProviderPrimario').value = config.cep_provider_primario;
    if (config.cep_api_key_primaria) getEl('cepApiKeyPrimaria').value = config.cep_api_key_primaria;
    if (config.cep_provider_secundario) getEl('cepProviderSecundario').value = config.cep_provider_secundario;
    if (config.cep_api_key_secundaria) getEl('cepApiKeySecundaria').value = config.cep_api_key_secundaria;
    if (config.placa_provider_ativo) getEl('placaProviderAtivo').value = config.placa_provider_ativo;
    if (config.placa_provider_primario) getEl('placaProviderPrimario').value = config.placa_provider_primario;
    if (config.placa_api_key_primaria) getEl('placaApiKeyPrimaria').value = config.placa_api_key_primaria;
    if (config.placa_provider_secundario) getEl('placaProviderSecundario').value = config.placa_provider_secundario;
    if (config.placa_api_key_secundaria) getEl('placaApiKeySecundaria').value = config.placa_api_key_secundaria;
    if (config.whatsapp_orcamento) getEl('whatsappOrcamento').value = formatarWhatsapp(config.whatsapp_orcamento);
    if (config.nome_exibicao_sistema) getEl('nomeExibicaoSistema').value = config.nome_exibicao_sistema;
    if (config.empresa_nome) getEl('empresaNome').value = config.empresa_nome;
    if (config.empresa_email) getEl('empresaEmail').value = config.empresa_email;
    if (config.empresa_telefone) getEl('empresaTelefone').value = config.empresa_telefone;
    if (config.empresa_endereco) getEl('empresaEndereco').value = config.empresa_endereco;
    if (config.logo_index_path) getEl('logoIndexPath').value = config.logo_index_path;
    if (config.logo_index_formato) getEl('logoIndexFormato').value = config.logo_index_formato;
    if (config.logo_index_escala) getEl('logoIndexEscala').value = Math.round(Number(config.logo_index_escala) * 100);
    if (config.logo_index_offset_x != null) getEl('logoIndexOffsetX').value = Math.round(Number(config.logo_index_offset_x));
    if (config.logo_index_offset_y != null) getEl('logoIndexOffsetY').value = Math.round(Number(config.logo_index_offset_y));
    if (config.qrcode_1_path) getEl('qrcode1Path').value = config.qrcode_1_path;
    if (config.qrcode_2_path) getEl('qrcode2Path').value = config.qrcode_2_path;
    atualizarPreviewBranding();

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
        ativo: getEl('envioAtivo').checked,
        cep_provider_ativo: (getEl('cepProviderAtivo')?.value || '').trim(),
        cep_provider_primario: (getEl('cepProviderPrimario')?.value || '').trim(),
        cep_api_key_primaria: (getEl('cepApiKeyPrimaria')?.value || '').trim(),
        cep_provider_secundario: (getEl('cepProviderSecundario')?.value || '').trim(),
        cep_api_key_secundaria: (getEl('cepApiKeySecundaria')?.value || '').trim(),
        placa_provider_ativo: (getEl('placaProviderAtivo')?.value || '').trim(),
        placa_provider_primario: (getEl('placaProviderPrimario')?.value || '').trim(),
        placa_api_key_primaria: (getEl('placaApiKeyPrimaria')?.value || '').trim(),
        placa_provider_secundario: (getEl('placaProviderSecundario')?.value || '').trim(),
        placa_api_key_secundaria: (getEl('placaApiKeySecundaria')?.value || '').trim(),
        whatsapp_orcamento: soDigitos(getEl('whatsappOrcamento')?.value || ''),
        nome_exibicao_sistema: (getEl('nomeExibicaoSistema')?.value || '').trim(),
        empresa_nome: (getEl('empresaNome')?.value || '').trim(),
        empresa_email: (getEl('empresaEmail')?.value || '').trim(),
        empresa_telefone: (getEl('empresaTelefone')?.value || '').trim(),
        empresa_endereco: (getEl('empresaEndereco')?.value || '').trim(),
        logo_index_path: (getEl('logoIndexPath')?.value || '').trim(),
        logo_index_formato: (getEl('logoIndexFormato')?.value || 'circulo').trim(),
        logo_index_escala: obterEscalaLogoBranding() / 100,
        logo_index_offset_x: obterOffsetLogoBranding('logoIndexOffsetX'),
        logo_index_offset_y: obterOffsetLogoBranding('logoIndexOffsetY'),
        qrcode_1_path: (getEl('qrcode1Path')?.value || '').trim(),
        qrcode_2_path: (getEl('qrcode2Path')?.value || '').trim()
    };

    try {
        await requestJson('/api/config/contador', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const profissionalEnvio = (getEl('profissionalEnvioAuto')?.value || '').trim();
        localStorage.setItem(CHAVE_PROF_ENVIO_AUTO, profissionalEnvio);
        alertSucesso('Configurações salvas com sucesso.');
        carregarHistorico();
    } catch (error) {
        alertErro(error.message);
    }
}

async function salvarPersonalizacao() {
    try {
        await persistirPersonalizacaoAtual();
        alertSucesso('Personalização salva com sucesso.');
    } catch (error) {
        alertErro(error.message);
    }
}

function montarPayloadPersonalizacao() {
    return {
        nome_exibicao_sistema: (getEl('nomeExibicaoSistema')?.value || '').trim(),
        empresa_nome: (getEl('empresaNome')?.value || '').trim(),
        empresa_email: (getEl('empresaEmail')?.value || '').trim(),
        empresa_telefone: (getEl('empresaTelefone')?.value || '').trim(),
        empresa_endereco: (getEl('empresaEndereco')?.value || '').trim(),
        logo_index_path: (getEl('logoIndexPath')?.value || '').trim(),
        logo_index_formato: (getEl('logoIndexFormato')?.value || 'circulo').trim(),
        logo_index_escala: obterEscalaLogoBranding() / 100,
        logo_index_offset_x: obterOffsetLogoBranding('logoIndexOffsetX'),
        logo_index_offset_y: obterOffsetLogoBranding('logoIndexOffsetY'),
        qrcode_1_path: (getEl('qrcode1Path')?.value || '').trim(),
        qrcode_2_path: (getEl('qrcode2Path')?.value || '').trim()
    };
}

async function persistirPersonalizacaoAtual() {
    return requestJson('/api/config/contador', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(montarPayloadPersonalizacao())
    });
}

async function enviarLogoIndex() {
    await enviarArquivoBranding('logo');
}

async function enviarQrCode(slot) {
    await enviarArquivoBranding(slot);
}

async function enviarArquivoBranding(destino) {
    const mapa = {
        logo: { input: 'logoIndexArquivo', path: 'logoIndexPath', mensagem: 'Imagem enviada. Agora salve a personalização para aplicar na tela inicial.' },
        qrcode1: { input: 'qrcode1Arquivo', path: 'qrcode1Path', mensagem: 'QR Code 1 enviado. Agora salve a personalização para aplicar na nota.' },
        qrcode2: { input: 'qrcode2Arquivo', path: 'qrcode2Path', mensagem: 'QR Code 2 enviado. Agora salve a personalização para aplicar na nota.' }
    };
    const config = mapa[destino];
    const inputArquivo = getEl(config?.input);
    if (!inputArquivo?.files?.length) {
        alertErro('Selecione uma imagem antes de enviar.');
        return;
    }

    const formData = new FormData();
    formData.append('arquivo', inputArquivo.files[0]);
    formData.append('destino', destino);

    try {
        const response = await fetch('/api/config/branding/logo-upload', {
            method: 'POST',
            body: formData
        });
        const dados = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(dados.erro || 'Falha ao enviar a imagem.');
        }

        const pathField = getEl(config.path);
        if (pathField) {
            pathField.value = dados.arquivo_path || dados.logo_index_path || dados.qrcode_1_path || dados.qrcode_2_path || '';
        }
        if (destino === 'logo') {
            previewLogoTemporaria = '';
        } else {
            previewQrTemporario[destino] = '';
        }
        atualizarPreviewBranding();
        await persistirPersonalizacaoAtual();
        inputArquivo.value = '';
        alertSucesso(`${config.mensagem} A imagem já foi aplicada no sistema.`);
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
                    Remover
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
    reorganizarSecaoPersonalizacao();
    alternarAbaConfig('geral');
    configurarEnterConfiguracoes();
    carregarConfig();
    carregarHistorico();
    carregarProfissionaisCadastrados();

    const whatsappInput = getEl('whatsappOrcamento');
    if (whatsappInput) {
        whatsappInput.addEventListener('input', () => {
            whatsappInput.value = formatarWhatsapp(whatsappInput.value);
        });
    }

    const nomeExibicaoInput = getEl('nomeExibicaoSistema');
    if (nomeExibicaoInput) {
        nomeExibicaoInput.addEventListener('input', atualizarPreviewBranding);
    }

    ['empresaNome', 'empresaEmail', 'empresaTelefone'].forEach((id) => {
        const campo = getEl(id);
        if (campo) campo.addEventListener('input', atualizarPreviewBranding);
    });

    const formatoLogoSelect = getEl('logoIndexFormato');
    if (formatoLogoSelect) {
        formatoLogoSelect.addEventListener('change', atualizarPreviewBranding);
    }
    const escalaLogoInput = getEl('logoIndexEscala');
    if (escalaLogoInput) {
        escalaLogoInput.addEventListener('input', atualizarPreviewBranding);
        escalaLogoInput.addEventListener('change', atualizarPreviewBranding);
    }
    const offsetXInput = getEl('logoIndexOffsetX');
    if (offsetXInput) {
        offsetXInput.addEventListener('input', atualizarPreviewBranding);
        offsetXInput.addEventListener('change', atualizarPreviewBranding);
    }
    const offsetYInput = getEl('logoIndexOffsetY');
    if (offsetYInput) {
        offsetYInput.addEventListener('input', atualizarPreviewBranding);
        offsetYInput.addEventListener('change', atualizarPreviewBranding);
    }

    const arquivoLogoInput = getEl('logoIndexArquivo');
    if (arquivoLogoInput) {
        arquivoLogoInput.addEventListener('change', () => {
            const arquivo = arquivoLogoInput.files?.[0];
            if (!arquivo) return;
            const reader = new FileReader();
            reader.onload = (evento) => {
                const imagem = getEl('brandingPreviewImage');
                previewLogoTemporaria = evento.target?.result || '';
                if (imagem) imagem.src = previewLogoTemporaria || BRANDING_LOGO_PADRAO;
            };
            reader.readAsDataURL(arquivo);
        });
    }

    ['qrcode1', 'qrcode2'].forEach((slot) => {
        const input = getEl(`${slot}Arquivo`);
        const previewId = slot === 'qrcode1' ? 'brandingPreviewQr1' : 'brandingPreviewQr2';
        input?.addEventListener('change', () => {
            const arquivo = input.files?.[0];
            if (!arquivo) return;
            const reader = new FileReader();
            reader.onload = (evento) => {
                const imagem = getEl(previewId);
                previewQrTemporario[slot] = evento.target?.result || '';
                if (imagem) imagem.src = previewQrTemporario[slot] || (slot === 'qrcode1' ? BRANDING_QRCODE_1_PADRAO : BRANDING_QRCODE_2_PADRAO);
            };
            reader.readAsDataURL(arquivo);
        });
    });

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

window.centralizarLogoBranding = centralizarLogoBranding;
window.resetarAjusteLogoBranding = resetarAjusteLogoBranding;
window.aplicarPresetLogoBranding = aplicarPresetLogoBranding;

window.salvarConfig = salvarConfig;
window.cadastrarProfissional = cadastrarProfissional;
window.removerProfissional = removerProfissional;
window.mascararCnpjEnvio = mascararCnpjEnvio;
window.validarCnpjCampo = validarCnpjCampo;
window.exportarDados = exportarDados;
window.importarDados = importarDados;
window.alternarAbaConfig = alternarAbaConfig;
window.enviarLogoIndex = enviarLogoIndex;
window.enviarQrCode = enviarQrCode;
window.salvarPersonalizacao = salvarPersonalizacao;

