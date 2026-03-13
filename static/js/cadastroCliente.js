// cadastroCliente.js - Versão CORRIGIDA com validação de CPF

// ===========================================
// FUNÇÃO DE VALIDAÇÃO DE CPF
// ===========================================
function validarCPF(cpf) {
    cpf = cpf.replace(/[^\d]/g, '');
    
    if (cpf.length !== 11) return false;
    
    // Verifica se todos os dígitos são iguais (CPF inválido)
    if (/^(\d)\1+$/.test(cpf)) return false;
    
    // Validação do primeiro dígito verificador
    let soma = 0;
    for (let i = 0; i < 9; i++) {
        soma += parseInt(cpf.charAt(i)) * (10 - i);
    }
    let resto = 11 - (soma % 11);
    let digito1 = (resto === 10 || resto === 11) ? 0 : resto;
    
    if (digito1 !== parseInt(cpf.charAt(9))) return false;
    
    // Validação do segundo dígito verificador
    soma = 0;
    for (let i = 0; i < 10; i++) {
        soma += parseInt(cpf.charAt(i)) * (11 - i);
    }
    resto = 11 - (soma % 11);
    let digito2 = (resto === 10 || resto === 11) ? 0 : resto;
    
    return digito2 === parseInt(cpf.charAt(10));
}

/// ===========================================
// FUNÇÃO PARA SALVAR CLIENTE (CORRIGIDA)
// ===========================================
async function salvar() {
    // PEGAR VALORES
    const nome = document.getElementById('nome_cliente')?.value;
    const cpf = document.getElementById('cpf')?.value;
    const cpfLimpo = cpf ? cpf.replace(/[^\d]/g, '') : '';

    // VALIDAR NOME
    if (!nome || nome.trim() === '') {
        alert('❌ Nome é obrigatório!');
        document.getElementById('nome_cliente')?.focus();
        return;
    }

    // VALIDAR CPF
    if (!cpfLimpo) {
        alert('❌ CPF é obrigatório!');
        document.getElementById('cpf')?.focus();
        return;
    }

    if (cpfLimpo.length !== 11) {
        alert('❌ CPF deve ter 11 dígitos!');
        document.getElementById('cpf')?.focus();
        return;
    }

    if (!validarCPF(cpf)) {
        alert('❌ CPF inválido!');
        document.getElementById('cpf')?.focus();
        return;
    }

    // VERIFICAR SE JÁ EXISTE
    try {
        const checkResponse = await fetch(`/api/clientes/busca?termo=${cpfLimpo}`);
        const checkData = await checkResponse.json();
        
        if (checkData.length > 0 && checkData[0].cpf === cpfLimpo) {
            alert('❌ CPF já cadastrado!');
            document.getElementById('cpf')?.focus();
            return;
        }
    } catch (error) {
        console.log('Erro ao verificar CPF, continuando...');
    }

    // ===== CRIAR OBJETO CLIENTE COM TODOS OS CAMPOS =====
    const cliente = {
        nome_cliente: nome.trim(),
        cpf: cpfLimpo,
        
        // ===== NOVOS CAMPOS ADICIONADOS =====
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
        km: document.getElementById('km')?.value ? parseInt(document.getElementById('km').value) : 0,
        direcao: document.getElementById('direcao')?.value || '',
        ar: document.getElementById('ar')?.value || ''
    };

    try {
        const response = await fetch('/api/clientes/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cliente)
        });

        const resultado = await response.json();

        if (response.ok) {
            alert('✅ Cliente cadastrado com sucesso!');
            limparFormularioCadastro();
        } else {
            alert('❌ Erro: ' + (resultado.erro || 'Erro desconhecido'));
        }
    } catch (error) {
        alert('❌ Erro de conexão com o servidor!');
        console.error('Erro:', error);
    }
}

// ===========================================
// FUNÇÃO PARA CANCELAR
// ===========================================
async function cancelar() {
    const confirmado = window.ui?.confirmAsync
        ? await window.ui.confirmAsync('Deseja realmente cancelar? Os dados não serão salvos.')
        : (window.ui ? window.ui.confirm('Deseja realmente cancelar? Os dados não serão salvos.') : confirm('Deseja realmente cancelar? Os dados não serão salvos.'));
    if (!confirmado) return;
    window.location.href = "/";
}

function limparFormularioCadastro() {
    const campos = [
        'nome_cliente', 'cpf', 'telefone', 'email',
        'endereco', 'cidade', 'estado', 'cep',
        'placa', 'fabricante', 'modelo', 'ano', 'motor',
        'combustivel', 'cor', 'tanque', 'km', 'direcao', 'ar'
    ];

    for (const id of campos) {
        const el = document.getElementById(id);
        if (!el) continue;
        el.value = '';
        el.style.borderColor = '';
    }

    document.getElementById('nome_cliente')?.focus();
}

// ===========================================
// MÁSCARAS E VALIDAÇÕES EM TEMPO REAL
// ===========================================
document.addEventListener('DOMContentLoaded', function() {
    
    // MÁSCARA DO CPF - com verificação de existência
    const campoCPF = document.getElementById('cpf');
    if (campoCPF) {
        campoCPF.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                if (value.length > 9) {
                    value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
                } else if (value.length > 6) {
                    value = value.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
                } else if (value.length > 3) {
                    value = value.replace(/(\d{3})(\d{1,3})/, '$1.$2');
                }
                e.target.value = value;
            }

            // Validação em tempo real (opcional)
            const cpfLimpo = value.replace(/\D/g, '');
            if (cpfLimpo.length === 11) {
                if (validarCPF(cpfLimpo)) {
                    e.target.style.borderColor = '#2c7a4d';
                } else {
                    e.target.style.borderColor = '#a03232';
                }
            } else {
                e.target.style.borderColor = '';
            }
        });
    }

    // MÁSCARA DA PLACA - com verificação de existência
    const campoPlaca = document.getElementById('placa');
    if (campoPlaca) {
        campoPlaca.addEventListener('input', function(e) {
            let value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
            if (value.length <= 7) {
                if (value.length > 3) {
                    value = value.substring(0,3) + '-' + value.substring(3);
                }
                e.target.value = value;
            }
        });
    }

    // MÁSCARA DO KM (só números) - com verificação de existência
    const campoKM = document.getElementById('km');
    if (campoKM) {
        campoKM.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/\D/g, '');
        });
    }

    // MÁSCARA DO ANO - com verificação de existência
    const campoAno = document.getElementById('ano');
    if (campoAno) {
        campoAno.addEventListener('input', function(e) {
            e.target.value = e.target.value.replace(/[^\d\/]/g, '');
        });
    }
});

// ===========================================
// ATALHOS DE TECLADO
// ===========================================
document.addEventListener('keydown', function(e) {
    if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        if (typeof salvar === 'function') {
            salvar();
        }
    }
    if (e.key === 'Escape') {
        if (typeof cancelar === 'function') {
            cancelar();
        }
    }
});
