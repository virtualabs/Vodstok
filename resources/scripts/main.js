$(document).ready(function() {
    vodka = new Vodka();

    $('body').bigblindui({
        'vodka': vodka,
        'downloadBar': $('#search'),
        'uploadElement': $('#uploader'),
        'registerElement': $('#register-server')
    });
});
