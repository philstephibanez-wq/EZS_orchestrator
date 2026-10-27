'use strict';
/* EZS UI V2: jQuery is loaded once by the base page; read-only REST. */
(function ($) {
    if (!$) { return; }

    $(function () {
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
