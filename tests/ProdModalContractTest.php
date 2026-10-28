<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$script=(string)file_get_contents($root.'/public/assets/ezs-prod-control.js');
$template=(string)file_get_contents($root.'/templates/infrastructure/index.html.twig');
foreach (['window.confirm(', 'window.prompt(', 'window.alert(', 'confirm(', 'prompt(', 'alert('] as $forbidden) {
    if (str_contains($script,$forbidden)) throw new RuntimeException('NATIVE_BROWSER_DIALOG_FORBIDDEN: '.$forbidden);
}
foreach (['id="prod-action-modal"','id="prod-action-confirm"','id="prod-action-modal-error"','bootstrap.bundle.min.js'] as $required) {
    if (!str_contains($template,$required)) throw new RuntimeException('PROD_MODAL_MISSING: '.$required);
}
foreach (['new window.bootstrap.Modal','modal.show()','modal.hide()','X-EZS-CSRF','confirmation:'] as $required) {
    if (!str_contains($script,$required)) throw new RuntimeException('PROD_MODAL_BEHAVIOR_MISSING: '.$required);
}
echo "EZS_PROD_MODAL_CONTRACT_OK\n";
