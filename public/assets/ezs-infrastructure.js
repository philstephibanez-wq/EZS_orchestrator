'use strict';
(function ($) {
    if (!$) return;
    $(function () {
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
                    const code = Number.isInteger(item.http_status) ? item.http_status : null;
                    const healthy = code !== null && code >= 200 && code < 400;
                    const httpError = code !== null && code >= 400;
                    const label = healthy ? 'HTTP opérationnel' : httpError ? 'Erreur HTTP' : item.tcp_listening ? 'TCP seul' : 'Façade absente';
                    const color = healthy ? 'text-bg-success' : httpError ? 'text-bg-danger' : item.tcp_listening ? 'text-bg-warning' : 'text-bg-secondary';
                    const $badge = $('#state-'+key);
                    $badge.text(label).removeClass('text-bg-secondary text-bg-success text-bg-warning text-bg-danger').addClass(color);
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
        $refresh.on('click', function(){ refresh(); refreshBackend(); });
        refresh(); refreshBackend();
        window.setInterval(function () { if (!document.hidden) {refresh(); refreshBackend();} }, 15000);
    });
})(window.jQuery);
