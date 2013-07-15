<?php

/**
 * Constants
 *
 * These constants must be defined here because no config.inc.php is available.
 */

define('CHUNK_DIR', 'chunks');
define('ENDPOINT_DIR','endpoints');
@require_once('utils.php');

/* Error counter */
$errors = 0;

/** 
 * Check if an install is required
 *
 * This check returns True only if the 'config.inc.php' already exists.
 */

function requires_install()
{
    return (!file_exists('config.inc.php'));
}


/**
 * Create the 'config.inc.php' file
 */

function create_config_file($quota)
{
    $f = fopen('./config.inc.php','w');
    if ($f)
    {
        $content = "<?php
define('QUOTA_MB',".(int)($_POST['quota']).");"."
define('CHUNK_DIR','chunks');
define('SERVERS_DIR','endpoints');
define('MAX_SERVERS',50);
/*
DO NOT MODIFY OR REMOVE THE FOLLOWING LINES
*/

define('QUOTA',QUOTA_MB*1024*1024);
define('VERSION','1.2.4');
";
        fwrite($f, $content);
        fclose($f);

        /* Success */
        return TRUE;
    }
    else
        /* Error */
        return false;
}


/**
 * Check install
 */

if (!requires_install())
{
    /* If install is ok, then redirect to the index page. */
    header('Location: '.dirname($_SERVER['REQUEST_URI']));
    die('install already done');
}

/* Check if a quota is set */
if (isset($_POST['quota']))
{
    /* Quota set, create config file and redirect to the index page */
    if (create_config_file($_POST['quota']))
    {
        header('Location: '.dirname($_SERVER['REQUEST_URI']));
        die('install ok');
    }
    else
        $errors++;
}

/* Displays the page */

?>
<!DOCTYPE html>
<html>
<head>
<title>Vodstok - Install</title>
<link rel="stylesheet" type="text/css" href="style.css" />

</head>
<body>
<div id="main">
	<div id="header">
		<div id="logo"/>
	</div>
	<div id="install">
	    <form action="" method="POST">
        <div class="block-header"><img src="images/redstar.png" alt="" title=""/>INSTALL</div>
		<div class="block-content">
            You are about to install your Vodstok node and to be a part of Vodstok's network, thank you. The installation process is quite easy
            and do not require any database settings. However, file access rights must have been correctly configured in order for the install
            process to run properly.<br/>
            Vodstok server uses two specific directories, <i>chunks</i> and <i>endpoints</i> with write access enabled.<br/><br/>
            <div class="important">Directories write access status:</div>
            <div id="tests">
                <?php
                
                /*
                 *  Directory access-rights checks
                 */

                /* check current dir access */
                echo('<br/>Current directory');
                if (test_write('.'))
                    echo('<span class="ok"></span>');
                else {
                    if (!@chmod('.',0777))
                    { 
                        echo('<span class="ko"></span>');
                        $errors++;
                    }
                    else
                        echo('<span class="ok"></span>');
                }
                
                /* check write access to chunks dir */
                echo('<br/>Chunks directory');
                if (test_write(CHUNK_DIR))
                    echo('<span class="ok"></span>');
                else {
                    if (!@chmod(CHUNK_DIR,0777))
                    { 
                        echo('<span class="ko"></span>');
                        $errors++;
                    }
                    else
                        echo('<span class="ok"></span>');
                }
                    
                /* check write access to repositories dir */
                echo('<br/>Endpoints directory');
                if (test_write(ENDPOINT_DIR))
                    echo('<span class="ok"></span>');
                else {
                    if (!@chmod(ENDPOINT_DIR,0777))
                    { 
                        echo('<span class="ko"></span>');
                        $errors++;
                    }
                    else
                        echo('<span class="ok"></span>');
                }
                ?>
                <br/>
                <?php if($errors>0) {
                    echo('<br/><br/><span class="error">Some errors occured. Please check your directories write access and try again. The installation process will not complete until write access rights are not correctly set.</span>');
                }
                ?>
                <br/>
            </div>
		</div>
		<?php if($errors==0) { ?>
        <div class="block-header"><img src="images/redstar.png" alt="" title=""/>SERVER STORAGE QUOTA</div>
		<div class="block-content">
            Select the desired disk space allocated to Vodstok<br/>(you may be able to change this later in the configuration file):<br/><br/>
            <label for="quota">Quota :</label>
            <select name="quota" id="quota">
                <option value="500">500 MB</option>
                <option value="1024">1 GB</option>
                <option value="2048">2 GB</option>
                <?php if(is_largefs_compliant()) {?>
                <option value="4096">4 GB</option>
                <option value="10240">10 GB</option>
                <option value="51200">50 GB</option>
                <option value="102400">100 GB</option>
                <option value="204899">200 GB</option>
                <?php } ?>
            </select>
            <br/><br/>
		</div>
		<?php } ?>
        <div class="block-header"><img src="images/redstar.png" alt="" title=""/>NOTES</div>
		<div class="block-content">
            Be careful, directory listing of <i>chunks</i> and <i>endpoints</i> directories should not be available. Please make sure your 
            Apache configuration allows htaccess files. Another solution consists in disabling the Apache's option Index in your host setup. 
		</div>
		<br/><br/>
		<center><input class="russian" type="submit" value="INSTALL RIGHT NOW !"/></center>
		<br/>
		</form>

	</div>
</div>



</body>
</html>
