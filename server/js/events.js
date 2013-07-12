
/**
 * Create or Get the instance of Trigger Manager service.
 *
 * @constructor
 * @this {events}
 */
var events = function() {
    this.triggers = {};
    this.subscribers = {};

    /* If TMService is already instancied, return instance (Singleton) */
    if (arguments.callee.instance) {
        return arguments.callee.instance;
    }
    else {
        arguments.callee.instance = this;
    }
};

/**
 * Subscribe to an event.
 *
 * This is done the nasty way by setting a specific property inside
 * the handler object. This property is then used to identify the
 * handler.
 *
 * @this {events}
 * @param {object} handler Handler reference.
 * @param {string} name Name of the event.
 * @param {object} callback Callback function to call when an event occurs.
 * @return {object} Return an uid for unsubscribe.
 */
events.prototype.subscribe = function(handler, name, callback) {
    /* Create the event if it does not exist */
    if (!(name in this.triggers)) {
        this.triggers[name] = {};
    }

    /* Add handler with associated callback */
    if (!handler.__tm_uuid) {
        handler.__tm_uuid = uuid();
        this.subscribers[handler.__tm_uuid] = handler;
    }
    this.triggers[name][handler.__tm_uuid] = callback;
};

/**
 * Unsubscribe to an event.
 *
 * @this {events}
 * @param {object} handler Handler reference
 * @param {string} name Event name
 */
events.prototype.unsubscribe = function(handler, name) {
    if ((handler != null) && (handler.__tm_uuid)) {
        if (name == null) {
            /* No specific event provided, remove all subscriptions. */
            for (var eventName in this.triggers) {
                if (handler.__tm_uuid in this.triggers[eventName]) {
                    delete this.triggers[eventName][handler.__tm_uuid];
                }
            }
        } else {
            /* Else, remove the specified handlers */
            if ((name in this.triggers) && (handler.__tm_uuid in this.triggers[name])) {
                delete this.triggers[name][handler.__tm_uuid];
            }
        }
    }
};

/**
 * Publish data for an event (notify all who have subscribe to it).
 *
 * @this {events}
 * @param {string} name Name of the event will be triggered.
 * @param {string[]} [data] An array of args to send to subscribers.
 */
events.prototype.publish = function(name, data) {
    if (name in this.triggers) {
        for (var subscriber in this.triggers[name]) {
            this.triggers[name][subscriber].apply(this.subscribers[subscriber], data);
        }
    }
};
