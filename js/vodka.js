/**
 * Chunk wrapper
 */

var Chunk = function(blob, index, key, content) {
    if (content == null) {
        this.blob = blob
        this.index = index;
        this.key = key;
        this.prepared = false;
        this.content = null;
    } else {
        this.prepared = true;
        this.content = content;
    }
    this.chunk_size = (32*1024 - 16);
};

Chunk.prototype.prepare = function() {
    var dfd = $.Deferred();

    if (!this.prepared) {
        /* Get content and encrypt it. */
        var chunk_content = this.blob.slice(this.index*this.chunk_size, (this.index+1)*this.chunk_size, "application/octet-stream");

        /* Send our chunk */
        blob2str(chunk_content).done((function(chunk_obj, dfd){
            return function(chunk) {
                chunk_obj.setContent(
                    encryptChunk(
                        CryptoJS.lib.WordArray.fromArrayBuffer(chunk),
                        chunk_obj.key
                    ).toString()
                );
                dfd.resolve(chunk_obj.content);
            };
        })(this, dfd));
    } else {
        dfd.resolve(this.content);
    }

    return dfd.promise();
};

Chunk.prototype.setContent = function(content) {
    this.content = content;
    this.prepared = true;
};

Chunk.prototype.release = function() {
    delete this.content;
    delete this.key;
    delete this.blob;
};

function raw_chunk(content) {
    return new Chunk(null, null, null, content);
};

/**
 * Vodstok Simple downloader
 *
 * @param [url] url Optional URL.
 */
var Vodka = function(url) {

    /* CONSTANTS */
    this.MODE_WAIT = 0;
    this.MODE_DL = 1;
    this.MODE_UL = 2;
    this.MODE_DISCOVERY = 3;

    this.baseUrl = url;

    this.nchunks = 0;
    this.progress = 0;
    this.mode = this.MODE_WAIT;
    this.endpoints = [];

    this.events = new events();
    this.events.subscribe(this, 'progress', this.onProgress);

    /* If TMService is already instancied, return instance (Singleton) */
    if (arguments.callee.instance) {
        return arguments.callee.instance;
    }
    else {
        arguments.callee.instance = this;
    }

};

/**
 * Retrieve this endpoint URL
 *
 * @this {Vodka}
 * @return {object} This endpoint's client
 */
Vodka.prototype.getUrl = function() {
    if (this.baseUrl == null) {
        var uri = new Uri(document.location.href);
    } else {
        var uri = new Uri(this.baseUrl);
    }
    var ep_uri = uri.protocol()+'://'+uri.host();
    if (uri.port()) {
        ep_uri += ':'+uri.port()
    }
    ep_uri += uri.path();
    return ep_uri;
};

/**
 * Discover existing nodes:
 * 1. query endpoints to identify servers
 * 2. check potential servers
 * 3. when enough servers found, send the 'vodka.network.ok' event.
 *
 * On error, send the 'vodka.network.failed' event.
 */
Vodka.prototype.discover = function() {
    this.mode = this.MODE_DISCOVERY;
    this.events.publish('vodka.network.discover');
    this.queryEndpoints().done((function(inst){
        return function(endpoints) {
            inst.events.publish('vodka.network.check', [endpoints.length]);
            /* Once the endpoints retrieved, check them */
            inst.checkServers().done((function(inst){
                if (inst.endpoints.length >= 3) {
                    inst.events.publish('vodka.network.ok');
                } else {
                    inst.events.publish('vodka.network.ko');
                }
            })(inst));
        };
    })(this)).fail((function(inst){
        return function() {
            inst.events.publish('vodka.network.ko');
        };
    })(this));
};

/**
 * Launch a download
 *
 * @this {Vodka}
 * @param {string} url
 */
Vodka.prototype.download = function(url) {
    var dfd = $.Deferred();

    /* Parse the requested url, or the current location
     * if url is not provided
     */
    if (url != null) {
        var uri = new Uri(url);
        var ep_uri = uri.protocol()+'://'+uri.host();
        if (uri.port()) {
            ep_uri += ':'+uri.port()
        }
        ep_uri += uri.path();
        var chunk_infos = uri.anchor();
    } else {
        chunk_infos = document.location.hash.slice(1);
        var ep_uri = document.location.protocol+'//';
        ep_uri += document.location.host;
        ep_uri += document.location.pathname;
    }

    /* Check chunk sanity */
    var chunk_patt =  /^[0-9a-f]{32}-[0-9a-f]{32}$/i;
    if (chunk_patt.test(chunk_infos)) {
        var chunk_id = chunk_infos.split('-')[1];
        var key = chunk_infos.split('-')[0];

        /* Launch the download */
        var chunk = this.dlFile(ep_uri+'?'+chunk_id, key).done(function(content){
            var len = content[1].length;
            var buf = new ArrayBuffer(content[1].length);
            var view = new Uint8Array(buf);
            for (var i = 0; i < len; i++) {
                  view[i] = content[1].charCodeAt(i) & 0xff;
            }
            makeDl(content[0], view);
        }).fail(function(){
            dfd.reject();
        });
    } else {
        dfd.reject();
    }

    return dfd.promise();
};

/**
 * Download a file given the first chunk and key.
 *
 * @this {Vodka}
 * @param {string} chunk First chunk URL
 * @param {object} key Decryption key
 */
Vodka.prototype.dlFile = function(chunk, key) {
    var dfd = $.Deferred();

    this.dlChunk([chunk], key, true).done((function(inst, dfd, key){
        return function(blob){
            try {
                var infos= blob.split('|');
                var filename = infos[0];
                var version = infos[1];
                var chunks = infos[2].split(',');

                if (version.split('.').length != 3) {
                    dfd.reject();
                } else {
                    if (filename != 'metadata') {
                        inst.nchunks = chunks.length;
                        inst.progress = 0;
                        inst.mode = inst.MODE_DL;

                        /* Display the download button */
                        //$('#dlbtn').button({label:'Download &laquo;' + filename + '&raquo;'})
                        $('#dlbtn').html('Download &laquo;' + filename + '&raquo;')
                            .unbind('click')
                            .bind('click', (function(inst, filename, dfd){
                                return function(){
                                    $('#dlbtn').hide();
                                    $('#progressbar').show();

                                    /* Launch the download of all chunks. */
                                    inst.dlChunk(chunks, key, true).done((function(filename, dfd){
                                        return function(content){
                                            dfd.resolve([filename, content]);
                                        };
                                    })(filename, dfd));
                                };
                            })(inst, filename, dfd))
                            .show();
                    } else {
                        /* Retrieve the complete metadata and launch the download of all chunks. */
                        dfd.resolve(inst.dlChunk(chunks, key, false)).done((function(inst, dfd, key){
                            return function(content){
                                var infos= content.split('|');
                                var filename = infos[0];
                                var version = infos[1];
                                var chunks = infos[2].split(',');

                                inst.nchunks = chunks.length;
                                inst.progress = 0;
                                inst.download_started = true;

                                /* Launching the dl of all chunks */
                                inst.dlChunk(chunks, key, trye).done((function(filename, dfd){
                                    return function(content){
                                        dfd.resolve([filename, content]);
                                    };
                                })(filename, dfd));
                            };
                        })(this, dfd, key));
                    }
                }
            } catch (err) {
                dfd.reject();
            }
        };
    })(this, dfd, key)).fail((function(inst, dfd){
        return function(){
            inst.mode = this.MODE_WAIT;
            inst.progress = 0;
            dfd.reject();
        };
    })(this, dfd));

    return dfd.promise();
};

/**
 * Download a given chunk and optionnaly parses its content.
 *
 * @this {Vodka}
 * @param {array} chunks Array of chunk to download, decrypt and concatenate.
 * @param {object} key Decryption key
 * @param {bool} last Return raw content if true.
 * @return {Deferred} Returns a deferred.
 */
Vodka.prototype.dlChunk = function(chunks, key, last) {
    var dfd = $.Deferred();

    /* Is it the last chunk ? */
    if (last == null)
        last = false;

    /* Deferred tasks */
    var deferreds = [];
    /* Output blob array */
    var blobs = new Array();

    /* Loop on every chunk and download it */
    var chunk_array = makeChunkArray(chunks);
    for (var i in chunk_array) {
        var client = new VodClient(chunk_array[i].object.split('?')[0]);
        var cid = chunk_array[i].object.split('?')[1];
        var dfd_ = $.Deferred();
        client.dlChunk(cid).done((function(inst, dfd, blobs, id, key){
            return function(content){
                content = decryptChunk(content, key);
                blobs[id] = content;
                if (inst.mode == inst.MODE_DL) {
                    inst.progress++;
                    inst.events.publish('progress', [inst.progress]);
                }
                dfd.resolve();
            };
        })(this, dfd_, blobs, chunk_array[i].id, key)).fail((function(dfd){
            return function(){
                dfd.reject();
            };
        })(dfd_));
        deferreds.push(dfd_.promise());
    }
    /* Once done, put all in one and return it */
    $.when.apply($, deferreds).then((function(inst, dfd, blobs, key, last){
        return function(){
            if (last) {
                /* Return content */
                dfd.resolve(blobs.join(''));
            } else {
                /* Parse content and returns a deferred. */
                var content = blobs.join('');
                var infos = content.split('|');
                var filename = infos[0];
                var version = infos[1];
                var chunks = infos[2].split(',');
                if (filename == 'metadata') {
                    return inst.dlChunk(chunks, key, false);
                } else {
                    return inst.dlChunk(chunks, key, true);
                }
            }
        }
    })(this, dfd, blobs, key, last)).fail((function(dfd){
        return function(){
            dfd.reject();
        };
    })(dfd));

    return dfd.promise();
};

/**
 * Retrieve and test endpoints (from a single endpoint)
 *
 * @this {Vodka}
 * @param [url] url Endpoint url
 */
Vodka.prototype.queryEndpoints = function(url, depth) {
    var dfd = $.Deferred();

    if (url != null) {
        var uri = new Uri(url);
        var ep_uri = uri.protocol()+'://'+uri.host();
        if (uri.port()) {
            ep_uri += ':'+uri.port();
        }
        ep_uri += uri.path();
    } else {
        var ep_uri = this.getUrl();
    }

    if (this.endpoints.indexOf(ep_uri) < 0) {
        this.endpoints.push(ep_uri);
    }

    /* Query endpoint for other endpoints */
    var client = new VodClient(ep_uri);
    client.endpoints().done((function(inst, ep, jq){
        return function(endpoints) {

            /* If max depth not reached */
            if (depth == null) {
                depth = 0;
            }
            if (depth < 2) {
                var deferreds = [];
                for (var i in endpoints) {
                    if (inst.endpoints.indexOf(endpoints[i]) < 0) {
                        inst.endpoints.push(endpoints[i]);
                    }
                    inst.events.publish('vodka.network.discover', [inst.endpoints.length]);
                    var dfd_ = jq.Deferred();
                    inst.queryEndpoints(endpoints[i], depth + 1).always(
                        (function(dfd){
                            return function(){
                                dfd.resolve();
                            };
                        })(dfd_)
                    );
                    deferreds.push(dfd_.promise());
                }
                jq.when.apply(jq, deferreds).then((function(inst, dfd){
                    return function() {
                        /* Keep only 10 endpoints max */
                        if (inst.endpoints.length > 10) {
                            inst.endpoints.slice(0,10);
                        }
                        dfd.resolve(inst.endpoints);
                    };
                })(inst, dfd));
            } else {
                dfd.resolve();
            }
        };
    })(this, ep_uri, $)).fail((function(dfd){
        return function(){
            dfd.reject();
        };
    })(dfd));

    /* Returns a deferred */
    return dfd.promise();
};

/**
 * Check discovered servers
 *
 * @this {Vodka}
 */
Vodka.prototype.checkServers = function() {
    var dfd = $.Deferred();

    var deferreds = [];
    var random_data = randomChunk(16);
    this.checkedServers = 0;
    this.originalNbServers = this.endpoints.length;

    for (var i in this.endpoints) {
        var c = new VodClient(this.endpoints[i]);
        var dfd_ = $.Deferred();
        c.uploadChunk(raw_chunk(random_data), 2000).fail((function(inst, ep){
            return function() {
                inst.endpoints.splice(inst.endpoints.indexOf(ep),1);
            };
        })(this, this.endpoints[i])).done((function(inst, ep){
            return function(cid) {
                var patt = /^[0-9a-f]{32}$/i;
                if (!patt.test(cid)) {
                    inst.endpoints.splice(inst.endpoints.indexOf(ep), 1);
                }
            };
        })(this, this.endpoints[i])).always((function(inst, dfd){
            return function(){
                inst.checkedServers++;
                dfd.resolve();
                inst.events.publish('vodka.network.progress', [inst.checkedServers, inst.originalNbServers]);
            };
        })(this, dfd_));
        deferreds.push(dfd_.promise());
    }
    $.when.apply($, deferreds).then((function(inst, dfd){
        return function(){
            if (inst.endpoints.length == 0) {
                dfd.reject();
            } else {
                dfd.resolve(inst.endpoints);
            }
        };
    })(this, dfd));

    /* Returns a deferred */
    return dfd.promise();
};

/**
 * Upload a file
 *
 * @this {Vokda}
 * @param {string} content File content
 * @param {string} key Encryption key
 */
Vodka.prototype.uploadFile = function(filename, blob, key, metafile) {
    var dfd = $.Deferred();

    this.progress = 0;
    this.mode = this.MODE_UL;

    /* Clean filename before starting upload */
    while (filename.indexOf('../')>=0) {
        filename = filename.replace('../','');
    }
    filename = filename.replace(' ','_');
    filename = filename.replace('/','_');
    filename = filename.replace('\\','');

    /* Split content in chunks */
    var chunks = [];
    var chunk_size = (32*1024 - 16);
    var nb_chunks = blob.size/chunk_size;
    if ((nb_chunks * chunk_size) < blob.size) {
        nb_chunks++;
    }
    this.nchunks = nb_chunks + 1;
    /*
    for (var i = 0; i < nb_chunks; i++) {
        chunks.push(blob.slice(i*chunk_size, (i+1)*chunk_size, "application/octet-stream"));
    }*/
    for (var i = 0; i < nb_chunks; i++) {
        chunks.push(new Chunk(blob, i, key));
    }

    /* Upload chunks and collect eps and ids */
    var deferreds = [];
    var chunk_refs = new Array();
    for (var i in chunks) {
        var dfd_ = $.Deferred();
        this.uploadChunk(chunks[i], key).done((function(inst, dfd, chunks, i){
            return function(cid) {
                chunks[i] = cid[0]+'?'+cid[1];
                inst.progress++;
                inst.events.publish('progress', [inst.progress]);
                dfd.resolve();
            };
        })(this, dfd_, chunk_refs, i)).fail((function(dfd){
            return function(){
                dfd.reject();
            };
        })(dfd));
        deferreds.push(dfd_.promise());
    }
    $.when.apply($, deferreds).then((function(inst, dfd, refs, metafile){
        return function(){
            /* get metadata */
            var metadata = refs.join(',');
            if (metafile) {
                var c = 'metadata|1.2.5|'+refs.join(',');
            } else {
                var c = filename+'|1.2.5|'+refs.join(',');
            }

            if (c.length > chunk_size) {
                inst.uploadFile('metadata', new Blob([c]), key, true).done((function(inst, dfd){
                    return function(fid) {
                        dfd.resolve(fid);
                    };
                })(inst, dfd)).fail((function(dfd){
                    return function() {
                        dfd.reject();
                    };
                })(dfd));
            } else {
                inst.uploadChunk(new Chunk(new Blob([c]), 0, key)).done((function(inst, dfd){
                    return function(cid) {
                        inst.progress = this.nchunks;
                        inst.events.publish('progress', [inst.progress]);
                        dfd.resolve(cid[0]+'?'+ (new Date().getTime()) +'#'+key+'-'+cid[1]);
                    };
                })(inst, dfd)).fail((function(inst, dfd){
                    return function() {
                        inst.mode = this.MODE_WAIT;
                        inst.progress = 0;
                        dfd.reject();
                    };
                })(inst, dfd));
            }
        };
    })(this, dfd, chunk_refs, metafile));

    /* Return deferred. */
    return dfd.promise();
};

/**
 * Upload a chunk
 *
 * @this {Vodka}
 * @param {string} chunk Chunk content
 * @param {string} key Encryption key
 * @return {Deferred} Deferred.
 */
Vodka.prototype.uploadChunk = function(chunk) {
    var dfd = $.Deferred();

    /* Check if we have some endpoints tested */
    if (this.endpoints && this.endpoints.length > 0) {

        /* Pick a random endpoint */
        var endpoint_url = choice(this.endpoints);
        var client = new VodClient(endpoint_url);

        /* Send our chunk */
        client.uploadChunk(chunk).done((function(ep, dfd){
            return function(id) {
                dfd.resolve([ep,id]);
            };
        })(endpoint_url, dfd)).fail((function(dfd){
            return function() {
                dfd.reject();
            };
        })(dfd));
    }

    /* Returns a deferred. */
    return dfd.promise();
};


/**
 * Register an url
 *
 * Fires a vodka.register.ok event if everything went right,
 * a vodka.register.ko if something went wrong.
 *
 * @this {Vodka}
 * @param {string} url Url to register
 */
Vodka.prototype.register = function(url) {
    var client = new VodClient(this.getUrl());
    if (client) {
        client.register(url).done((function(inst){
            return function() {
                inst.events.publish('vodka.register.ok');
            };
        })(this)).fail((function(inst){
            return function() {
                inst.events.publish('vodka.register.ko');
            };
        })(this));
    }
};

/**
 * Propagate registered servers to other servers.
 *
 * This task must be launched asynchronously and in
 * background, in a way this is transparent to the
 * user and ensure Vodstok network's perenity.
 * This must be executed only once.
 */
Vodka.prototype.propagate = function(url) {
    if (this.endpoints.length > 3) {
        targets = this.endpoints.slice(0,3);
        for (var i in targets) {
            for (var j in targets) {
                if (i != j) {
                    var client = new VodClient(targets[i]);
                    client.register(targets[j]);
                }
            }
        }
    }
};

/**
 * Update progress bar.
 *
 * @this {Vodka}
 * @param {int} progress Progress to display.
 */
Vodka.prototype.onProgress = function(progress) {
    var percent = Math.ceil((progress/this.nchunks)*100);
    var progressBarWidth = percent * $('#progressbar').width() / 100;
    $('#progressbar').find('div').css('width',progressBarWidth+'px').html(percent + "%&nbsp;");
};


/**
 * Encryption routine
 */
var encryptChunk = function(data, key) {
    var iv = CryptoJS.enc.Hex.parse(CryptoJS.SHA512(CryptoJS.enc.Hex.parse(key)).toString().slice(0,32));
    return CryptoJS.AES.encrypt(data, CryptoJS.enc.Hex.parse(key), { iv: iv});
};

/**
 * Decryption routine
 */
var decryptChunk = function(data, key) {
    var iv = CryptoJS.enc.Hex.parse(CryptoJS.SHA512(CryptoJS.enc.Hex.parse(key)).toString().slice(0,32));
    return hex2a(CryptoJS.AES.decrypt(data, CryptoJS.enc.Hex.parse(key), { iv: iv}).toString());
};

/***************************
 * File access in JS
 **************************/

function makeDl(filename, content) {
    var blob = new Blob([content], {type: "application/octet-stream"});
    var saver = saveAs(blob, filename);
}

