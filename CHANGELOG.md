# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


## [Unreleased]
## Changed
 - Add support for pytest versions 7.0 and 7.1
 - Relax pytest version pin to allow all versions under 8.x


## [1.2.5] — 2021-08-23
### Fixed
 - Avoid `ValueError: wrapper has not been initialized` when using implicit referential lambda fixtures (e.g. `name = lambda_fixture()`) in combination with `py.test --doctest-modules`


## [1.2.4] — 2020-12-28
### Changed
 - Add support for pytest version 6.2
 - Relax pytest version pin to allow all versions under 7.x


## [1.2.3] — 2020-11-02
### Fixed
 - Resolve error in `py.test --fixtures` due to `__module__` not properly being curried to fixture func


## [1.2.2] — 2020-11-02
### Fixed
 - Resolve error in `py.test --fixtures` when using `error_fixture`, `not_implemented_fixture`, or `disabled_fixture`


## [1.2.1] — 2020-11-02
### Changed
 - Add support for pytest version 6.1


## [1.2.0] — 2020-09-06
### Added
 - Allow certain arguments of wrapped fixture to be ignored w/ @wrap_fixture


## [1.1.1] — 2020-08-01
### Changed
 - Add support for pytest versions 4.6, 5.0, 5.1, 5.2, 5.3, 5.4, and 6.0


## [1.1.0] — 2019-08-14
### Added
 - Introduced `wrap_fixture` utility to extend fixtures while currying method signatures to feed pytest's dependency graph


## [1.0.0] — 2019-05-26
### Removed
 - Removed injection of pytest-lambda attrs into the `pytest` namespace


## [0.1.0] — 2019-02-02
### Fixed
 - Resolve error when executing `py.test --fixtures`


## [0.0.2] — 2018-07-29
### Added
 - Allow conditional raising of exceptions with `error_fixture`

### Changed
 - Updated README with more succinct examples, and titles for example sections


## [0.0.1] - 2018-07-28
### Added
 - `lambda_fixture`, `static_fixture`, `error_fixture`, `disabled_fixture`, and `not_implemented_fixture`
 - Totes rad README (that can actually be run with pytest! thanks to [pytest-markdown](https://github.com/Jc2k/pytest-markdown))
