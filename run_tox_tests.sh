#!/bin/sh
#
# Run tests for each supported python/pytest version combo.
#
# When attempting to run the entire set of tox environments in parallel, some issues
# arise due to the not-so-isolatedness of poetry dependency installation. To address
# those issues, this script runs each version of pytest in separate batches, so that
# each python version only runs a single suite at a time.
#

tox "$@" -p 5 -e py37-pytest71,py38-pytest71,py39-pytest71,py310-pytest71,py311-pytest71
tox "$@" -p 5 -e py37-pytest70,py38-pytest70,py39-pytest70,py310-pytest70,py311-pytest70
tox "$@" -p 5 -e py37-pytest62,py38-pytest62,py39-pytest62,py310-pytest62,py311-pytest62
tox "$@" -p 3 -e py37-pytest61,py38-pytest61,py39-pytest61
tox "$@" -p 3 -e py37-pytest60,py38-pytest60,py39-pytest60
tox "$@" -p 3 -e py37-pytest54,py38-pytest54,py39-pytest54
tox "$@" -p 3 -e py37-pytest53,py38-pytest53,py39-pytest53
tox "$@" -p 3 -e py37-pytest52,py38-pytest52,py39-pytest52
tox "$@" -p 3 -e py37-pytest51,py38-pytest51,py39-pytest51
tox "$@" -p 3 -e py37-pytest50,py38-pytest50,py39-pytest50
tox "$@" -p 3 -e py37-pytest46,py38-pytest46,py39-pytest46
tox "$@" -p 3 -e py37-pytest45,py38-pytest45,py39-pytest45
tox "$@" -p 3 -e py37-pytest44,py38-pytest44,py39-pytest44
tox "$@" -p 3 -e py37-pytest40,py38-pytest40,py39-pytest40
tox "$@" -p 3 -e py37-pytest39,py38-pytest39,py39-pytest39
tox "$@" -p 3 -e py37-pytest36,py38-pytest36,py39-pytest36
