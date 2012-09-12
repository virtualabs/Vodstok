<?php

require_once('config.inc.php');

/** Chunks related stuff **/

function error($reason) {
	header('HTTP/1.0 404 '.$reason);
	die($reason);
}

function getFreeSpace() 
{
    if (is_dir(CHUNK_DIR))
    {
        if (is_link(CHUNK_DIR))
            $dir = opendir(readlink(CHUNK_DIR));
        else
        	$dir = opendir(CHUNK_DIR);
        if ($dir !== FALSE)
        {
        	$used = 0;
        	while (false !== ($entry = readdir($dir))) {
        		if (($entry!='.')&&($entry!='..')&&($entry!='.htaccess'))
        			$used += @filesize(CHUNK_DIR.'/'.$entry);
        	}
        	$left = QUOTA - $used;
            if ($left < 0)
                $left = 0;
        	closedir($dir);
            return $left;
        }
    }

    /* if an error occurred */
    error('ERR_BAD_DIRECTORY');
}

function deleteOlderChunk() {
    if (is_dir(CHUNK_DIR))
    {
        if (is_link(CHUNK_DIR))
            $dir = opendir(readlink(CHUNK_DIR));
        else
        	$dir = opendir(CHUNK_DIR);
            
        if ($dir !== false)
        {
        	$older = '';
        	$older_ts = time();		
                $used = 0;
                while (false !== ($entry = readdir($dir))) {
                        if (($entry!='.') && ($entry!='..') && ($entry!='.htaccess') && !is_dir($entry))
                        {
        			$entry_ts = @filemtime(CHUNK_DIR.'/'.$entry);
        			if ($entry_ts < $older_ts)
        			{
        				$older_ts = $entry_ts;
        				$older = $entry;
        			}
                        }
                }
        	closedir($dir);
        
        	/* unlink older file */
        	@unlink(CHUNK_DIR.'/'.$older);
            return;
        }
    }
    
    /* An error occurred */
    error('ERR_BAD_DIRECTORY: GetFreeSpace');
}

function clean($space)
{
	/* Check if space required is out of quota */
	if ($space>QUOTA)
		error('ERR_LOW_QUOTA');

    /* Get free space and clean to make some space */
	$free_space = getFreeSpace();
    do {
        /* If ok, remove an older chunk */
        deleteOlderChunk();
        
        /* Get freespace */
        $free_space = getFreeSpace();
        
    } while ($free_space < $space);
		
}

function dlChunk($id)
{
	/* Check id */
	if (preg_match('/^[0-9a-f]{32}$/i', $id))
	{
		/* check if chunk exists */
		if (file_exists(CHUNK_DIR.'/'.$id))
		{
			/* update modification time */
			touch(CHUNK_DIR.'/'.$id);
			echo @base64_encode(file_get_contents(CHUNK_DIR.'/'.$id));
		}
		else
			error('ERR_UNK');
	}
	else
		error('ERR_UNK');
}

function createChunk($data)
{
	/* Check max chunk size (32Ko) */
	$data = @base64_decode($data);
	if (strlen($data)>32768)
		error('ERR_TOO_LARGE');	

	/* Check if chunk exists */
	$id = md5($data.$_SERVER['REMOTE_ADDR'].time().rand());
	if (!file_exists(CHUNK_DIR.'/'.$id))
	{
		/* Make enough room for this chunk */
		clean(strlen($data));

		/* Create chunk */
		$f = fopen(CHUNK_DIR.'/'.$id,'wb');
		fwrite($f, $data);
		fclose($f);

		/* Chmod */
		chmod(CHUNK_DIR.'/'.$id, 0777);
	}
	die($id);
}

function dispStats()
{
	$quota = QUOTA;
	$usage = array();
    
    if (is_dir(CHUNK_DIR))
    {
        if (is_link(CHUNK_DIR))
            $dir = opendir(readlink(CHUNK_DIR));
        else
        	$dir = opendir(CHUNK_DIR);
            
        if ($dir !== false)
        {
            $chunks = 0;
            $min=time();
            
            while (false !== ($entry = readdir($dir))) {
                if (($entry!='.')&&($entry!='..')&&($entry!='.htaccess'))
                {
                    $entry_creation_date = @filemtime(CHUNK_DIR.'/'.$entry);
                    if ($entry_creation_date<$min)
                        $min = $entry_creation_date;
                    $chunks++;
                }
            }
            if ((time()-$min)>0)
                $usage_med = floor(($chunks*60)/(time()-$min));
            else
                $usage_med = 0;
        
        	$used = $chunks*32768;
        	if ($used>$quota)
        	   $used = $quota;
        	die('quota:'.$quota.',used:'.$used.',chunks:'.$chunks.',usage:'.$usage_med);
        }
    }
    
    /* An error occured */
    error('ERR_BAD_DIRECTORY');
    
}

/** Endpoints related stuff **/


function shouldRegister($ip, $endpoint) {
    if (is_dir(ENDPOINT_DIR))
    {
        if (is_link(ENDPOINT_DIR))
            $dir = opendir(readlink(ENDPOINT_DIR));
        else
        	$dir = opendir(ENDPOINT_DIR);
        
        if ($dir !== false)
        {
        	$older = '';
        	$limit = time()-3600;		
            $used = 0;
            $hash = md5($endpoint);
            while (false !== ($entry = readdir($dir))) {
                    if (($entry!='.')&&($entry!='..')&&($entry!='.htaccess'))
                    {
                    	$meta = @explode('-',$entry);
                    	$ip_ = $meta[0];
                    	$ep_ = $meta[1];
                    	if ($ip_===$ip)
                    	{
        					$entry_ts = @filemtime(ENDPOINT_DIR.'/'.$entry);
        					if ($entry_ts >= $limit)
                            {
                                closedir($dir);
        						return false;
                            }
        				}
        				if ($ep_==$hash)
                        {
                            closedir($dir);
                            return false;
                        }
                    }
            }
        	closedir($dir);
        	return true;
        }
    }
    
    /* An error occurred */
    error('ERR_BAD_DIRECTORY');
    return false;
}


function deleteOlderEndpoint() {
    if (is_dir(ENDPOINT_DIR))
    {
        if (is_link(ENDPOINT_DIR))
            $dir = opendir(readlink(ENDPOINT_DIR));
        else
        	$dir = opendir(ENDPOINT_DIR);
        
        if ($dir !== false)
        {
        	$older = '';
        	$older_ts = time();		
            $used = 0;
            while (false !== ($entry = readdir($dir))) {
                    if (($entry!='.')&&($entry!='..')&&($entry!='.htaccess'))
                    {
        		$entry_ts = @filemtime(ENDPOINT_DIR.'/'.$entry);
        		if ($entry_ts < $older_ts)
        		{
        			$older_ts = $entry_ts;
        			$older = $entry;
        		}
                    }
            }
        	closedir($dir);
        
        	/* unlink older file */
        	@unlink(ENDPOINT_DIR.'/'.$older);
            return;
        }
    }
    
    /* An error occured */
    error('ERR_BAD_DIRECTORY');
}


function registerEndpoint($ip,$url)
{
	/* Check last endpoint registration for this IP address */
	if (!shouldRegister($ip,$url))
		error('ERR_CANNOT_REGISTER');	

	/* Create endpoint file */
    if (is_dir(CHUNK_DIR))
    {
    	$f = fopen(ENDPOINT_DIR.'/'.$ip.'-'.md5($url),'wb');
    	fwrite($f, $url);
    	fclose($f);

    	/* chmod */
    	@chmod(ENDPOINT_DIR.'/'.$ip.'-'.md5($url), 0777);
    }
    else
        error('ERR_BAD_DIRECTORY');
}

function listRandomEndpoints()
{
    if (is_dir(ENDPOINT_DIR))
    {
        if (is_link(ENDPOINT_DIR))
            $dir = opendir(readlink(ENDPOINT_DIR));
        else
        	$dir = opendir(ENDPOINT_DIR);
        
        if ($dir !== false)
        {
        	$dir = opendir(ENDPOINT_DIR);
            $endpoints = array();
            while (false !== ($entry = readdir($dir))) {
                    if (($entry!='.')&&($entry!='..')&&($entry!='.htaccess'))
                        array_push($endpoints, file_get_contents(ENDPOINT_DIR.'/'.$entry));
            }
        	closedir($dir);
            
            /* shuffle and keep only the 5 first entries */
            shuffle($endpoints);
            die(implode(',',array_slice($endpoints,0,5)));
        }
    }
    
    /* An error occurred */
    error('ERR_BAD_DIRECTORY');
}

?>
