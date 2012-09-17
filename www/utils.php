<?php

require_once('config.inc.php');

/** Helpers **/

/**
 * is_meta($entry_name)
 *
 * Check if an entry name corresponds to one of our metadata files
 */
 
function is_meta($entry_name)
{
    if (strlen($entry_name)>0)
        return ($entry_name[0]=='.');
    else
        return false;
} 

/**
 * test_write($dir)
 *
 * Try to write into a directory $dir.
 * Returns true if directory is writeable, false otherwise.
 */

function test_write($dir)
{
    /* If file exists, remove it */
    if (@file_exists($dir.'/.test'))
        @unlink($dir.'/.test');

    /* Create a test file */
    $f = @fopen($dir.'/.test','w');
    if ($f)
    {
        /* Write something */
        $data = rand();
        @fwrite($f, $data);
        @fclose($f);
        
        /* Reopen it */
        $f = @fopen($dir.'/.test','r');
        if ($f)
        {
            /* Check content */
            $content = @fread($f, 256);
            $res = ($content == $data);
            @fclose($f);
            return $res;
        }
        
        /* Remove test file */
        @unlink($dir.'./test');
    }
    
    /* An error occurred */
    return false;
}


/** Chunks related stuff **/


/**
 * error()
 *
 * Returns an error and stop processing. Errors are returned as 404 statuses,
 * followed by a reason.
 */

function error($reason) {
	header('HTTP/1.0 404 '.$reason);
	die($reason);
}


/**
 * Lock()
 *
 * Acquire a file lock in order to ensure quota management.
 * This function returns a handle on the file lock.
 */

function lock() {
        /* check if .size file exists */
        if (!file_exists(CHUNK_DIR.'/.lock'))
        {
            /* file does not exists, create it */
            $f = fopen(CHUNK_DIR.'/.lock','w');
            if ($f) {
                flock($f, LOCK_EX);
                fwrite($f, '');
                flock($f, LOCK_UN);
                fclose($f);
            }
            else
                error('ERR_UNK (lock file cannot be created)');
        }
        
        /* Open lock file */
        $f = fopen(CHUNK_DIR.'/.lock','r');
        flock($f, LOCK_EX);
        return $f;
}


/**
 * unlock(handle)
 * 
 * Unlock a previously acquired file lock.
 */

function unlock($f) {
    @flock($f, LOCK_UN);
    @fclose($f);
}


/**
 * getConsumedSpace()
 * 
 * Read the .size file located in the chunk directory. This file contains
 * the total size used by all chunks.
 */

function getConsumedSpace()
{
        /* check if .size file exists */
        if (!file_exists(CHUNK_DIR.'/.size'))
        {
            /* file does not exists, create it */
            $f = fopen(CHUNK_DIR.'/.size','w');
            if ($f) {
                fwrite($f, '0');
                fclose($f);
            }
            else
                error('ERR_UNK (quota file cannot be created)');
        }
        else
        {
            /* read .size file */
            $f = fopen(CHUNK_DIR.'/.size','r');
            if ($f) {
                $consumed = fread($f, 4096);
                fclose($f);
                return $consumed;
            }
            else
                error('ERR_UNK (quota file cannot be read)');
        }
}


/**
 * setConsumedSpace($space)
 *
 * Set the content of the .size file with $space. A lock must be acquired
 * before doing so, to be sure another request does not modify the server's
 * state.
 */

function setConsumedSpace($space_left) {
        /* check if .size file exists */
        /* file does not exists, create it */
        $f = fopen(CHUNK_DIR.'/.size','w');
        if ($f) {
            fwrite($f, $space_left);
            fclose($f);
        }
        else
            error('ERR_UNK (quota file cannot be created)');
}


/** 
 * getFreeSpace()
 *
 * Compute the remaining disk space based on the defined quota and returns it.
 */
 
function getFreeSpace()
{
    $free_space = QUOTA - getConsumedSpace();
    if ($free_space < 0)
        $free_space = 0;
    return $free_space;
}


/**
 * deleteOldestChunk()
 *
 * Remove the oldest chunk (based on last modification date).
 * If a chunk has been downloaded before, its modification date is recent
 * and this chunk will not be removed. Only old chunks that are not requested
 * for a while are removed, ensuring popular chunks persistence.
 */

function deleteOldestChunk() {
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
                    if (!is_meta($entry) && !is_dir($entry))
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
        
            /* compute the new size */
            $entry_size = filesize(CHUNK_DIR.'/'.$older);
            $left = getConsumedSpace() - $entry_size;
            if ($left < 0)
                $left = 0;
            setConsumedSpace($left);
            
        	/* unlink older file */
        	@unlink(CHUNK_DIR.'/'.$older);
            return;
        }
    }
    
    /* An error occurred */
    error('ERR_BAD_DIRECTORY: GetFreeSpace');
}


/**
 * clean($required_space)
 *
 * This function remove as many old chunks as possible to obtain $required_space
 * bytes available, based on the defined quota.
 *
 * If the required space is greater than the defined quota, throws an error.
 */
 
function clean($space)
{
	/* Check if space required is out of quota */
	if ($space>QUOTA)
		error('ERR_LOW_QUOTA');

    /* Get free space and clean to make some space */
    $free_space = getFreeSpace();
    if ($free_space < $space)
    {
        do {
            /* If ok, remove the oldest chunk */
            deleteOldestChunk();
            
            /* Get freespace */
            $free_space = getFreeSpace();
        } while ($free_space < $space);
    }		
}


/**
 * dlChunk($chunk_id)
 *
 * Echo the content of a given chunk if present in our chunks directory.
 * Echoed content is base64 encoded.
 */
 
function dlChunk($id)
{
	/* Check id */
	if (preg_match('/^[0-9a-f]{32}$/i', $id))
	{
		/* check if chunk exists */
		if (file_exists(CHUNK_DIR.'/'.$id))
		{
			/* update modification time */
			@touch(CHUNK_DIR.'/'.$id);
			echo @base64_encode(file_get_contents(CHUNK_DIR.'/'.$id));
		}
		else
			error('ERR_UNK');
	}
	else
		error('ERR_UNK');
}


/**
 * createChunk($chunk_data)
 *
 * Creates a chunk in CHUNK_DIR.
 */
 
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
        $lock = lock();
        
		/* Make enough room for this chunk */
		clean(strlen($data));

		/* Create chunk */
		$f = fopen(CHUNK_DIR.'/'.$id,'wb');
		fwrite($f, $data);
		fclose($f);
        
        /* Update consumed size */
        $consumed = getConsumedSpace();
        setConsumedSpace($consumed+strlen($data));

		/* Chmod */
		chmod(CHUNK_DIR.'/'.$id, 0777);
        
        unlock($lock);
	}
	die($id);
}

function dispStats()
{
	$quota = QUOTA;
	$usage = array();
    
    $consumed = getConsumedSpace();
    $free_space =getFreeSpace();
        
    if (is_dir(CHUNK_DIR))
    {
        /*
        if (is_link(CHUNK_DIR))
            $dir = opendir(readlink(CHUNK_DIR));
        else
        	$dir = opendir(CHUNK_DIR);
            
        if ($dir !== false)
        {
            $chunks = 0;
            $min=time();
            
            while (false !== ($entry = readdir($dir))) {
                if (!is_meta($entry) && !is_dir($entry))
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
        */
        die('quota:'.$quota.',used:'.$consumed.',chunks:'.floor($consumed/32768.0).',usage:0');
    }
    
    /* An error occured */
    error('ERR_BAD_DIRECTORY');
    
}

/** Endpoints related stuff **/


/**
 * shouldRegister($ip, $server)
 *
 * Check if server registration is required.
 */

function shouldRegister($ip, $server) {
    if (is_dir(SERVERS_DIR))
    {
        if (is_link(SERVERS_DIR))
            $dir = opendir(readlink(SERVERS_DIR));
        else
        	$dir = opendir(SERVERS_DIR);
        
        if ($dir !== false)
        {
        	$older = '';
        	$limit = time()-3600;		
            $used = 0;
            $hash = md5($server);
            while (false !== ($entry = readdir($dir))) {
                    if (!is_meta($entry) && !is_dir($entry))
                    {
                    	$meta = @explode('-',$entry);
                    	$ip_ = $meta[0];
                    	$ep_ = $meta[1];
                    	if ($ip_===$ip)
                    	{
        					$entry_ts = @filemtime(SERVERS_DIR.'/'.$entry);
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


/**
 * deleteOldestServer()
 * 
 * Delete the oldest server from the directory
 */

function deleteOldestServer() {
    if (is_dir(SERVERS_DIR))
    {
        if (is_link(SERVERS_DIR))
            $dir = opendir(readlink(SERVERS_DIR));
        else
        	$dir = opendir(SERVERS_DIR);
        
        if ($dir !== false)
        {
        	$older = '';
        	$older_ts = time();		
            $used = 0;
            while (false !== ($entry = readdir($dir))) {
                    if (!is_meta($entry) && !is_dir($entry))
                    {
        		$entry_ts = @filemtime(SERVERS_DIR.'/'.$entry);
        		if ($entry_ts < $older_ts)
        		{
        			$older_ts = $entry_ts;
        			$older = $entry;
        		}
                    }
            }
        	closedir($dir);
        
        	/* unlink older file */
        	@unlink(SERVERS_DIR.'/'.$older);
            return;
        }
    }
    
    /* An error occured */
    error('ERR_BAD_DIRECTORY');
}


/**
 * registerServer($ip, $url)
 * 
 * Registers a server into the directory. $ip is required
 * to limit flooding.
 */

function registerServer($ip, $url)
{
	/* Check last endpoint registration for this IP address */
	if (!shouldRegister($ip,$url))
		error('ERR_CANNOT_REGISTER');	

	/* Create endpoint file */
    if (is_dir(CHUNK_DIR))
    {
    	$f = fopen(SERVERS_DIR.'/'.$ip.'-'.md5($url),'wb');
    	fwrite($f, $url);
    	fclose($f);

    	/* chmod */
    	@chmod(SERVERS_DIR.'/'.$ip.'-'.md5($url), 0777);
    }
    else
        error('ERR_BAD_DIRECTORY');
}


/**
 * listRandomServers()
 *
 * Returns a list of <=5 servers
 */

function listRandomServers()
{
    if (is_dir(SERVERS_DIR))
    {
        if (is_link(SERVERS_DIR))
            $dir = opendir(readlink(SERVERS_DIR));
        else
        	$dir = opendir(SERVERS_DIR);
        
        if ($dir !== false)
        {
        	$dir = opendir(SERVERS_DIR);
            $servers = array();
            while (false !== ($entry = readdir($dir))) {
                    if (!is_meta($entry) && !is_dir($entry))
                        array_push($servers, file_get_contents(SERVERS_DIR.'/'.$entry));
            }
        	closedir($dir);
            
            /* shuffle and keep only the 5 first entries */
            shuffle($servers);
            die(implode(',',array_slice($servers,0,5)));
        }
    }
    
    /* An error occurred */
    error('ERR_BAD_DIRECTORY');
}

