<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/Module/Infrastructure/DevOwnershipAssessment.php';

use Ezs\Web\Module\Infrastructure\DevOwnershipAssessment;

$check = new DevOwnershipAssessment();
$state = ['php_pid'=>1201,'caddy_pid'=>1202];
$php = ['schema'=>'ezs.windows.attestation.v1','verified'=>true,'pid'=>1201,'port'=>8791,
    'image_path'=>'H:\\PHP\\php-8.5-x64\\php-cgi.exe','creation_filetime'=>'133456789012345678',
    'command_line_attested'=>false,'lifecycle_authorized'=>false];
$caddy = ['schema'=>'ezs.windows.attestation.v1','verified'=>true,'pid'=>1202,'port'=>8790,
    'image_path'=>'H:\\Caddy\\caddy.exe','creation_filetime'=>'133456789012345679',
    'command_line_attested'=>false,'lifecycle_authorized'=>false];
$ok = $check->assess($state,$php,$caddy);
if (!$ok['all_snapshots_consistent'] || $ok['lifecycle_authorized'] || $ok['safe_to_cutover']) {
    throw new RuntimeException('CONSISTENT_SNAPSHOT_BAD_DECISION');
}
foreach (['pid'=>9999,'port'=>8510,'image_path'=>'H:\\other\\python.exe',
          'creation_filetime'=>'bad','verified'=>false,'command_line_attested'=>true] as $key=>$value) {
    $bad = $php;
    $bad[$key] = $value;
    if ($check->assess($state,$bad,$caddy)['php_identity_consistent']) {
        throw new RuntimeException('BAD_PHP_SNAPSHOT_ACCEPTED:'.$key);
    }
}
$bad = $caddy;
$bad['image_path']='H:\\Tools\\caddy.exe.txt';
if ($check->assess($state,$php,$bad)['caddy_identity_consistent']) {
    throw new RuntimeException('BAD_CADDY_IMAGE_ACCEPTED');
}
if ($check->assess(['php_pid'=>1201,'caddy_pid'=>1201],$php,$caddy)['state_valid']) {
    throw new RuntimeException('SAME_PID_ACCEPTED');
}
echo "EZS_DEV_OWNERSHIP_ASSESSMENT_CONTRACT_OK\n";
