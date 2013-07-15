<?php

require_once('utils.php');

echo('Testing chunk dir ... ');
if (!test_write(CHUNK_DIR))
    echo('KO<br/>');
else
    echo('OK<br/>');
    
echo('Testing endpoint dir ... ');
if (!test_write(ENDPOINT_DIR))
    echo('KO<br/>');
else
    echo('OK<br/>');
    
echo('Testing root dir ...');
if (!test_write('.'))
    echo('KO<br/>');
else
    echo('OK<br/>');
