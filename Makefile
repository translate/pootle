CWD = $(shell pwd)
SRC_DIR = ${CWD}/pootle
DOCS_DIR = ${CWD}/docs
STATIC_DIR = ${SRC_DIR}/static
ASSETS_DIR = $(shell python -c "from pootle.settings import *; print(STATIC_ROOT)")
JS_DIR = ${STATIC_DIR}/js
CSS_DIR = ${STATIC_DIR}/css
IMAGES_DIR = ${STATIC_DIR}/images
SPRITE_DIR = ${IMAGES_DIR}/sprite
FORMATS=--formats=bztar
TEST_ENV_NAME = pootle_test_env

.PHONY: all build clean sprite test pot help docs assets

all: help

build: docs assets
	python setup.py sdist ${FORMATS} ${TAIL}

assets:
	npm --version
	node --version
	cd ${JS_DIR} && \
	npm cache clear && \
	npm install && \
	cd ${CWD}
	python manage.py webpack --extra=--display-error-details
	mkdir -p ${ASSETS_DIR}
	python manage.py collectstatic --noinput --clear -i node_modules -i .tox -i docs ${TAIL}
	python manage.py assets build ${TAIL}
	chmod 664 ${ASSETS_DIR}.webassets-cache/*

travis-assets:
	npm --version
	node --version
	if [ -d "${ASSETS_DIR}.webassets-cache/" ]; then \
		echo "eating cache - yum!"; \
	else \
		cd ${JS_DIR} && \
		npm install && \
		cd ${CWD}; \
		python manage.py webpack --dev --nowatch; \
		mkdir -p ${ASSETS_DIR}; \
		python manage.py collectstatic --noinput --clear -i node_modules -i .tox -i docs ${TAIL}; \
		python manage.py assets build ${TAIL}; \
		chmod 664 ${ASSETS_DIR}.webassets-cache/*; \
	fi

docs:
	# Make sure that the submodule with docs theme is pulled and up-to-date.
	git submodule update --init
	# The following creates the HTML docs.
	# NOTE: cd and make must be in the same line.
	cd ${DOCS_DIR}; make SPHINXOPTS="-W -q -j 4" html ${TAIL}

docs-review: docs
	python -mwebbrowser file://$(shell pwd)/${DOCS_DIR}/_build/html/index.html

sprite:
	glue --sprite-namespace="" --namespace="" ${SPRITE_DIR} --css=${CSS_DIR} --img=${IMAGES_DIR}
	optipng -o7 ${IMAGES_DIR}/sprite.png

clean:
	npm cache clear
	rm -rf ${TEST_ENV_NAME}

test: clean assets
	virtualenv ${TEST_ENV_NAME} && \
	source ${TEST_ENV_NAME}/bin/activate && \
	pip install -r requirements/tests.txt && \
	python setup.py test

pot:
	@${SRC_DIR}/tools/createpootlepot

get-translations:
	ssh pootle.locamotion.org ". /var/www/sites/pootle/env/bin/activate; python /var/www/sites/pootle/src/manage.py sync_stores --verbosity=1 --project=pootle"
	rsync -az --delete --exclude="LINGUAS" --exclude=".translation_index" --exclude=pootle-terminology.po pootle.locamotion.org:/var/www/sites/pootle/translations/pootle/ ${SRC_DIR}/locale
	for po in $$(find ${SRC_DIR}/locale -name "*.po"); do msgcat $$po > $$po.2 && mv $$po.2 $$po; done

put-translations:
	rsync -azv --progress --exclude="*~" --exclude="*.mo" --exclude="LC_MESSAGES" --exclude=unicode --exclude="LINGUAS" --exclude=".translation_index" --exclude=pootle-terminology.po ${SRC_DIR}/locale/ pootle.locamotion.org:/var/www/sites/pootle/translations/pootle/
	ssh pootle.locamotion.org ". /var/www/sites/pootle/env/bin/activate; python /var/www/sites/pootle/src/manage.py update_stores --verbosity=1 --project=pootle"

linguas:
	@${SRC_DIR}/tools/make-LINGUAS.sh 80 > ${SRC_DIR}/locale/LINGUAS

jslint:
	cd ${JS_DIR} \
	&& npm run lint

publish-pypi:
	python setup.py sdist ${FORMATS} upload

help:
	@echo "Help"
	@echo "----"
	@echo
	@echo "  assets - collect and rebuild the static assets"
	@echo "  build - create sdist with required prep"
	@echo "  docs - build Sphinx docs"
	@echo "  docs-review - launch webbrowser to review docs"
	@echo "  sprite - create CSS sprite"
	@echo "  clean - remove any temporal files"
	@echo "  test - run test suite"
	@echo "  pot - update the POT translations templates"
	@echo "  get-translations - retrieve Pootle translations from server (requires ssh config for pootletranslations)"
	@echo "  linguas - update the LINGUAS file with languages over 80% complete"
	@echo "  publish-pypi - publish on PyPI"
