'use strict';

var gulp = require('gulp'),
    $ = require('gulp-load-plugins')({
      pattern: ['gulp-*', 'gulp.*', 'main-bower-files'],
      replaceString: /\bgulp[\-.]/
    });

var config = {
    sassPath: './resources/styles',
    imagePath: './resources/images',
    scriptPath: './resources/scripts',
    bowerDir: './bower_components' 
};

gulp.task('connect', function() {
    $.connect.server({
        root: 'app',
        livereload: true
    });
});

gulp.task('bower', function() { 
    return $.bower().pipe(gulp.dest(config.bowerDir));
});

gulp.task('scripts', function() {
  return gulp.src($.mainBowerFiles().concat(config.scriptPath + '/**/*'))
    .pipe($.filter('*.js'))
    .pipe($.concat('main.js'))
    .pipe($.uglify())
    .pipe(gulp.dest('app/public/script'));
});

gulp.task('vendors', function() {
  return gulp.src($.mainBowerFiles())
    .pipe($.filter('*.js'))
    .pipe($.concat('vendor.js'))
    .pipe($.uglify())
    .pipe(gulp.dest('app/public'))
});

gulp.task('images', function() {
  return gulp.src(config.imagePath + '/**/*')
    .pipe($.cache($.imagemin({ optimizationLevel: 5, progressive: true, interlaced: true })))
    .pipe(gulp.dest('app/public/image'));
});

gulp.task('html', function () {
  gulp.src('./app/*.html')
    .pipe($.connect.reload());
});

gulp.task('styles', function() {
  return $.rubySass(
              config.sassPath + '/main.scss',
              {
                  style: 'compressed',
                  loadPath: [
                      config.bowerDir + '/materialize/sass'
                  ]
              }
         )
         .pipe($.autoprefixer('last 1 version'))
         .pipe(gulp.dest('app/public/style'));
});

gulp.task('fonts', function() {
    return gulp.src(config.bowerDir + '/materialize/dist/font/**')
               .pipe($.filter('**/*.{eot,svg,ttf,woff}'))
               .pipe(gulp.dest('app/public/font'));
});

gulp.task('watch', function () {
  gulp.watch([config.sassPath + '/**/*.scss'], ['styles']);
  gulp.watch([config.imagePath + '/*'], ['images']);
  gulp.watch([config.scriptPath + '/*'], ['scripts']);
  gulp.watch(['bower.json'], ['bower']);
  gulp.watch(['./app/*.html'], ['html']);
});

gulp.task('default', ['scripts', 'images', 'fonts', 'styles', 'html', 'connect', 'watch']);
