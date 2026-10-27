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
            $.ajax({url:'/api/v2/infrastructure/dev-health', method:'GET', dataType:'json', cache:false, timeout:5000})
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
                    $('#lab-backend').text(labBackend.http_status === null ? (labBackend.tcp_listening ? 'TCP seul' : 'Arrêt / absent') : 'HTTP ' + labBackend.http_status);
                    if (labBackend.tcp_listening && $('#state-lab').text() === 'Façade absente') $('#state-lab').text('Backend actif · façade absente').removeClass('text-bg-secondary').addClass('text-bg-warning');
                }
                $feedback.text('Mesure DEV : ' + (data.timestamp_utc || 'récente'));
              })
              .fail(function () { $feedback.text('Supervision DEV indisponible'); })
              .always(function () { pending = false; $refresh.prop('disabled', false); });
        }
        $refresh.on('click', refresh);
        refresh();
        window.setInterval(function () { if (!document.hidden) refresh(); }, 15000);
    });
})(window.jQuery);
