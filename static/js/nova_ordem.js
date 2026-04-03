function nomeArquivoOrcamento() {
    const data = new Date();
    const stamp = [
        data.getFullYear(),
        String(data.getMonth() + 1).padStart(2, '0'),
        String(data.getDate()).padStart(2, '0'),
        '_',
        String(data.getHours()).padStart(2, '0'),
        String(data.getMinutes()).padStart(2, '0'),
    ].join('');
    return `orcamento_preliminar_${stamp}.pdf`;
}

async function salvarBlobOrcamento(blob, nomeArquivo) {
    if (window.showSaveFilePicker) {
        const handle = await window.showSaveFilePicker({
            suggestedName: nomeArquivo,
            types: [{
                description: 'Arquivo PDF',
                accept: { 'application/pdf': ['.pdf'] }
            }]
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        return true;
    }

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = nomeArquivo;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    return true;
}

window.gerarOrcamentoPreview = async function() {
    const dados = coletarDadosOrdem();
    if (!dados) return;

    try {
        const response = await fetch('/api/orcamento/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        if (!response.ok) {
            const erro = await response.json().catch(() => ({}));
            alertErro(erro.erro || 'Nao foi possivel gerar o orcamento.');
            return;
        }

        const blob = await response.blob();
        const previewUrl = URL.createObjectURL(blob);
        const previewTab = window.open(previewUrl, '_blank', 'noopener');
        if (!previewTab) {
            alertErro('Nao foi possivel abrir a pre-visualizacao. Verifique o bloqueio de pop-up.');
        }

        await salvarBlobOrcamento(blob, nomeArquivoOrcamento());
        alertSucesso('Orcamento salvo na pasta selecionada');
    } catch (error) {
        console.error(error);
        alertErro('Falha ao gerar o orcamento preliminar.');
    }
};

window.enviarOrcamento = window.gerarOrcamentoPreview;
