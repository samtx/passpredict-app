const gulp = require('gulp');
const sass = require('gulp-sass');
const sourcemaps = require('gulp-sourcemaps');
const del = require('del');

const staticDir = 'app/static/';


const compileSass = function () {
    return gulp.src(staticDir + 'sass/**/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest(staticDir + 'css/'));
}

// watch for changes
const watchSource = function (done) {
    gulp.watch([staticDir+'/sass/**/*.scss'], exports.default);
    done();
  };


const clean = function() {
    return del([
        staticDir + 'css/main.css',
    ]);
};


exports.default = gulp.series(clean, compileSass)


exports.watch = gulp.series(
    exports.default,
    watchSource
);
