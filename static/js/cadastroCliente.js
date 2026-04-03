// cadastroCliente.js - Cadastro e edição de cliente

let clienteEdicaoId = null;
let wizardStep = 1;
const WIZARD_STEPS = 3;

function alertErro(mensagem) {
    if (window.ui) return window.ui.error(mensagem);
    alert(`Erro: ${mensagem}`);
}

function alertSucesso(mensagem) {
    if (window.ui) return window.ui.success(mensagem);
    alert(`Sucesso: ${mensagem}`);
}

function validarCPF(cpf) {
    cpf = (cpf || '').replace(/[^\d]/g, '');
    if (cpf.length !== 11) return false;
    if (/^(\d)\1+$/.test(cpf)) return false;

    let soma = 0;
    for (let i = 0; i < 9; i++) soma += parseInt(cpf.charAt(i), 10) * (10 - i);
    let resto = 11 - (soma % 11);
    let digito1 = (resto === 10 || resto === 11) ? 0 : resto;
    if (digito1 !== parseInt(cpf.charAt(9), 10)) return false;

    soma = 0;
    for (let i = 0; i < 10; i++) soma += parseInt(cpf.charAt(i), 10) * (11 - i);
    resto = 11 - (soma % 11);
    let digito2 = (resto === 10 || resto === 11) ? 0 : resto;
    return digito2 === parseInt(cpf.charAt(10), 10);
}

function obterClienteFormulario() {
    const cpf = document.getElementById('cpf')?.value || '';
    return {
        nome_cliente: (document.getElementById('nome_cliente')?.value || '').trim(),
        cpf: cpf.replace(/[^\d]/g, ''),
        telefone: document.getElementById('telefone')?.value || '',
        email: document.getElementById('email')?.value || '',
        endereco: document.getElementById('endereco')?.value || '',
        cidade: document.getElementById('cidade')?.value || '',
        estado: document.getElementById('estado')?.value || '',
        cep: document.getElementById('cep')?.value || '',
        placa: document.getElementById('placa')?.value || '',
        fabricante: document.getElementById('fabricante')?.value || '',
        modelo: document.getElementById('modelo')?.value || '',
        ano: document.getElementById('ano')?.value || '',
        motor: document.getElementById('motor')?.value || '',
        combustivel: document.getElementById('combustivel')?.value || '',
        cor: document.getElementById('cor')?.value || '',
        tanque: document.getElementById('tanque')?.value || '',
        km: document.getElementById('km')?.value ? parseInt(document.getElementById('km').value, 10) : 0,
        direcao: document.getElementById('direcao')?.value || '',
        ar: document.getElementById('ar')?.value || ''
    };
}

function preencherFormularioCliente(cliente) {
    const campos = ['nome_cliente', 'cpf', 'telefone', 'email', 'endereco', 'cidade', 'estado', 'cep', 'placa', 'fabricante', 'modelo', 'ano', 'motor', 'combustivel', 'cor', 'tanque', 'km', 'direcao', 'ar'];
    campos.forEach((campo) => {
        const el = document.getElementById(campo);
        if (el) el.value = cliente?.[campo] ?? '';
    });
}

function destinoPosEdicao() {
    return clienteEdicaoId ? '/consultarOS.html' : '/';
}

function voltarTelaCliente() {
    window.location.assign(destinoPosEdicao());
}

function executarAoPressionarEnter(campo, callback) {
    if (!campo) return;
    campo.addEventListener('keydown', function(e) {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        callback();
    });
}

function elementoVisivelParaEnter(el) {
    if (!el || el.disabled || el.hidden) return false;
    const style = window.getComputedStyle(el);
    return style.display !== 'none' && style.visibility !== 'hidden';
}

function focarProximoCampoCadastro(atual) {
    const campos = Array.from(document.querySelectorAll(
        '.step-content input:not([type="hidden"]), .step-content select, .step-content textarea, .step-content button'
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

function configurarEnterCadastroCliente() {
    document.addEventListener('keydown', function(e) {
        if (e.key !== 'Enter') return;
        const alvo = e.target;
        if (!(alvo instanceof HTMLElement)) return;
        if (alvo.tagName === 'TEXTAREA' || alvo.tagName === 'BUTTON') return;
        if (alvo.id === 'placa' || alvo.id === 'cep') return;
        if (alvo.matches('input, select')) {
            e.preventDefault();
            focarProximoCampoCadastro(alvo);
        }
    });
}

async function buscarCep() {
    const cepInput = document.getElementById('cep');
    const enderecoInput = document.getElementById('endereco');
    const cidadeInput = document.getElementById('cidade');
    const estadoInput = document.getElementById('estado');
    const cep = (cepInput?.value || '').replace(/\D/g, '');

    if (cep.length !== 8) {
        alertErro('Informe um CEP válido com 8 dígitos.');
        cepInput?.focus();
        return;
    }

    try {
        const response = await fetch(`/api/integracoes/cep/${cep}`);
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Falha ao consultar CEP.');

        if (cepInput) cepInput.value = dados.cep || cepInput.value;
        if (enderecoInput) {
            const partesEndereco = [dados.logradouro, dados.bairro].filter(Boolean);
            enderecoInput.value = partesEndereco.join(' - ') || enderecoInput.value;
        }
        if (cidadeInput) cidadeInput.value = dados.cidade || cidadeInput.value;
        if (estadoInput) estadoInput.value = dados.estado || estadoInput.value;

        alertSucesso(`CEP localizado via ${dados.fonte}.`);
    } catch (error) {
        alertErro(`${error.message} Você pode continuar com preenchimento manual.`);
    }
}

function preencherDadosVeiculo(dados) {
    // Preencher apenas campos do veículo (não sobrescrever dados do cliente ou endereço)
    const mapeamento = {
        placa: 'placa',
        fabricante: 'fabricante',
        modelo: 'modelo',
        ano: 'ano',
        cor: 'cor',
        combustivel: 'combustivel',
        motor: 'motor',
        tanque: 'tanque',
        km: 'km',
        direcao: 'direcao',
        ar: 'ar'
    };
    Object.entries(mapeamento).forEach(([origem, destino]) => {
        const campo = document.getElementById(destino);
        if (campo && (dados[origem] !== undefined && dados[origem] !== null)) campo.value = dados[origem];
    });
}

/* ====== WIZARD: gerenciamento de passos, validação e saves parciais ====== */
function showStep(n) {
    wizardStep = n;
    document.querySelectorAll('.step-content').forEach(el => {
        el.style.display = Number(el.getAttribute('data-step')) === n ? '' : 'none';
    });
    document.querySelectorAll('#stepper .step').forEach(el => {
        const s = Number(el.getAttribute('data-step'));
        el.classList.toggle('active', s === n);
        el.classList.toggle('completed', s < n);
    });
    document.getElementById('btnVoltar').style.display = n > 1 ? '' : 'none';
    document.getElementById('btnAvancar').style.display = n < WIZARD_STEPS ? '' : 'none';
    document.getElementById('btnSalvarCliente').style.display = n === WIZARD_STEPS ? '' : 'none';
}

function wizardPrev() {
    if (wizardStep > 1) showStep(wizardStep - 1);
}

async function wizardNext() {
    // valida o passo atual antes de avançar
    const ok = await validateAndSaveStep(wizardStep);
    if (!ok) return;
    if (wizardStep < WIZARD_STEPS) showStep(wizardStep + 1);
}

async function validateAndSaveStep(step) {
    try {
        if (step === 1) {
            // Step 1: vehicle data. Plate is optional. If provided, try to query external API to fill vehicle fields.
            const placa = (document.getElementById('placa')?.value || '').trim();
            if (placa) {
                try {
                    const response = await fetch(`/api/integracoes/placa/${encodeURIComponent(placa)}`);
                    const dados = await response.json();
                    if (response.ok) {
                        // Only fill vehicle fields. If the API returns cliente_id, keep it to support editing but do not auto-fill client inputs.
                        preencherDadosVeiculo(dados);
                        if (dados.cliente_id) clienteEdicaoId = dados.cliente_id;
                    }
                } catch (e) {
                    // consulta externa falhou, não bloqueia
                }
            }
            // Salva apenas os campos do veículo como rascunho
            const payload = {
                placa: document.getElementById('placa')?.value || '',
                fabricante: document.getElementById('fabricante')?.value || '',
                modelo: document.getElementById('modelo')?.value || '',
                ano: document.getElementById('ano')?.value || '',
                cor: document.getElementById('cor')?.value || '',
                motor: document.getElementById('motor')?.value || '',
                combustivel: document.getElementById('combustivel')?.value || '',
                tanque: document.getElementById('tanque')?.value || '',
                km: document.getElementById('km')?.value ? parseInt(document.getElementById('km').value, 10) : 0,
                direcao: document.getElementById('direcao')?.value || '',
                ar: document.getElementById('ar')?.value || ''
            };
            if (clienteEdicaoId) payload.id = clienteEdicaoId;
            await saveDraft(payload);
            return true;
        }
        if (step === 2) {
            // Validações do cliente: nome e contato obrigatórios
            const nome = (document.getElementById('nome_cliente')?.value || '').trim();
            const telefone = (document.getElementById('telefone')?.value || '').trim();
            if (!nome) {
                alertErro('Nome do cliente é obrigatório para prosseguir.');
                document.getElementById('nome_cliente')?.focus();
                return false;
            }
            if (!telefone) {
                alertErro('Contato (telefone) é obrigatório para prosseguir.');
                document.getElementById('telefone')?.focus();
                return false;
            }
            // salva rascunho (cliente)
            const payloadCliente = {
                nome_cliente: document.getElementById('nome_cliente')?.value || '',
                cpf: (document.getElementById('cpf')?.value || '').replace(/\D/g, ''),
                telefone: document.getElementById('telefone')?.value || '',
                email: document.getElementById('email')?.value || ''
            };
            if (clienteEdicaoId) payloadCliente.id = clienteEdicaoId;
            await saveDraft(payloadCliente);
            return true;
        }
        if (step === 3) {
            // Validação mínima de endereço: rua/cidade/estado ou busca por CEP
            const endereco = (document.getElementById('endereco')?.value || '').trim();
            const cidade = (document.getElementById('cidade')?.value || '').trim();
            const estado = (document.getElementById('estado')?.value || '').trim();
            const cep = (document.getElementById('cep')?.value || '').replace(/\D/g, '');
            if (!cep && (!endereco || !cidade || !estado)) {
                alertErro('Preencha CEP ou endereço, cidade e estado antes de concluir.');
                return false;
            }
            // salva apenas os campos de endereço
            const payloadEndereco = {
                endereco: document.getElementById('endereco')?.value || '',
                cidade: document.getElementById('cidade')?.value || '',
                estado: document.getElementById('estado')?.value || '',
                cep: document.getElementById('cep')?.value || ''
            };
            if (clienteEdicaoId) payloadEndereco.id = clienteEdicaoId;
            await saveDraft(payloadEndereco);
            return true;
        }
        return true;
    } catch (e) {
        alertErro('Erro durante validação: ' + (e.message || e));
        return false;
    }
}

async function saveDraft() {
    // saveDraft can receive an optional payload argument (partial data). If none provided, fall back to full form.
    const args = Array.from(arguments);
    const provided = args[0];
    const payload = provided || obterClienteFormulario();
    try {
        const resp = await fetch('/api/clientes/draft', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.erro || 'Falha ao salvar rascunho');
        clienteEdicaoId = data.id;
        return true;
    } catch (err) {
        console.error('Erro ao salvar rascunho', err);
        alertErro('Não foi possível salvar rascunho localmente. Você pode prosseguir, mas seu progresso não será salvo.');
        return false;
    }
}

async function salvarFinal() {
    // valida todos os passos antes de enviar final
    for (let s = 1; s <= WIZARD_STEPS; s++) {
        const ok = await validateAndSaveStep(s);
        if (!ok) return;
    }
    // Ao final, reuse a função salvar() padrão para submissão final (que faz validações completas)
    salvar();
}

async function consultarPlaca() {
    const placaInput = document.getElementById('placa');
    const placa = (placaInput?.value || '').trim();
    if (!placa) {
        alertErro('Informe uma placa para consulta.');
        placaInput?.focus();
        return;
    }

    try {
        const response = await fetch(`/api/integracoes/placa/${encodeURIComponent(placa)}`);
        const dados = await response.json();
        if (!response.ok) throw new Error(dados.erro || 'Falha ao consultar placa.');

        preencherDadosVeiculo(dados);
        const mensagemFonte = dados.fonte === 'cadastro_local'
            ? 'Cadastro local encontrado pela placa. Dados do cliente e do veículo foram sugeridos.'
            : `Consulta realizada via ${dados.fonte}. Dados do veículo foram preenchidos quando disponíveis.`;
        alertSucesso(mensagemFonte);
    } catch (error) {
        alertErro(`${error.message} Você pode preencher os dados do veículo manualmente.`);
    }
}

async function carregarClienteEdicao() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    if (!id) return;

    clienteEdicaoId = id;
    try {
        const response = await fetch(`/api/clientes/${id}`);
        const cliente = await response.json();
        if (!response.ok) throw new Error(cliente.erro || 'Cliente não encontrado.');
        preencherFormularioCliente(cliente);

        document.getElementById('tituloCadastroCliente').textContent = 'Editar Cadastro';
        document.getElementById('subtituloCadastroCliente').textContent = `Ajuste os dados do cadastro #${id}.`;
        document.getElementById('btnSalvarCliente').textContent = '✓ Salvar Alterações';
    } catch (error) {
        alertErro(error.message);
    }
}

async function salvar() {
    const cliente = obterClienteFormulario();

    if (!cliente.nome_cliente) {
        alertErro('Nome é obrigatório!');
        document.getElementById('nome_cliente')?.focus();
        return;
    }

    if (!cliente.cpf) {
        alertErro('CPF é obrigatório!');
        document.getElementById('cpf')?.focus();
        return;
    }

    if (cliente.cpf.length !== 11) {
        alertErro('CPF deve ter 11 dígitos!');
        document.getElementById('cpf')?.focus();
        return;
    }

    if (!validarCPF(cliente.cpf)) {
        alertErro('CPF inválido!');
        document.getElementById('cpf')?.focus();
        return;
    }

    if (!clienteEdicaoId) {
        try {
            const checkResponse = await fetch(`/api/clientes/busca?termo=${cliente.cpf}`);
            const checkData = await checkResponse.json();
            if (checkData.length > 0 && checkData[0].cpf === cliente.cpf) {
                alertErro('CPF já cadastrado!');
                document.getElementById('cpf')?.focus();
                return;
            }
        } catch (error) {
            console.log('Erro ao verificar CPF, continuando...');
        }
    }

    try {
        const response = await fetch(clienteEdicaoId ? `/api/clientes/${clienteEdicaoId}` : '/api/clientes/', {
            method: clienteEdicaoId ? 'PUT' : 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cliente)
        });

        const resultado = await response.json();
        if (!response.ok) {
            alertErro(resultado.erro || 'Erro desconhecido');
            return;
        }

        alertSucesso(clienteEdicaoId ? 'Cliente atualizado com sucesso!' : 'Cliente cadastrado com sucesso!');
        if (clienteEdicaoId) {
            window.location.assign('/consultarOS.html');
            return;
        }
        limparFormularioCadastro();
    } catch (error) {
        alertErro('Erro de conexão com o servidor!');
        console.error('Erro:', error);
    }
}

async function cancelar() {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Deseja realmente cancelar? Os dados não serão salvos.')
        : (window.ui ? window.ui.confirm('Deseja realmente cancelar? Os dados não serão salvos.') : confirm('Deseja realmente cancelar? Os dados não serão salvos.'));
    if (!confirmado) return;
    window.location.assign('/');
}

function limparFormularioCadastro() {
    const campos = ['nome_cliente', 'cpf', 'telefone', 'email', 'endereco', 'cidade', 'estado', 'cep', 'placa', 'fabricante', 'modelo', 'ano', 'motor', 'combustivel', 'cor', 'tanque', 'km', 'direcao', 'ar'];
    campos.forEach((id) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.value = '';
        el.style.borderColor = '';
    });
    document.getElementById('placa')?.focus();
}

document.addEventListener('DOMContentLoaded', function() {
    carregarClienteEdicao();
    configurarEnterCadastroCliente();

    const campoCPF = document.getElementById('cpf');
    if (campoCPF) {
        campoCPF.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                if (value.length > 9) value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
                else if (value.length > 6) value = value.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
                else if (value.length > 3) value = value.replace(/(\d{3})(\d{1,3})/, '$1.$2');
                e.target.value = value;
            }

            const cpfLimpo = value.replace(/\D/g, '');
            if (cpfLimpo.length === 11) {
                e.target.style.borderColor = validarCPF(cpfLimpo) ? '#2c7a4d' : '#a03232';
            } else {
                e.target.style.borderColor = '';
            }
        });
    }

    const campoPlaca = document.getElementById('placa');
    if (campoPlaca) {
        campoPlaca.addEventListener('input', function(e) {
            let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
            if (value.length <= 7) {
                if (value.length > 3) value = value.substring(0, 3) + '-' + value.substring(3);
                e.target.value = value;
            }
        });
        executarAoPressionarEnter(campoPlaca, consultarPlaca);
        campoPlaca.addEventListener('blur', function() {
            const valor = campoPlaca.value.trim();
            if (valor.length >= 7 && !clienteEdicaoId) {
                consultarPlaca();
            }
        });
    }

    const campoKM = document.getElementById('km');
    if (campoKM) {
        campoKM.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    }

    const campoAno = document.getElementById('ano');
    if (campoAno) {
        campoAno.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/[^\d\/]/g, '');
        });
    }

    const campoCep = document.getElementById('cep');
    if (campoCep) {
        campoCep.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '').slice(0, 8);
            if (value.length > 5) value = `${value.slice(0, 5)}-${value.slice(5)}`;
            e.target.value = value;
        });
        executarAoPressionarEnter(campoCep, buscarCep);
        campoCep.addEventListener('blur', function() {
            const valor = (campoCep.value || '').replace(/\D/g, '');
            if (valor.length === 8) buscarCep();
        });
    }

    if (!clienteEdicaoId) {
        document.getElementById('placa')?.focus();
    }
    // inicializa stepper
    showStep(1);
});

document.addEventListener('keydown', function(e) {
    if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        salvar();
    }
    if (e.key === 'Escape') cancelar();
});

window.voltarTelaCliente = voltarTelaCliente;
window.buscarCep = buscarCep;
window.consultarPlaca = consultarPlaca;
