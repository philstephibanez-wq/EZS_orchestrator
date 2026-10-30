/* DEV: diagnostic unifié; GET en lecture seule et export par liste blanche. */
'use strict';
(() => {
    const panel = document.getElementById('ezs-debug-panel');
    if (!panel) return;
    const output = document.getElementById('ezs-debug-output');
    const status = document.getElementById('ezs-debug-status');
    const copy = document.getElementById('ezs-debug-copy');
    const refresh = document.getElementById('ezs-debug-refresh');
    const spinner = document.getElementById('ezs-debug-spinner');
    const rows = document.getElementById('ezs-debug-groups-body');
    const native = document.getElementById('ezs-debug-native');
    const browser = document.getElementById('ezs-debug-browser');
    if (!output || !status || !copy || !refresh || !spinner || !rows || !native || !browser) return;
    panel.dataset.ezsDebugReady = '1';
    status.textContent = 'Diagnostic prêt';
    output.textContent = 'En attente de collecte automatique.';
    const groups = {dev: 'dev-title', lab: 'lab-title', assistant: 'assistant-title'};
    const nativeNames = {dev:['ezscore_dev','ezscore_preview'], lab:['lab'], assistant:['assistant']};
    const errors = [];
    let report = '';
    let busy = false;
    const buttonChanges = [];
    // Observation uniquement : jamais de modification des boutons ni de la requête métier.
    const observedButtons = Object.keys(groups).flatMap(group => {
        const card = document.getElementById(groups[group])?.closest('.ezs-server-card');
        return card ? [...card.querySelectorAll('.ezs-server-actions button')].slice(0, 2).map((button, index) => ({group, verb:index ? 'stop' : 'start', button})) : [];
    });
    const buttonObserver = new MutationObserver(records => {
        for (const record of records) {
            const match = observedButtons.find(item => item.button === record.target);
            if (!match || record.attributeName !== 'disabled') continue;
            buttonChanges.push(new Date().toISOString() + ' ' + match.group + '/' + match.verb + ' disabled=' + match.button.disabled);
            if (buttonChanges.length > 30) buttonChanges.shift();
        }
    });
    observedButtons.forEach(item => buttonObserver.observe(item.button, {attributes:true, attributeFilter:['disabled']}));

    window.addEventListener('error', () => { if (errors.length < 10) errors.push('SCRIPT_ERROR'); });
    window.addEventListener('unhandledrejection', () => { if (errors.length < 10) errors.push('PROMISE_REJECTION'); });
    try { panel.open = sessionStorage.getItem('ezs_debug_open') === '1'; } catch (_) { /* facultatif */ }
    panel.addEventListener('toggle', () => {
        try { sessionStorage.setItem('ezs_debug_open', panel.open ? '1' : '0'); } catch (_) { /* facultatif */ }
        if (panel.open) void collect();
    });

    function cell(row, value) {
        const td = document.createElement('td');
        td.textContent = String(value);
        row.appendChild(td);
    }
    function safeStatus(value) {
        return ['ATTESTED','ABSENT','RECORDED_UNVERIFIED','PORT_UNVERIFIED','MISSING'].includes(value) ? value : 'INCONNU';
    }
    function dom(group) {
        const doc = document;
        const card = doc.getElementById(groups[group])?.closest('.ezs-server-card');
        const buttons = card ? [...card.querySelectorAll('.ezs-server-actions button')] : [];
        return {count:card ? buttons.length : 'hors page', start:buttons[0] ? String(buttons[0].disabled) : 'ABSENT', stop:buttons[1] ? String(buttons[1].disabled) : 'ABSENT'};
    }
    async function get(url) {
        const response = await fetch(url,{method:'GET',credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(10000)});
        if (!response.ok) throw new Error('HTTP_' + response.status);
        return response.json();
    }
    async function collect() {
        if (busy || !panel.open) return;
        busy = true;
        spinner.classList.remove('d-none');
        refresh.disabled = true;
        status.textContent = report ? 'Actualisation du diagnostic… (dernières valeurs conservées)' : 'Actualisation du diagnostic…';
        if (!report) output.textContent = 'Actualisation du diagnostic…';
        let incomplete = false;
        const lines = [
            'EZS — DIAGNOSTIC DEV DÉTAILLÉ (lecture seule)',
            'Horodatage UTC : ' + new Date().toISOString(),
            'Version : ' + (document.querySelector('.navbar-brand small')?.textContent.trim() || 'inconnue'),
            'Page : ' + location.pathname,
            'Navigateur : ' + (navigator.userAgent.includes('Chrome') ? 'Chromium' : 'autre'),
            'Document : ' + document.readyState,
            'jQuery : ' + (window.jQuery ? 'présent' : 'absent'),
            'Script Infrastructure : ' + document.querySelectorAll('script[src*="ezs-infrastructure.js"]').length,
            'Erreurs JS observées : ' + (errors.join(', ') || 'aucune'),
            '', 'ÉTATS NATIFS PHP'
        ];
        try {
            const data = await get('/api/v2/infrastructure/dev-debug-native');
            if (data.schema !== 'ezs.dev_group_native_debug.v1') throw new Error('SCHEMA');
            const list = [];
            for (const [group, names] of Object.entries(nativeNames)) {
                for (const name of names) {
                    const value = safeStatus(data.groups?.[group]?.[name]);
                    lines.push(group + ' / ' + name + ' : ' + value);
                    list.push(group + ' / ' + name + ' : ' + value);
                }
            }
            if (data.error) {
                incomplete = true;
                lines.push('Inventaire : INDISPONIBLE');
            }
            native.textContent = list.join(' | ') + (data.error ? ' ; Inventaire indisponible' : '');
        } catch (_) {
            incomplete = true;
            native.textContent = 'Inventaire natif indisponible';
            lines.push('Inventaire natif : INDISPONIBLE');
        }
        lines.push('', 'API ET BOUTONS OBSERVÉS');
        const divergences = [];
        const newRows = document.createDocumentFragment();
        try {
            const data = await get('/api/v2/infrastructure/dev-groups');
            if (data.schema !== 'ezs.dev_groups.v1') throw new Error('SCHEMA');
            lines.push('API GET : 200 ; schéma reconnu : true');
            for (const group of Object.keys(groups)) {
                const item = data.groups?.[group];
                const state = ['RUNNING','STOPPED','UNVERIFIED','PARTIAL'].includes(item?.state) ? item.state : 'INCONNU';
                const d = dom(group);
                if (d.count === 'hors page') {
                    divergences.push(group + ' : boutons absents sur cette page (non comparable)');
                } else if (d.count !== 2) {
                    divergences.push(group + ' : nombre de boutons inattendu (' + d.count + ')');
                } else {
                    if (d.start !== String(item?.start !== true)) divergences.push(group + ' / démarrer : API=' + (item?.start === true) + ', DOM disabled=' + d.start);
                    if (d.stop !== String(item?.stop !== true)) divergences.push(group + ' / arrêter : API=' + (item?.stop === true) + ', DOM disabled=' + d.stop);
                }
                const row = document.createElement('tr');
                [group,state,item?.start === true,item?.stop === true,d.count,d.start,d.stop].forEach(v => cell(row,v));
                newRows.appendChild(row);
                lines.push(group + ' : état=' + state + ' ; start=' + (item?.start === true) + ' ; stop=' + (item?.stop === true)
                    + ' ; DOM boutons=' + d.count + ', demarrer.disabled=' + d.start + ', arreter.disabled=' + d.stop);
            }
        } catch (_) {
            incomplete = true;
            lines.push('API GET : INDISPONIBLE');
            for (const group of Object.keys(groups)) {
                const d = dom(group);
                const row = document.createElement('tr');
                [group,'INCONNU','INCONNU','INCONNU',d.count,d.start,d.stop].forEach(v => cell(row,v));
                newRows.appendChild(row);
                lines.push(group + ' : API indisponible ; DOM boutons=' + d.count + ', demarrer.disabled=' + d.start + ', arreter.disabled=' + d.stop);
            }
        }
        lines.push('', 'ÉCARTS API / DOM (instantané, sans action)');
        lines.push(...(divergences.length ? divergences : ['Aucun écart détecté à cet instant']));
        lines.push('', 'CHANGEMENTS DES BOUTONS OBSERVÉS (max. 30, depuis ouverture de page)');
        lines.push(...(buttonChanges.length ? buttonChanges : ['Aucun changement observé']));
        rows.replaceChildren(newRows);
        browser.textContent = 'jQuery : ' + (window.jQuery ? 'présent' : 'absent') + ' ; document : ' + document.readyState
            + ' ; script Infrastructure : ' + document.querySelectorAll('script[src*="ezs-infrastructure.js"]').length;
        report = lines.join('\n');
        output.textContent = report;
        status.textContent = incomplete ? 'Collecte incomplète — consulter le rapport (' + report.length + ' caractères)' : 'Diagnostic actualisé — ' + new Date().toLocaleTimeString('fr-FR') + ' (' + report.length + ' caractères)';
        refresh.disabled = false;
        spinner.classList.add('d-none');
        busy = false;
    }
    refresh.addEventListener('click', () => { void collect(); });
    copy.addEventListener('click', async () => {
        if (!report) await collect();
        if (!report) return;
        try {
            await navigator.clipboard.writeText(report);
            status.textContent = 'Diagnostic complet copié — coller dans le chat';
        } catch (_) {
            output.focus();
            const selection = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(output);
            selection.removeAllRanges();
            selection.addRange(range);
            status.textContent = 'Copie automatique indisponible : Ctrl + C sur le texte sélectionné';
        }
    });
    if (panel.open) void collect();
})();
