/**
 * AI Startup Mentor — Chat Interface
 * Handles sending questions, rendering structured responses,
 * typing animation, quick-question buttons, and chat clearing.
 */
document.addEventListener('DOMContentLoaded', function () {

    // ── DOM refs ──────────────────────────────────────────────
    const page        = document.querySelector('.mentor-page');
    const messages    = document.getElementById('chatMessages');
    const input       = document.getElementById('chatInput');
    const sendBtn     = document.getElementById('sendBtn');
    const clearBtn    = document.getElementById('clearChatBtn');
    const quickBtns   = document.querySelectorAll('.quick-btn');
    const welcomeMsg  = document.getElementById('welcomeMsg');

    if (!page) return;
    const reportId = page.getAttribute('data-report-id');

    // ── Auto-resize textarea ──────────────────────────────────
    input.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // ── Enter to send (Shift+Enter = newline) ─────────────────
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    // ── Quick question buttons ────────────────────────────────
    quickBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const q = this.getAttribute('data-q');
            if (q) {
                input.value = q;
                input.style.height = 'auto';
                input.style.height = Math.min(input.scrollHeight, 120) + 'px';
                sendMessage();
            }
        });
    });

    // ── Clear chat ────────────────────────────────────────────
    clearBtn.addEventListener('click', function () {
        if (!confirm('Clear all chat history for this startup?')) return;

        fetch(`/dashboard/report/${reportId}/mentor/clear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                messages.innerHTML = `
                    <div class="chat-welcome" id="welcomeMsg">
                        <i class="fa-solid fa-robot"></i>
                        <p>
                            <strong style="color:#fff;">Chat cleared.</strong><br>
                            Ask me anything about your startup.
                        </p>
                    </div>`;
            }
        })
        .catch(() => alert('Failed to clear chat. Please try again.'));
    });

    // ── Core: send a message ──────────────────────────────────
    function sendMessage() {
        const question = input.value.trim();
        if (!question || sendBtn.disabled) return;

        // Remove welcome state
        const welcome = document.getElementById('welcomeMsg');
        if (welcome) welcome.remove();

        // Append user bubble
        appendUserBubble(question);

        // Clear + lock input
        input.value = '';
        input.style.height = 'auto';
        setLoading(true);

        // Show typing indicator
        const typingId = showTyping();

        // Call API
        fetch(`/dashboard/report/${reportId}/mentor/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question }),
        })
        .then(r => r.json())
        .then(data => {
            removeTyping(typingId);
            setLoading(false);

            if (data.error) {
                appendErrorBubble(data.error);
                return;
            }

            if (data.structured) {
                appendAssistantBubble(data.structured);
            } else {
                appendErrorBubble('Received an unexpected response. Please try again.');
            }
        })
        .catch(err => {
            removeTyping(typingId);
            setLoading(false);
            appendErrorBubble('Connection error. Please check your network and try again.');
            console.error('Mentor chat error:', err);
        });
    }

    // ── Render helpers ────────────────────────────────────────
    function appendUserBubble(text) {
        const row = document.createElement('div');
        row.className = 'msg-row user';
        row.innerHTML = `
            <div class="msg-avatar"><i class="fa-regular fa-user"></i></div>
            <div class="msg-bubble">${escapeHtml(text)}</div>
        `;
        messages.appendChild(row);
        scrollBottom();
    }

    function appendAssistantBubble(structured) {
        const row = document.createElement('div');
        row.className = 'msg-row assistant';

        const priorityClass = (structured.priority_level || 'medium').toLowerCase();
        const priorityLabel = structured.priority_level || 'Medium';

        // Build action steps HTML
        let stepsHtml = '';
        if (structured.action_steps && structured.action_steps.length) {
            const items = structured.action_steps
                .map((step, i) => `
                    <li>
                        <span class="step-num">${i + 1}</span>
                        <span>${escapeHtml(step)}</span>
                    </li>`)
                .join('');
            stepsHtml = `
                <div class="struct-section steps">
                    <div class="struct-label">Action Steps</div>
                    <ul class="steps-list">${items}</ul>
                </div>`;
        }

        row.innerHTML = `
            <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="msg-bubble">
                <strong>${escapeHtml(structured.recommendation || '')}</strong>
                <div class="structured-block">
                    <div class="struct-section reason">
                        <div class="struct-label">Reasoning</div>
                        ${escapeHtml(structured.reasoning || '')}
                    </div>
                    ${stepsHtml}
                    <div class="struct-section priority ${priorityClass}">
                        <i class="fa-solid fa-flag"></i>
                        ${escapeHtml(priorityLabel)} Priority
                    </div>
                </div>
            </div>
        `;
        messages.appendChild(row);
        scrollBottom();
    }

    function appendErrorBubble(msg) {
        const row = document.createElement('div');
        row.className = 'msg-row assistant';
        row.innerHTML = `
            <div class="msg-avatar" style="background: rgba(239,68,68,0.3);">
                <i class="fa-solid fa-triangle-exclamation" style="color:#f87171;"></i>
            </div>
            <div class="msg-bubble" style="border-color:rgba(239,68,68,0.25); background:rgba(239,68,68,0.06);">
                <span style="color:#f87171;">${escapeHtml(msg)}</span>
            </div>
        `;
        messages.appendChild(row);
        scrollBottom();
    }

    // ── Typing indicator ──────────────────────────────────────
    function showTyping() {
        const id = 'typing-' + Date.now();
        const row = document.createElement('div');
        row.className = 'msg-row assistant';
        row.id = id;
        row.innerHTML = `
            <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        messages.appendChild(row);
        scrollBottom();
        return id;
    }

    function removeTyping(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // ── Utilities ─────────────────────────────────────────────
    function setLoading(state) {
        sendBtn.disabled = state;
        input.disabled = state;
        sendBtn.innerHTML = state
            ? '<i class="fa-solid fa-spinner fa-spin"></i>'
            : '<i class="fa-solid fa-paper-plane"></i>';
    }

    function scrollBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function escapeHtml(str) {
        if (typeof str !== 'string') return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Scroll to bottom on initial load if there's history
    scrollBottom();
});
