/**
 * Ajax requests spooler
 *
 * @constructor
 * @this {AjaxSpooler}
 */
var AjaxSpooler = function() {
    this.requests = [];
    this.current = 0;
    this.max = 3;

    if (arguments.callee.instance) {
        return arguments.callee.instance;
    } else {
        arguments.callee.instance = this;
    }
};

/**
 * Add a request to the spooler
 *
 * @this {AjaxSpooler}
 * @param {object} request Ajax request (for $.ajax)
 */
AjaxSpooler.prototype.add = function(request) {
    /* Override success and error callbacks */
    if (request.success) {
        request.success = (function(inst, callback){
            return function(data){
                inst.done();
                callback(data);
            };
        })(this, request.success);
    }
    if (request.error) {
        request.error = (function(inst, callback){
            return function(){
                inst.done();
                callback();
            }
        })(this, request.error);
    }
    
    /* Enqueue request and run */
    this.requests.push(request);
    this.update();
};

/**
 * Final callback.
 *
 * @this {AjaxSpooler}
 */
AjaxSpooler.prototype.done = function() {
    /* Enqueue other requests if any */
    this.current--;
    this.update();
};

/**
 * Update the spooler
 * 
 * Check if the spooler can launch some requests and launch them if any.
 *
 * @this {AjaxSpooler}
 */
AjaxSpooler.prototype.update = function() {
    /* Is there some slots available ? */
    if (this.current < this.max) {
        while ((this.current < this.max) && (this.requests.length > 0)) {
            this.current++;
            $.ajax(this.requests.pop(0));
        }
    }
};
