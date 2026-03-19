// cadastroCliente.js - Cadastro e edição de cliente

let clienteEdicaoId = null;

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
    window.location.href = destinoPosEdicao();
}

function executarAoPressionarEnter(campo, callback) {
    if (!campo) return;
    campo.addEventListener('keydown', function(e) {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        callback();
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
    const mapeamento = {
        placa: 'placa',
        nome_cliente: 'nome_cliente',
        cpf: 'cpf',
        telefone: 'telefone',
        email: 'email',
        endereco: 'endereco',
        cidade: 'cidade',
        estado: 'estado',
        cep: 'cep',
        fabricante: 'fabricante',
        modelo: 'modelo',
        ano: 'ano',
        cor: 'cor',
        combustivel: 'combustivel',
        motor: 'motor'
    };
    Object.entries(mapeamento).forEach(([origem, destino]) => {
        const campo = document.getElementById(destino);
        if (campo && dados[origem]) campo.value = dados[origem];
    });
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

        document.getElementById('tituloCadastroCliente').textContent = '✏️ Editar Cadastro';
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
            window.location.href = '/consultarOS.html';
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
    voltarTelaCliente();
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
