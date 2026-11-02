'use strict';
(function ($) {
    if (!$) return;
    $(function () {
        // Remove the redundant footer from the Infrastructure view.
        $('.ezs-footerline').remove();
        const $feedback = $('#dev-health-feedback');
        const $refresh = $('#refresh-dev-health');
        let pending = false;
        // Snapshot fusion: an HTTP response alone never proves the native process is running.
        const serviceTransport = {dev:null,lab:null,assistant:null};
        const serviceNative = {dev:null,lab:null,assistant:null};
        function renderServiceBadge(group) {
            const native = serviceNative[group];
            const transport = serviceTransport[group];
            const http = transport ? transport.http : null;
            const tcp = transport ? transport.tcp : null;
            const explicitFailure = transport && transport.applicationHealthy === false;
            const explicitHealth = transport && transport.applicationHealthy === true;
            // Native STOPPED is authoritative, even when a stale HTTP proxy still responds.
            const failed = native === 'STOPPED' || explicitFailure ||
                (transport && http !== null && http >= 500) ||
                (transport && http === null && tcp === false);
            // Green means native process attested and front HTTP reachable, not full workflow health.
            const reachable = native === 'RUNNING' && transport &&
                http !== null && http >= 200 && http < 400;
            const verified = !failed && reachable &&
                (explicitHealth || transport.applicationHealthy !== false);
            const label = failed ? 'En erreur' : verified ? 'En ligne' : '\u00c0 v\u00e9rifier';
            const $badge = $('#state-' + group);
            $badge.text(label).removeClass('text-bg-secondary text-bg-success text-bg-warning text-bg-danger')
                .addClass(failed ? 'text-bg-danger' : verified ? 'text-bg-success' : 'text-bg-warning');
            $badge.attr('title', 'Processus natif : ' + (native || 'non attest\u00e9') +
                ' ; HTTP : ' + (http === null ? 'sans mesure' : http) +
                ' ; sant\u00e9 fonctionnelle : ' + (explicitHealth ? 'attest\u00e9e' : explicitFailure ? 'en erreur' : 'non test\u00e9e'));
        }
        function refresh() {
            if (pending) return;
            pending = true;
            $refresh.prop('disabled', true);
            $.ajax({url:'/api/v2/infrastructure/dev-health', method:'GET', dataType:'json', cache:false, timeout:9000})
              .done(function (data) {
                if (!data || data.schema !== 'ezs.dev_health.v1' || !Array.isArray(data.items)) throw new Error('bad_payload');
                const mapping = {ezscore:'dev',lab:'lab',assistant:'assistant'};
                let labBackend = null;
                data.items.forEach(function (item) {
                    if (item.component === 'lab' && item.kind === 'backend') { labBackend = item; return; }
                    const key = mapping[item.component];
                    if (!key) return;
                    $('#tcp-'+key).text(item.tcp_listening ? 'Ouvert' : 'Fermé');
                    $('#http-'+key).text(item.http_status === null ? 'Sans réponse' : String(item.http_status));
                    serviceTransport[key] = {
                        http:item.http_status, tcp:item.tcp_listening === true,
                        applicationHealthy:item.application_healthy
                    };
                    renderServiceBadge(key);
                });
                if (labBackend) {
                    $('#lab-backend').text(labBackend.tcp_listening ? 'FastCGI TCP ouvert' : 'Arrêt / absent');
                    if (labBackend.tcp_listening && $('#state-lab').text() === 'Façade absente') $('#state-lab').text('Backend actif · façade absente').removeClass('text-bg-secondary').addClass('text-bg-warning');
                }
                $feedback.text('Mesure DEV : ' + (data.timestamp_utc || 'récente'));
              })
              .fail(function () {
                  Object.keys(serviceTransport).forEach(function(group) {
                      serviceTransport[group] = null;
                      renderServiceBadge(group);
                  });
                  $feedback.text('Supervision DEV indisponible');
              })
              .always(function () { pending = false; $refresh.prop('disabled', false); });
        }
        function refreshBackend() {
            $.ajax({url:'/api/v2/infrastructure/dev-backend',method:'GET',dataType:'json',timeout:5000,cache:false})
              .done(function(data) {
                  if (!data || data.schema !== 'ezs.dev_backend.v1' || !data.item) return;
                  const d = data.item;
                  $('#dev-backend').text(d.tcp_listening ? 'Port TCP ouvert' : 'Arrêt / absent');
                  $('#dev-backend-ownership').text(d.ownership === 'legacy_exact' ? 'PID '+d.pid+' — serveur legacy identifié' : d.ownership === 'foreign' ? 'PID '+d.pid+' — processus étranger' : d.ownership === 'absent' ? 'Aucun listener' : 'Indéterminée');
                  if (d.tcp_listening && $('#state-dev').text() === 'Façade absente') {
                      $('#state-dev').text('Backend présent · façade absente').removeClass('text-bg-secondary').addClass('text-bg-warning');
                  }
              });
        }

        // Group control uses the existing buttons, without altering PROD or the Orchestrator root.
        const groups = {dev:'#dev-title', lab:'#lab-title', assistant:'#assistant-title'};
        const controls = {};
        let csrf = '';
        let acting = false;
        const modes = {dev:null,lab:null,assistant:null};
        // La vérification native peut prendre plusieurs secondes ; ne jamais simuler un état prêt.
        const groupRequestStart = {dev:0, lab:0, assistant:0};
        const $statusline = $('.ezs-statusline .text-body-secondary').first();
        $statusline.text('État des environnements — commandes DEV / LAB / Assistant vérifiées par le serveur');
        const actionDescriptions = {
            dev:'Commandes natives disponibles après vérification des processus',
            lab:'Démarrer / Redémarrer / Arrêter sous contrôle de l’Orchestrator',
            assistant:'Commandes natives supervisées ; aucune action sur les jobs ou l’IA'
        };
        Object.keys(groups).forEach(function (group) {
            const $card = $(groups[group]).closest('.ezs-server-card');
            $card.find('dt').filter(function () { return $(this).text().trim() === 'Action'; })
                .next('dd').text(actionDescriptions[group]);
            if (group === 'dev') $card.find('dt').filter(function () { return $(this).text().trim() === 'État complémentaire'; })
                .next('dd').text('État confirmé par l’inventaire natif avant toute commande');
            if (group === 'lab' || group === 'assistant') $card.find('dt').filter(function () { return $(this).text().trim() === 'Autorité Orchestrator'; })
                .next('dd').text('Orchestrator local · processus attestés · protection CSRF');
        });
        // EZS_GROUPS_STABLE_R82: seule une attestation change l'etat visible.
        let groupsPending = false;
        let groupsEpoch = 0;
        const rendered = {dev:null,lab:null,assistant:null};
        Object.keys(groups).forEach(function(group) {
            const $buttons = $(groups[group]).closest('.ezs-server-card').find('.ezs-server-actions button');
            controls[group] = {start:$buttons.eq(0), stop:$buttons.eq(1)};
            $buttons.removeAttr('title').prop('disabled', true);
            controls[group].start.text('État inconnu');
        });
        function disableAll() {
            Object.keys(controls).forEach(function(group) {
                controls[group].start.prop('disabled', true);
                controls[group].stop.prop('disabled', true);
            });
        }
        function indicateUnavailable(reason) {
            Object.keys(controls).forEach(function(group) {
                const card = $(groups[group]).closest('.ezs-server-card');
                card.attr('data-ezs-probe', 'unavailable');
                controls[group].start.attr('title', 'Permissions indisponibles : ' + reason);
                controls[group].stop.attr('title', 'Permissions indisponibles : ' + reason);
            });
        }
        function $cardFor(group) { return $(groups[group]).closest('.ezs-server-card'); }
        function refreshGroups() {
            if (acting || groupsPending) return;
            groupsPending = true;
            const epoch = ++groupsEpoch;
            const startedAt = window.performance.now();
            $.ajax({url:'/api/v2/infrastructure/dev-groups',method:'GET',dataType:'json',timeout:10000,cache:false})
              .done(function(data) {
                  if (acting || epoch !== groupsEpoch) return;
                  if (!data || data.schema !== 'ezs.dev_groups.v1' || !data.groups || !data.csrf) {
                      csrf = '';
                      disableAll();
                      indicateUnavailable('réponse invalide');
                      Object.keys(serviceNative).forEach(function(group) { serviceNative[group] = null; renderServiceBadge(group); });
                      $feedback.text('Pilotage DEV : permissions indisponibles (réponse invalide)');
                      return;
                  }
                  csrf = data.csrf;
                  Object.keys(controls).forEach(function(group) {
                      const state = data.groups[group] || {};
                       serviceNative[group] = state.state === 'RUNNING' || state.state === 'STOPPED' ? state.state : null;
                       renderServiceBadge(group);
                      const mode = state.state === 'RUNNING' && state.restart === true ? 'restart'
                          : state.state === 'STOPPED' && state.start === true ? 'start' : null;
                      const next = {state:state.state || 'UNVERIFIED',mode:mode,stop:state.stop === true};
                      const previous = rendered[group];
                      modes[group] = mode;
                      if (!previous || previous.state !== next.state || previous.mode !== next.mode || previous.stop !== next.stop) {
                          const $start = controls[group].start;
                          const $stop = controls[group].stop;
                          $start.text(mode === 'restart' ? 'Redémarrer' : mode === 'start' ? 'Démarrer' : 'Indisponible');
                          $start.removeAttr('aria-busy').attr('aria-label', mode === 'restart' ? 'Redémarrer ' + group : mode === 'start' ? 'Démarrer ' + group : 'Commande indisponible pour ' + group);
                          $stop.attr('aria-label', 'Arrêter ' + group);
                          $cardFor(group).attr('data-ezs-state', next.state);
                          $start.toggleClass('btn-outline-primary', mode !== null)
                              .toggleClass('btn-outline-secondary', mode === null);
                          $stop.toggleClass('btn-outline-danger', next.stop)
                              .toggleClass('btn-outline-secondary', !next.stop);
                          $start.attr('title', 'État natif : ' + next.state);
                          $stop.attr('title', 'État natif : ' + next.state);
                          rendered[group] = next;
                      }
                      // Droits réévalués à chaque résultat attesté, sans changer les libellés.
                      controls[group].start.prop('disabled', mode === null);
                      controls[group].stop.prop('disabled', !next.stop);
                      $cardFor(group).attr('data-ezs-probe', 'verified');
                      $cardFor(group).attr('data-ezs-state-probe-ms', String(Math.round(window.performance.now() - startedAt)));
                  });
              }).fail(function(xhr, textStatus) {
                  if (acting || epoch !== groupsEpoch) return;
                  const status = xhr && xhr.status ? String(xhr.status) : (textStatus || 'réseau');
                  const reason = xhr && xhr.responseJSON && xhr.responseJSON.error ? String(xhr.responseJSON.error) : 'réponse indisponible';
                  $feedback.text('Pilotage DEV : permissions indisponibles (HTTP ' + status + ' / ' + reason + ')');
                  csrf = '';
                  disableAll();
                  indicateUnavailable('HTTP ' + status + ' / ' + reason);
                  Object.keys(serviceNative).forEach(function(group) { serviceNative[group] = null; renderServiceBadge(group); });
                  // Conserver le dernier libellé attesté. Ne pas convertir une panne API en STOPPED.
                  Object.keys(controls).forEach(function(group) {
                      $cardFor(group).attr('data-ezs-probe', 'unavailable');
                  });
              }).always(function() { groupsPending = false; });
        }
        // EZS_DIALOG_CONFIRM_V1: no window.confirm/alert/prompt or OS message box.
        function confirmEzs(message) {
            return new Promise(function (resolve) {
                const dialog = document.createElement('dialog');
                dialog.setAttribute('aria-label', 'Confirmer l’action');
                dialog.className = 'ezs-confirm-dialog';
                dialog.style.cssText = 'border:1px solid #777;border-radius:12px;padding:0;max-width:min(460px,94vw);width:100%;background:var(--bs-body-bg,#fff);color:var(--bs-body-color,#222);box-shadow:0 12px 48px #0006';
                const body = document.createElement('div');
                body.className = 'p-4';
                const title = document.createElement('h2');
                title.className = 'h5';
                title.textContent = 'Confirmer l’action';
                const detail = document.createElement('p');
                detail.textContent = message;
                const actions = document.createElement('div');
                actions.className = 'd-flex gap-2 justify-content-end mt-3';
                const cancel = document.createElement('button');
                cancel.type = 'button';
                cancel.className = 'btn btn-outline-secondary';
                cancel.textContent = 'Annuler';
                const accept = document.createElement('button');
                accept.type = 'button';
                accept.className = 'btn btn-primary';
                accept.textContent = 'Confirmer';
                actions.append(cancel, accept);
                body.append(title, detail, actions);
                dialog.appendChild(body);
                document.body.appendChild(dialog);
                let settled = false;
                function settle(accepted) {
                    if (settled) return;
                    settled = true;
                    dialog.close();
                    dialog.remove();
                    resolve(accepted);
                }
                cancel.addEventListener('click', function () { settle(false); });
                accept.addEventListener('click', function () { settle(true); });
                dialog.addEventListener('cancel', function (event) { event.preventDefault(); settle(false); });
                try { dialog.showModal(); cancel.focus(); }
                catch (_) { settle(false); }
            });
        }
        async function action(group, verb) {
            if (!controls[group]) return;
            const button = verb === 'stop' ? controls[group].stop : controls[group].start;
            if (acting || !csrf || !button || button.prop('disabled')) return;
            const label = {dev:'EZScore DEV',lab:'EZStudio LAB',assistant:'Assistant'}[group];
            const confirmation = verb === 'stop' ?
                'Arrêter les processus natifs de '+label+' ? Les travaux en cours peuvent être interrompus. Les autres groupes et l’IA restent inchangés.' :
                verb === 'restart' ? 'Redémarrer les processus natifs de '+label+' ? Les travaux en cours peuvent être interrompus. Si la relance échoue, le groupe peut rester arrêté. PROD et les autres groupes restent inchangés.' :
                'Démarrer uniquement les processus natifs de '+label+' ?';
            if (!(await confirmEzs(confirmation))) return;
            acting = true;
            disableAll();
            $feedback.text((verb === 'start' ? 'Démarrage' : verb === 'restart' ? 'Redémarrage' : 'Arrêt')+' '+label+' en cours…');
            $.ajax({
                url:'/api/v2/infrastructure/dev-groups/'+group+'/'+verb,
                method:'POST',
                headers:{'X-EZS-CSRF':csrf},
                data:{confirmation:verb.toUpperCase()+'_'+group.toUpperCase()},
                dataType:'json',
                timeout:125000
            }).done(function() {
                $feedback.text('Commande '+label+' exécutée ; actualisation de l’état.');
            }).fail(function(xhr) {
                const message = xhr.responseJSON && xhr.responseJSON.error ? xhr.responseJSON.error : 'commande indisponible';
                $feedback.text('Commande '+label+' refusée : '+message);
            }).always(function() {
                acting = false;
                refresh(); refreshBackend(); refreshGroups();
            });
        }
        Object.keys(controls).forEach(function(group) {
            controls[group].start.on('click', function(){ if (modes[group]) action(group,modes[group]); });
            controls[group].stop.on('click', function(){ action(group,'stop'); });
        });
        $refresh.on('click', function(){ refresh(); refreshBackend(); refreshGroups(); });
        refresh(); refreshBackend(); refreshGroups();
        window.setInterval(function () { if (!document.hidden) {refresh(); refreshBackend(); refreshGroups();} }, 15000);
    });
})(window.jQuery);
