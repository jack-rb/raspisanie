<?php
$ch = curl_init("http://127.0.0.1:8000/groups/");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

var_dump($response);
var_dump($httpCode);
?> 