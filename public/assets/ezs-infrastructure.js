'use strict';
(function ($) {
    if (!$) return;
    $(function () {
        // Remove the redundant footer from the Infrastructure view.
        $('.ezs-footerline').remove();
        const $feedback = $('#dev-health-feedback');
        const $refresh = $('#refresh-dev-health');
        let pending = false;
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
                    const label = item.http_status !== null ? ((item.http_status >= 500) ? 'Erreur HTTP' : 'Répond') : item.tcp_listening ? 'TCP seul' : 'Façade absente';
                    const $badge = $('#state-'+key);
                    $badge.text(label).removeClass('text-bg-secondary text-bg-success text-bg-warning').addClass(item.http_status !== null ? 'text-bg-success' : item.tcp_listening ? 'text-bg-warning' : 'text-bg-secondary');
                });
                if (labBackend) {
                    $('#lab-backend').text(labBackend.tcp_listening ? 'FastCGI TCP ouvert' : 'Arrêt / absent');
                    if (labBackend.tcp_listening && $('#state-lab').text() === 'Façade absente') $('#state-lab').text('Backend actif · façade absente').removeClass('text-bg-secondary').addClass('text-bg-warning');
                }
                $feedback.text('Mesure DEV : ' + (data.timestamp_utc || 'récente'));
              })
              .fail(function () { $feedback.text('Supervision DEV indisponible'); })
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
        Object.keys(groups).forEach(function(group) {
            const $card = $(groups[group]).closest('.ezs-server-card');
            const $buttons = $card.find('.ezs-server-actions button');
            controls[group] = {start:$buttons.eq(0), stop:$buttons.eq(1)};
            $buttons.removeAttr('title').prop('disabled', true);
        });
        function disableAll() {
            Object.keys(controls).forEach(function(group) {
                controls[group].start.prop('disabled', true);
                controls[group].stop.prop('disabled', true);
            });
        }
        function refreshGroups() {
            if (acting) return;
            $.ajax({url:'/api/v2/infrastructure/dev-groups',method:'GET',dataType:'json',timeout:10000,cache:false})
              .done(function(data) {
                  if (!data || data.schema !== 'ezs.dev_groups.v1' || !data.groups || !data.csrf) {
                      csrf = ''; disableAll(); return;
                  }
                  csrf = data.csrf;
                  Object.keys(controls).forEach(function(group) {
                      const state = data.groups[group] || {};
                      controls[group].start.prop('disabled', !state.start);
                      controls[group].stop.prop('disabled', !state.stop);
                      controls[group].start.attr('title', 'État natif : '+(state.state || 'indéterminé'));
                      controls[group].stop.attr('title', 'État natif : '+(state.state || 'indéterminé'));
                  });
              }).fail(function() { csrf = ''; disableAll(); });
        }
        function action(group, verb) {
            if (acting || !csrf || !controls[group] || controls[group][verb].prop('disabled')) return;
            const label = {dev:'EZScore DEV',lab:'EZStudio LAB',assistant:'Assistant'}[group];
            const confirmation = verb === 'stop' ?
                'Arrêter les processus natifs de '+label+' ? Les travaux en cours peuvent être interrompus. Les autres groupes et l’IA restent inchangés.' :
                'Démarrer uniquement les processus natifs de '+label+' ?';
            if (!window.confirm(confirmation)) return;
            acting = true;
            disableAll();
            $feedback.text((verb === 'start' ? 'Démarrage' : 'Arrêt')+' '+label+' en cours…');
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
            controls[group].start.on('click', function(){ action(group,'start'); });
            controls[group].stop.on('click', function(){ action(group,'stop'); });
        });
        $refresh.on('click', function(){ refresh(); refreshBackend(); refreshGroups(); });
        refresh(); refreshBackend(); refreshGroups();
        window.setInterval(function () { if (!document.hidden) {refresh(); refreshBackend(); refreshGroups();} }, 15000);
    });
})(window.jQuery);
