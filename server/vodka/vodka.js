/**
 * Vodstok Simple downloader
 *
 * @param [url] url Optional URL.
 */
var VodkaSimpleDl = function(url) {
    this.nchunks = 0;
    this.progress = 0;
    this.download_started = false;

    $('#progressbar').progressbar({
        value: 0
    });

    this.events = new events();
    this.events.subscribe(this, 'progress', this.onProgress);

    /* Parse the requested url, or the current location
     * if url is not provided
     */
    if (url != null) {
        var uri = new Uri(url);
        var ep_uri = uri.protocol()+'://'+uri.host()+':'+uri.port()+uri.path();
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
        });
    } else {
        console.log('No file to download');
    }
};

/**
 * Download a file given the first chunk and key.
 *
 * @this {VodkaSimpleDl}
 * @param {string} chunk First chunk URL
 * @param {object} key Decryption key
 */
VodkaSimpleDl.prototype.dlFile = function(chunk, key) {
    var dfd = $.Deferred();

    this.dlChunk([chunk], key, true).done((function(inst, dfd, key){
        return function(blob){
            var infos= blob.split('|');
            var filename = infos[0];
            var version = infos[1];
            var chunks = infos[2].split(',');
            if (filename != 'metadata') {
                inst.nchunks = chunks.length;
                inst.progress = 0;
                inst.download_started = true;

                /* Launch the download of all chunks. */
                inst.dlChunk(chunks, key, true).done((function(filename, dfd){
                    return function(content){
                        dfd.resolve([filename, content]);
                    };
                })(filename, dfd));
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
        };
    })(this, dfd, key)).fail((function(dfd){
        return function(){ dfd.reject(); };
    })(dfd));

    return dfd.promise();
};

/**
 * Download a given chunk and optionnaly parses its content.
 *
 * @this {VodkaSimpleDl}
 * @param {array} chunks Array of chunk to download, decrypt and concatenate.
 * @param {object} key Decryption key
 * @param {bool} last Return raw content if true.
 * @return {Deferred} Returns a deferred.
 */
VodkaSimpleDl.prototype.dlChunk = function(chunks, key, last) {
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
                if (inst.download_started) {
                    inst.progress++;
                    inst.events.publish('progress', [inst.progress]);
                }
                dfd.resolve();
            };
        })(this, dfd_, blobs, chunk_array[i].id, key)).fail((function(dfd){
            return function(){dfd.reject();};
        })(dfd));
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
                var chunks = infos[1].split(',');
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

VodkaSimpleDl.prototype.onProgress = function(progress) {
    $('#progressbar').progressbar('value', (progress/this.nchunks)*100);
};

/**
 * Encryption routine
 */
var encryptChunk = function(data, key) {
    var iv = CryptoJS.SHA512(key).slice(0, 16);
    return CryptoJS.AES.encrypt(data, key, { iv: iv});
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

//var test = new VodkaSimpleDl('http://virtualabs.fr/vodstok/#7f7f3e635b1b2bbf613d677462f8704c-86aec4b638f84315bcb6fad67dc7aed5');
var test = new VodkaSimpleDl('http://virtualabs.fr/vodstok/#aa99a1b0fcce7f5934c1d6b52164f8ad-9433d26cdfd1606bb09efccb45a8139c');
//var test = new VodkaSimpleDl();
/*
client.endpoints().done(function(ep){
    console.log(ep);
});
client.uploadChunk('test').done(function(data){
    console.log(data);
});
client.dlChunk('00b585ef4cb7e81721903e00df4e9f7f').done(function(data){
    console.log(data);
});*/
