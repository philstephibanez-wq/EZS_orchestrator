<?php
declare(strict_types=1);
$path=parse_url($_SERVER['REQUEST_URI']??'/',PHP_URL_PATH);
if($path==='/redirect'){http_response_code(302);header('Location: /target');return;}
if($path==='/cookie'){header('Set-Cookie: ezs_recipe=ok; Path=/; HttpOnly; SameSite=Lax');echo 'cookie';return;}
header('Content-Type: application/json; charset=utf-8');
echo json_encode(['path'=>$path,'method'=>$_SERVER['REQUEST_METHOD']??'GET',
 'body'=>file_get_contents('php://input'),'forwarded_proto'=>$_SERVER['HTTP_X_FORWARDED_PROTO']??'',
 'forwarded_host'=>$_SERVER['HTTP_X_FORWARDED_HOST']??'',
 'cookie'=>$_SERVER['HTTP_COOKIE']??''],JSON_UNESCAPED_SLASHES);
