/**
 * Manage download bar element
 */
(function($) {
    $.fn.bigblindDownloader = function(options) {
        var settings = this.settings = $.extend({}, options);
        var initDfd = $.Deferred();

        var init = function() {
            console.debug('[BigblindDownloader] Initializing ...');
            
            $(this).bind('keypress', function(event) {
                if (event.which == 13) {
                    startDownload();
                }
            });

            initDfd.resolve();

            return initDfd.promise().done(function() {
                initialized();
            });
        }.bind(this);

        var initialized = function() {
            console.debug('[BigblindDownloader] Initialized.');
        };

        var startDownload = function() {
            var file = $(this).val();
            if (file) {
                console.debug('[BigblindDownloader] Downloading "' + file + '" ...');
                settings.vodka.download(file).done(function() {
                    $(this).val('');
                    console.debug('[BigblindDownloader] Downloading of "' + file + '" successfull.');
                }.bind(this)).fail(function() {
                    $(this).val('');
                    console.debug('[BigblindDownloader] Downloading of "' + file + '" failed.');
                }.bind(this));
            }
        }.bind(this);

        init();
    };
})(jQuery);
