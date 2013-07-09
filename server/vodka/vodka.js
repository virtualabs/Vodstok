var choice = function(items) {
    return items[Math.floor(Math.random()*items.length)];
};

function hex2a(hex) {
    var str = '';
    for (var i = 0; i < hex.length; i += 2)
        str += String.fromCharCode(parseInt(hex.substr(i, 2), 16));
    return str;
}
function toHex(str) {
    var hex = '';
    for(var i=0;i<str.length;i++) {
        hex += ''+str.charCodeAt(i).toString(16);
    }
    return hex;
}
/**
 * Crypto layer
 */

var VodkaSimpleDl = function(url) {
    if (url != null) {
        /* Parse url */
        var uri = new Uri(url);
        var ep_uri = uri.protocol()+'://'+uri.host()+':'+uri.port()+uri.path();
    } else {
        uri = document.location.fragment;
    }
    
    var chunk_infos = uri.anchor();
    var chunk_id = chunk_infos.split('-')[1];
    var key = chunk_infos.split('-')[0];

    /* Get the first chunk */
    var chunk = this.dlFile(ep_uri+'?'+chunk_id, key).done(function(content){
        console.log('content length: '+content[1].length)
        var len = content[1].length;
        var buf = new ArrayBuffer(content[1].length);
        var view = new Uint8Array(buf);
        for (var i = 0; i < len; i++) {
              view[i] = content[1].charCodeAt(i) & 0xff;
        }
        makeDl(content[0], view);
    });
    
};

VodkaSimpleDl.prototype.dlFile = function(chunk, key) {
    var dfd = $.Deferred();

    this.dlChunk([chunk], key, true).done((function(inst, dfd, key){
        return function(blob){
            console.log(blob);
            //blob = hex2a(blob);
            console.log(blob);
            var infos= blob.split('|');
            var filename = infos[0];
            var version = infos[1];
            var chunks = infos[2].split(',');
            console.log(chunks);
            if (filename != 'metadata') {
                inst.dlChunk(chunks, key, true).done((function(filename, dfd){
                    return function(content){
                        dfd.resolve([filename, content]);
                    };
                })(filename, dfd));
            } else {
                dfd.resolve(inst.dlChunk(chunks, key, false));
            }
        };
    })(this, dfd, key)).fail((function(dfd){
        return function(){ dfd.reject(); };
    })(dfd));

    return dfd.promise();
};

VodkaSimpleDl.prototype.dlChunk = function(chunk, key, last) {
    var dfd = $.Deferred();

    if (last == null)
        last = false;
    console.log(last);
    var deferreds = [];
    var blobs = new Array();
    for (var i in chunk) {
        var client = new VodClient(chunk[i].split('?')[0]);
        var cid = chunk[i].split('?')[1];
        var dfd_ = $.Deferred();
        client.dlChunk(cid).done((function(dfd, blobs, id, key){
            return function(content){
                content = decryptChunk(content, key);
                blobs[id] = content;
                dfd.resolve();
            };
        })(dfd_, blobs, i, key)).fail((function(dfd){
            return function(){dfd.reject();};
        })(dfd));
        deferreds.push(dfd_.promise());
    }
    $.when.apply($, deferreds).then((function(inst, dfd, blobs, key, last){
        return function(){
            if (last) {
                console.log(blobs);
                dfd.resolve(blobs.join(''));
            } else {
                console.log(blobs);
                var content = blobs.join('');
                console.log(content);
                var infos = content.split('|');
                var filename = infos[0];
                var chunks = infos[1].split(',');
                console.log(chunks);
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

var encryptChunk = function(data, key) {
    var iv = CryptoJS.SHA512(key).slice(0, 16);
    return CryptoJS.AES.encrypt(data, key, { iv: iv});
};

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
