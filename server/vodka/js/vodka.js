/**
 * UUID
 */
var uuid = function(){
    'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
            return v.toString(16);
    });
}

/**
 * Our event manager
 */

var evtmanager = function(){
    this.subscribers = [];
    this.subscriptions = {};
};

evtmanager.prototype.subscribe = function(subscriber, evt, callback) {
    if ('__em_uuid' in subscriber) {
        subscriber.__em_uuid = uuid();
        this.subscribers.push(subscriber.__em_uuid);
    }
    if (!(evt in this.subscriptions[subscriber.__em_uuid])) {
        this.subscriptions[subscriber.__em_uuid][evt] = [subscriber, callback];
    }
};

evtmanager.prototype.publish = function(evt, params) {
    for (var id in this.subscribers) {
        if (evt in this.subscriptions[this.subscribers[id]]) {
            this.subscriptions[this.subscribers[id]][evt][1].apply(
                this.subscriptions[this.subscribers[id]][evt][0],
                params
            );
        }
    }
};


/* Vodka JS main code */
console.log('main');
var handler = function(){
    this.onFoo = function(param){
        console.log('foo :'+param);
    }
}

var em = new evtmanager();
var handler = new handler();

em.subscribe(handler, 'foo', handler.onFoo);
em.publish('foo', 'bar');

