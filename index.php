<?php
$host = "127.0.0.1:8000";
$uri = $_SERVER['REQUEST_URI'];

// Отладка
error_log("Request URI: " . $uri);

// Проксируем запрос
$ch = curl_init("http://" . $host . $uri);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

// Отладка
error_log("Response code: " . $httpCode);
error_log("Response: " . substr($response, 0, 100));

http_response_code($httpCode);
echo $response;
?> 