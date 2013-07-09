/***************************
 * File access in JS
 **************************/

function makeDl(filename, content) {
    var blob = new Blob([content]);
    var saver = saveAs(blob, filename);
}

makeDl('test.txt', 'foo !');
