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
    $.ajax({
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
VodClient.prototype.uploadChunk = function(content) {
    var dfd = $.Deferred();
    $.ajax({
        url: this.urlbase,
        crossDomain: true,
        type: 'POST',
        data: {
            'chunk': data
        },
        success: (function(dfd){
            return function(data){
                dfd.resolve(data);
            };
        })(dfd),
        error: (function(dfd){
            return function() {
                dfd.reject();
            };
        })(dfd)
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

    $.ajax({
        url: this.urlbase + '?endpoints',
        crossDomain: true,
        success: (function(dfd){
            return function(data){
                dfd.resolve(data.split(','));
            };
        })(dfd),
        error: (function(dfd){
            return function(data){
                dfd.reject();
            };
        })(dfd)
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

    $.ajax({
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
        })(dfd)
    });

    /* Returns a deferred. */
    return dfd.promise();
};


/***************************
 * File access in JS
 **************************/

function makeDl(filename, content) {
    var blobprev = new Blob(['foo']);
    var blobnext = new Blob(['bar']);
    var thisblob = new Blob([content]);
    var blob = new Blob([blobprev, thisblob, blobnext]);
    var saver = saveAs(blob, filename);
}

var client = new VodClient('http://virtualabs.fr/vodstok/');
client.endpoints().done(function(ep){
    console.log(ep);
});
/*
client.uploadChunk('test').done(function(data){
    console.log(data);
});
client.dlChunk('00b585ef4cb7e81721903e00df4e9f7f').done(function(data){
    console.log(data);
});*/
