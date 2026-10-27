'use strict';
/* EZS UI V2: jQuery is loaded once by the base page; read-only REST. */
(function ($) {
    if (!$) { return; }

    $(function () {
        function refreshDevHealth() {
            const $trigger = $('#refresh-dev-health');
            const $feedback = $('#dev-health-feedback');
            $trigger.prop('disabled', true);
            $.ajax({url:'/api/v2/infrastructure/dev-health', method:'GET', dataType:'json', timeout:5000, cache:false})
                .done(function(payload) {
                    if (!payload || payload.schema !== 'ezs.dev_health.v1' || !Array.isArray(payload.items)) {
                        $feedback.text('Réponse supervision invalide.'); return;
                    }
                    const $fragment = $(document.createDocumentFragment());
                    payload.items.forEach(function(item) {
                        if (!item || typeof item.component !== 'string' || !Number.isInteger(item.port)) return;
                        const $row = $('<tr>');
                        $('<td>').text(item.component).appendTo($row);
                        $('<td>').text(String(item.port)).appendTo($row);
                        $('<td>').text(item.tcp_listening ? 'Ouvert' : 'Fermé').appendTo($row);
                        $('<td>').text(item.http_status === null ? 'Sans réponse' : String(item.http_status)).appendTo($row);
                        $fragment.append($row);
                    });
                    $('#dev-health-rows').empty().append($fragment);
                    $feedback.text('Mesure effectuée : ' + payload.timestamp_utc + '.');
                })
                .fail(function(xhr) { $feedback.text('Supervision indisponible (HTTP ' + xhr.status + ').'); })
                .always(function() { $trigger.prop('disabled', false); });
        }
        $('#refresh-dev-health').on('click', refreshDevHealth);
        refreshDevHealth();
        window.setInterval(function(){ if (!document.hidden) refreshDevHealth(); }, 15000);
        const $button = $('#refresh-environments');
        const $rows = $('#environment-rows');
        const $feedback = $('#environment-feedback');

        $('#refresh-listeners').on('click', function () {
            const $trigger = $(this);
            const $feedback = $('#listeners-feedback');
            $trigger.prop('disabled', true);
            $feedback.text('Vérification en cours…');
            $.ajax({url: '/api/v2/infrastructure/listeners', method: 'GET', dataType: 'json', timeout: 5000})
                .done(function (payload) {
                    if (!payload || payload.schema !== 'ezs.listeners.v1' || !Array.isArray(payload.items)) {
                        $feedback.text('Réponse invalide.'); return;
                    }
                    const $fragment = $(document.createDocumentFragment());
                    payload.items.forEach(function (item) {
                        if (!item || typeof item.component !== 'string' || !Number.isInteger(item.port) || typeof item.tcp_listening !== 'boolean') return;
                        const $row = $('<tr>');
                        $('<td>').text(item.component).appendTo($row);
                        $('<td>').text(String(item.port)).appendTo($row);
                        $('<td>').text(item.tcp_listening ? 'Oui' : 'Non').appendTo($row);
                        $fragment.append($row);
                    });
                    $('#listener-rows').empty().append($fragment);
                    $feedback.text('Ports DEV vérifiés.');
                })
                .fail(function () { $feedback.text('Vérification indisponible.'); })
                .always(function () { $trigger.prop('disabled', false); });
        });
        $button.on('click', function () {
            $button.prop('disabled', true);
            $feedback.text('Actualisation en cours…');
            $.ajax({
                url: '/api/v2/environments',
                method: 'GET',
                dataType: 'json',
                timeout: 5000,
                cache: false
            }).done(function (payload) {
                if (!payload || payload.schema !== 'ezs.environments.v1' || !Array.isArray(payload.items)) {
                    $feedback.text('Réponse du catalogue non conforme.');
                    return;
                }
                const $fragment = $(document.createDocumentFragment());
                payload.items.forEach(function (item) {
                    if (!item || typeof item.component !== 'string' || typeof item.environment !== 'string' || typeof item.maintenance !== 'boolean') {
                        return;
                    }
                    const $row = $('<tr>');
                    $('<td>').text(item.component).appendTo($row);
                    $('<td>').text(item.environment.toUpperCase()).appendTo($row);
                    $('<td>').text(item.maintenance ? 'Disponible' : 'Non applicable').appendTo($row);
                    $fragment.append($row);
                });
                $rows.empty().append($fragment);
                $feedback.text('Catalogue actualisé.');
            }).fail(function () {
                $feedback.text('Actualisation indisponible. Le dernier catalogue affiché est conservé.');
            }).always(function () {
                $button.prop('disabled', false);
            });
        });
    });
})(window.jQuery);
