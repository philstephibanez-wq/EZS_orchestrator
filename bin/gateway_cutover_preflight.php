<?php
declare(strict_types=1);
// Read-only deployment gate. Does not start, stop, reconfigure or signal services.
$root=dirname(__DIR__);
$stateFile=$root.'/runtime/v2-prod/processes.json';
$gateway=$root.'/runtime_components/prod_gateway_php/router.php';
$legacy=$root.'/runtime_components/prod_gateway/server.py';
function checkHttp(string $uri): array {
 $ctx=stream_context_create(['http'=>['timeout'=>3,'ignore_errors'=>true,'follow_location'=>0]]);
 $body=@file_get_contents($uri,false,$ctx);
 $headers=$http_response_header??[];
 $code=preg_match('~^HTTP/\\S+ (\\d{3})~',(string)($headers[0]??''),$m)?(int)$m[1]:0;
 return ['http'=>$code,'body'=>is_string($body)?$body:null];
}
$state=is_file($stateFile)?json_decode((string)file_get_contents($stateFile),true):null;
$status=checkHttp('http://127.0.0.1:8510/__ezscore_gateway_status');
$payload=is_string($status['body'])?json_decode($status['body'],true):null;
$expected=is_array($payload)&&($payload['protocol']??null)==='ezscore.online-gateway.v3'
 && ($payload['ok']??null)===true && ($payload['backend_port']??null)===8511;
$preflight=[
 'schema'=>'ezs.gateway.cutover.preflight.v1',
 'mode'=>'READ_ONLY_NO_CUTOVER',
 'files'=>['php_candidate'=>is_file($gateway),'python_rollback'=>is_file($legacy)],
 'prod_state_present'=>is_array($state),
 'prod_gateway_status_http'=>$status['http'],
 'prod_gateway_protocol_valid'=>$expected,
 'prod_maintenance'=>$expected?($payload['maintenance']??null):null,
 'cutover_blockers'=>[
  'No validated production PHP gateway process manager / persistent launch',
  'PROD lifecycle still launches and verifies Python gateway on 8510',
  'Infrastructure ownership diagnostic still expects python.exe on 8510',
  'Real SSO, media auth and streaming tests not approved',
  'No exercised rollback procedure with verified process identity',
 ],
 'can_cutover'=>false,
];
echo json_encode($preflight,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n";
exit($expected&&is_array($state)&&is_file($gateway)&&is_file($legacy)?0:1);
