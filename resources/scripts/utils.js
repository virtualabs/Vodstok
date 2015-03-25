/**
 * Utils
 */

/**
 * Pick a random item from  a list of items
 *
 * @param {array} items Item array
 * @return {object} Item picked
 */
var choice = function(items) {
    return items[Math.floor(Math.random()*items.length)];
};


/**
 * Convert an hex string to ascii
 *
 * @param {string} hex Hex string
 * @return {string} Ascii string
 */
function hex2a(hex) {
    var str = '';
    for (var i = 0; i < hex.length; i += 2)
        str += String.fromCharCode(parseInt(hex.substr(i, 2), 16));
    return str;
}

/**
 * Convert an ascii string to hex form
 *
 * @param {string} str String to convert
 * @return {string} Hex string
 */
function toHex(str) {
    var hex = '';
    for(var i=0;i<str.length;i++) {
        hex += ''+str.charCodeAt(i).toString(16);
    }
    return hex;
}

/**
 * Shuffle an array
 */
function shuffle(o){ //v1.0
        for(var j, x, i = o.length; i; j = parseInt(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);
        return o;
};

/**
 * Convert a simple array into an indexed-array
 */
function makeChunkArray(array){
    var output = [];
    /* copy content */
    for (var i in array) {
        output.push({
            id: i,
            object: array[i]
        });
    }

    /* Shuffle output */
    return shuffle(output);
};

/**
 * UUID
 */
var uuid = function(){
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
    });
};

/**
 * Generate a random string
 */
function randomChunk(size)
{
    return CryptoJS.lib.WordArray.random(size).toString(CryptoJS.enc.Base64);
}


function generate_key() {
    return CryptoJS.lib.WordArray.random(16).toString(CryptoJS.enc.Hex);
}

function blob2str(blob) {
    var dfd = $.Deferred();
    var fr = new FileReader();
    fr.onloadend = (function(inst, dfd){
        return function(event) {
            dfd.resolve(event.target.result);
        };
    })(this, dfd);
    fr.readAsArrayBuffer(blob);

    return dfd.promise();
}