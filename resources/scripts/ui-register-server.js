/**
 * Manage share element
 */
(function($) {
    $.fn.bigblindRegisterServer = function(options) {
        var settings = this.settings = $.extend({}, options);
        var initDfd = $.Deferred();

        var init = function() {
            console.debug('[bigblindRegisterServer] Initializing ...');

            $(this).bind('submit', function(event) {
                event.preventDefault();
                var endpoint = $(this.server).val();

                if (endpoint) {
                    console.debug('[bigblindRegisterServer] Try registering : "' + endpoint + '" ...');
                    settings.vodka.register(endpoint);

                    toggleRegisterForm();
                }

                return false;
            });

            $(this).bind('reset', function(event) {
                $(this).find('label').removeClass('active');
            });

            vodka.events.subscribe(this, 'vodka.register.ko', function() {
                console.debug('[bigblindRegisterServer] Registering failed.');
                toggleRegisterForm();
                $(this).reset();
            });

            vodka.events.subscribe(this, 'vodka.register.ok', function() {
                console.debug('[bigblindRegisterServer] Registering successfull.');
                toggleRegisterForm();
                $(this).trigger('reset');
            });
            
            initDfd.resolve();

            return initDfd.promise().done(function() {
                initialized();
            });
        }.bind(this);

        var toggleRegisterForm = function() {
            $(this).toggleClass('hidden');
            $(settings.loader).toggleClass('hidden');
        }.bind(this);

        var initialized = function() {
            console.debug('[bigblindRegisterServer] Initialized.');
        };

        init();
    };
})(jQuery);
