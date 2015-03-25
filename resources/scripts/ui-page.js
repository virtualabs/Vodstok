/**
 * Manage UI page elements
 */
(function($) {
    $.fn.bigblindui = function(options) {
        var settings = this.settings = $.extend({}, options);

        var init = function() {
            initPages();

            if (settings.downloadBar) {
                $(settings.downloadBar).bigblindDownloader();
            }

            if (settings.uploadElement) {
                $(settings.uploadElement).bigblindUploader();
            }

            if (settings.registerElement) {
                $(settings.registerElement).bigblindRegisterServer({
                    'loader': $('#register-server-progress'),
                    'vodka': settings.vodka
                });
            }
        };

        var initPages = function() {
            $(this).find('.content').fullpage({
                anchors: ['share', 'presentation-what', 'presentation-why', 'presentation-how'],
                verticalCentered: true,
                resize: true,
                sectionSelector: '.page'
            });
        }.bind(this);

        init();
    };
})(jQuery);
