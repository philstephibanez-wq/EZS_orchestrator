<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/Module/Infrastructure/WindowsNativeAttestation.php';
use Ezs\Web\Module\Infrastructure\WindowsNativeAttestation;
$fixture=['schema'=>'ezs.windows.attestation.v1','verified'=>true,'pid'=>123,'port'=>8510,
    'image_path'=>'C:\\Python\\python.exe','creation_filetime'=>'133456789012345678',
    'command_line_attested'=>false,'lifecycle_authorized'=>false];
$good=WindowsNativeAttestation::validateResult($fixture,123,8510);
if(($good['verified']??false)!==true || ($good['safe_to_cutover']??true)!==false)throw new RuntimeException('EXPECTED_SAFE_SNAPSHOT');
foreach(['pid','port','image_path','creation_filetime','command_line_attested','lifecycle_authorized'] as $key) {
    $bad=$fixture;
    unset($bad[$key]);
    if((WindowsNativeAttestation::validateResult($bad,123,8510)['verified']??true)!==false)throw new RuntimeException('MISSING_FIELD_ACCEPTED:'.$key);
}
$bad=$fixture;$bad['pid']=124;
if((WindowsNativeAttestation::validateResult($bad,123,8510)['verified']??true)!==false)throw new RuntimeException('PID_MISMATCH_ACCEPTED');
$bad=$fixture;$bad['image_path']='relative\\python.exe';
if((WindowsNativeAttestation::validateResult($bad,123,8510)['verified']??true)!==false)throw new RuntimeException('RELATIVE_PATH_ACCEPTED');
echo "EZS_WINDOWS_NATIVE_ATTESTATION_CONTRACT_OK\n";
