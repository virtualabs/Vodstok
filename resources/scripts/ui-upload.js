/**
 * Manage upload element
 */
(function($) {
    $.fn.bigblindUploader = function(options) {
        var settings = this.settings = $.extend({}, options);
        var initDfd = $.Deferred();

        var init = function() {
            console.debug('[BigblindUploader] Initializing ...');

            $(this).find('.btn-large').bind('click', function() {
                console.debug('[BigblindUploader] Clicked on upload button.');
            });
            
            initDfd.resolve();

            return initDfd.promise().done(function() {
                initialized();
            });
        }.bind(this);

        var initialized = function() {
            console.debug('[BigblindUploader] Initialized.');
        };

        init();
    };
})(jQuery);
