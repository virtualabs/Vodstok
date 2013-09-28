/**
 * Vodstok client
 *
 * Implements all the required method
 */

var VodClient = function(urlbase){
    this.urlbase = urlbase;
};

/**
 * Download a chunk
 *
 * @this {VodClient}
 * @param {string} chunk_id Chunk ID
 * @return {string} Chunk content as string
 */
VodClient.prototype.dlChunk = function(chunk_id) {
    var dfd = $.Deferred();

    (new AjaxSpooler()).add({
        url: this.urlbase+'?chunk='+chunk_id,
        crossDomain: true,
        success: (function(dfd){
            return function(data){
                dfd.resolve(data);
            };
        })(dfd),
        error: (function(dfd){
            return function(){
                dfd.reject();
            };
        })(dfd)
    });

    /* Returns a deferred. */
    return dfd.promise();
};

/**
 * Upload a chunk
 *
 * @this {VodClient}
 * @param {string} content Chunk content
 * @return {string} Chunk ID
 */
VodClient.prototype.uploadChunk = function(content, timeout) {
    /* Set timeout. */
    if (timeout == null) {
        timeout = 10000;
    }
    var dfd = $.Deferred();
    (new AjaxSpooler()).add({
        url: this.urlbase+'?'+(new Date().getTime()),
        crossDomain: true,
        type: 'POST',
        data: {
            'chunk': content
        },
        success: (function(dfd){
            return function(data){
                dfd.resolve(data);
            };
        })(dfd),
        error: (function(client, content, dfd){
            return function(xhr, error) {
	    	if ((error == 'timeout') || (error == 'abort')) {
			/* Timeout error, let's retry ! */
			console.log('[timeout] retry.');
			client.uploadChunk(content);
		} else {
                	dfd.reject();
		}
            };
        })(this, content, dfd),
        timeout: timeout
    });

    /* Returns a deferred. */
    return dfd.promise();
};

/**
 * Get endpoints
 *
 * @this {VodClient}
 * @return {array} List of endpoints URL
 */
VodClient.prototype.endpoints = function() {
    var dfd = $.Deferred();

    (new AjaxSpooler()).add({
        url: this.urlbase + '?endpoints',
        crossDomain: true,
        success: (function(dfd){
            return function(data){
                dfd.resolve(data.split(','));
            };
        })(dfd),
        error: (function(dfd){
            return function(){
                dfd.reject();
            };
        })(dfd),
        timeout: 5000
    });

    /* Returns a deferred. */
    return dfd.promise();
};

/**
 * Get client stats
 *
 * @this {VodClient}
 * @return {string} Statistics
 */
VodClient.prototype.stats = function() {
    var dfd = $.Deferred();

    (new AjaxSpooler()).add({
        url: this.urlbase+'?stats',
        crossDomain: true,
        success: (function(dfd){
            return function(data){
                dfd.resolve(data);
            };
        })(dfd),
        error: (function(dfd){
            return function(){
                dfd.reject();
            };
        })(dfd),
        timeout: 5000
    });

    /* Returns a deferred. */
    return dfd.promise();
};

/**
 * Register an url
 *
 * @this {VodClient}
 * @param {string} url Url to register
 */
VodClient.prototype.register = function(url) {
    var dfd = $.Deferred();

    /* Registration is done outside the main spool
     * to allow background registration tasks.
     * The Ajax spooler is only useful to prevent
     * too much cpu/memory usage when downloading
     * and decrypting chunks.
     */
    $.ajax({
        url: this.urlbase+'?register=' + url,
        crossDomain: true,
        success: (function(dfd){
            return function(data){
                dfd.resolve(data);
            };
        })(dfd),
        error: (function(dfd){
            return function(){
                dfd.reject();
            };
        })(dfd),
        timeout: 5000
    });

    /* Returns a deferred. */
    return dfd.promise();
};

/**
 * Test remote server
 *
 * @this {VodClient}
 */
VodClient.prototype.test = function() {
    var dfd = $.Deferred();

    var test_chunk = randomChunk();
    this.uploadChunk(test_chunk).done((function(inst, dfd, content){
        return function(cid) {
            inst.dlChunk(cid).done((function(inst, dfd, check){
                return function(content) {
                    if (check == content) {
                        dfd.resolve();
                    } else {
                        dfd.reject();
                    }
                };
            })(inst, dfd, content)).fail((function(dfd){
                return function() {
                    dfd.reject();
                };
            })(inst, dfd));
        };
    })(this, dfd, test_chunk)).fail((function(dfd){
        return function() {
            dfd.reject();
        };
    })(dfd));

    /* Return a deferred. */
    return dfd.promise();
};

