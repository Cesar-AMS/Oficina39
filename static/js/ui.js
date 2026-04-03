// ui.js - notificacoes padronizadas (toast) + confirmacao sincronizada
(function () {
    const CONTAINER_ID = 'ui-toast-container';
    const STYLE_ID = 'ui-toast-style';
    let counter = 0;

    function normalizeMessage(message, fallback) {
        const text = (message || '').toString().trim();
        return text || fallback;
    }

    function ensureStyle() {
        if (document.getElementById(STYLE_ID)) return;
        const style = document.createElement('style');
        style.id = STYLE_ID;
        style.textContent = `
            #${CONTAINER_ID} {
                position: fixed;
                top: 16px;
                right: 16px;
                z-index: 99999;
                display: flex;
                flex-direction: column;
                gap: 10px;
                max-width: 420px;
                pointer-events: none;
            }

            .ui-toast {
                pointer-events: auto;
                border-radius: 14px;
                padding: 14px 16px;
                color: #fff;
                font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-size: 0.92rem;
                line-height: 1.5;
                box-shadow: 0 10px 28px rgba(15,23,42,0.18);
                display: flex;
                align-items: flex-start;
                gap: 10px;
                animation: uiToastIn 180ms ease-out;
                border: 1px solid rgba(255,255,255,0.1);
            }

            .ui-toast--success { background: #10b981; }
            .ui-toast--error { background: #ef4444; }
            .ui-toast--info { background: #1a56db; }

            .ui-toast__msg {
                flex: 1;
                word-break: break-word;
            }

            .ui-toast__close {
                border: none;
                background: transparent;
                color: #fff;
                cursor: pointer;
                font-size: 1rem;
                line-height: 1;
                padding: 0;
                opacity: 0.9;
            }

            .ui-toast__close:hover { opacity: 1; }

            .ui-toast--hide {
                opacity: 0;
                transform: translateY(-6px);
                transition: all 180ms ease;
            }

            @keyframes uiToastIn {
                from { opacity: 0; transform: translateY(-8px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .ui-confirm-overlay {
                position: fixed;
                inset: 0;
                background: rgba(15, 23, 42, 0.5);
                z-index: 100000;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 16px;
            }

            .ui-confirm-modal {
                width: 100%;
                max-width: 420px;
                background: #fff;
                border-radius: 16px;
                box-shadow: 0 20px 45px rgba(15,23,42,0.18);
                padding: 24px;
                font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                color: #1f2937;
                animation: uiToastIn 150ms ease-out;
            }

            .ui-confirm-title {
                font-size: 1.05rem;
                font-weight: 700;
                margin-bottom: 10px;
            }

            .ui-confirm-message {
                font-size: 0.95rem;
                line-height: 1.5;
                margin-bottom: 18px;
                white-space: pre-wrap;
                color: #4b5563;
            }

            .ui-confirm-actions {
                display: flex;
                justify-content: flex-end;
                gap: 8px;
            }

            .ui-confirm-btn {
                border: none;
                border-radius: 8px;
                padding: 10px 16px;
                cursor: pointer;
                font-size: 0.92rem;
                font-weight: 600;
            }

            .ui-confirm-btn--cancel {
                background: #ffffff;
                color: #1f2937;
                border: 1px solid #d1d5db;
            }

            .ui-confirm-btn--ok {
                background: #1a56db;
                color: #fff;
                border: 1px solid #1a56db;
            }
        `;
        document.head.appendChild(style);
    }

    function ensureContainer() {
        let container = document.getElementById(CONTAINER_ID);
        if (container) return container;
        container = document.createElement('div');
        container.id = CONTAINER_ID;
        document.body.appendChild(container);
        return container;
    }

    function removeToast(toast) {
        toast.classList.add('ui-toast--hide');
        setTimeout(() => {
            if (toast && toast.parentElement) toast.parentElement.removeChild(toast);
        }, 180);
    }

    function showToast(type, message, fallback, timeoutMs = 4200) {
        const text = normalizeMessage(message, fallback);
        if (!document.body) {
            window.alert(text);
            return;
        }

        ensureStyle();
        const container = ensureContainer();
        const toast = document.createElement('div');
        toast.className = `ui-toast ui-toast--${type}`;
        toast.dataset.id = `t${++counter}`;

        const msg = document.createElement('div');
        msg.className = 'ui-toast__msg';
        msg.textContent = text;

        const closeBtn = document.createElement('button');
        closeBtn.className = 'ui-toast__close';
        closeBtn.type = 'button';
        closeBtn.setAttribute('aria-label', 'Fechar');
        closeBtn.textContent = '×';
        closeBtn.addEventListener('click', () => removeToast(toast));

        toast.appendChild(msg);
        toast.appendChild(closeBtn);
        container.appendChild(toast);

        if (timeoutMs > 0) {
            setTimeout(() => removeToast(toast), timeoutMs);
        }
    }

    const ui = {
        success(message) {
            showToast('success', message, 'Operação concluída.');
        },
        error(message) {
            showToast('error', message, 'Ocorreu uma falha.');
        },
        info(message) {
            showToast('info', message, 'Mensagem informativa.');
        },
        // Mantido síncrono para não quebrar fluxos existentes.
        confirm(message) {
            return window.confirm(normalizeMessage(message, 'Confirma esta ação?'));
        },
        confirmAsync(message, options = {}) {
            const text = normalizeMessage(message, 'Confirma esta ação?');
            const title = normalizeMessage(options.title, 'Confirmar');
            const okText = normalizeMessage(options.okText, 'Confirmar');
            const cancelText = normalizeMessage(options.cancelText, 'Cancelar');

            if (!document.body) return Promise.resolve(window.confirm(text));
            ensureStyle();

            return new Promise((resolve) => {
                const overlay = document.createElement('div');
                overlay.className = 'ui-confirm-overlay';

                const modal = document.createElement('div');
                modal.className = 'ui-confirm-modal';

                const titleEl = document.createElement('div');
                titleEl.className = 'ui-confirm-title';
                titleEl.textContent = title;

                const msgEl = document.createElement('div');
                msgEl.className = 'ui-confirm-message';
                msgEl.textContent = text;

                const actions = document.createElement('div');
                actions.className = 'ui-confirm-actions';

                const cancelBtn = document.createElement('button');
                cancelBtn.type = 'button';
                cancelBtn.className = 'ui-confirm-btn ui-confirm-btn--cancel';
                cancelBtn.textContent = cancelText;

                const okBtn = document.createElement('button');
                okBtn.type = 'button';
                okBtn.className = 'ui-confirm-btn ui-confirm-btn--ok';
                okBtn.textContent = okText;

                function close(result) {
                    if (overlay.parentElement) overlay.parentElement.removeChild(overlay);
                    document.removeEventListener('keydown', onKeyDown);
                    resolve(result);
                }

                function onKeyDown(e) {
                    if (e.key === 'Escape') close(false);
                }

                cancelBtn.addEventListener('click', () => close(false));
                okBtn.addEventListener('click', () => close(true));
                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) close(false);
                });
                document.addEventListener('keydown', onKeyDown);

                actions.appendChild(cancelBtn);
                actions.appendChild(okBtn);
                modal.appendChild(titleEl);
                modal.appendChild(msgEl);
                modal.appendChild(actions);
                overlay.appendChild(modal);
                document.body.appendChild(overlay);
                okBtn.focus();
            });
        }
    };

    window.ui = ui;
})();
