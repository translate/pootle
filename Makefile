CWD = $(shell pwd)
SRC_DIR = ${CWD}/pootle
DOCS_DIR = ${CWD}/docs
STATIC_DIR = ${SRC_DIR}/static
ASSETS_DIR = $(shell pootle shell --plain -c  "from django.conf import settings; print(settings.STATIC_ROOT)")
JS_DIR = ${STATIC_DIR}/js
CSS_DIR = ${STATIC_DIR}/css
IMAGES_DIR = ${STATIC_DIR}/images
SPRITE_DIR = ${IMAGES_DIR}/sprite

POOTLE_CMD = $(shell sh -c "command -v pootle")
ifeq ($(POOTLE_CMD),)
	POOTLE_CMD=python manage.py
endif

.PHONY: all build sprite pot help docs assets

all: help

build: docs assets
	python setup.py sdist --formats=bztar ${TAIL}

assets:
	npm --version
	node --version
	cd ${JS_DIR} && \
	npm install && \
	cd ${CWD}
	cp ${JS_DIR}/node_modules/select2/dist/js/i18n/*.js ${JS_DIR}/select2_l10n/
	echo 'Compiling js i18n'
	${POOTLE_CMD} compilejsi18n -v0
	${POOTLE_CMD} webpack --extra=--display-error-details
	mkdir -p ${ASSETS_DIR}

	echo 'Collecting static'
	${POOTLE_CMD} collectstatic -v0 --noinput --clear -i node_modules -i .tox -i docs ${TAIL}

	echo 'Building assets'
	${POOTLE_CMD} assets -v0 build ${TAIL}

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
		cp ${JS_DIR}/node_modules/select2/dist/js/i18n/*.js ${JS_DIR}/select2_l10n/; \
		${POOTLE_CMD} compilejsi18n -v0; \
		${POOTLE_CMD} webpack --dev --nowatch; \
		mkdir -p ${ASSETS_DIR}; \
		echo 'Collecting static'; \
		${POOTLE_CMD} collectstatic -v0 --noinput --clear -i node_modules -i .tox -i docs ${TAIL}; \
		echo 'Building assets'; \
		${POOTLE_CMD} assets -v0 build ${TAIL}; \
		chmod 664 ${ASSETS_DIR}.webassets-cache/*; \
	fi

docs:
	# Make sure that the submodule with docs theme is pulled and up-to-date.
	git submodule update --init
	# The following creates the HTML docs.
	# NOTE: cd and make must be in the same line.
	cd ${DOCS_DIR}; make SPHINXOPTS="-T -W -q " html ${TAIL}

docs-review: docs
	python -mwebbrowser file://$(shell pwd)/${DOCS_DIR}/_build/html/index.html

sprite:
	glue --sprite-namespace="" --namespace="" --cachebuster ${SPRITE_DIR} --css=${CSS_DIR} --img=${IMAGES_DIR}
	optipng -o7 ${IMAGES_DIR}/sprite*.png

pot:
	@${SRC_DIR}/tools/createpootlepot

get-translations:
	ssh pootle.locamotion.org ". /var/www/sites/pootle/env/bin/activate; python /var/www/sites/pootle/src/manage.py sync_stores --verbosity=1 --project=pootle"
	rsync -az --delete --exclude=en_US --exclude="LINGUAS" --exclude=".translation_index" --exclude=pootle-terminology.po pootle.locamotion.org:/var/www/sites/pootle/translations/pootle/ ${SRC_DIR}/locale
	for po in $$(find ${SRC_DIR}/locale -name "*.po"); do msgcat $$po > $$po.2 && mv $$po.2 $$po; done

put-translations:
	rsync -azv --progress --exclude="*~" --exclude="*.mo" --exclude="LC_MESSAGES" --exclude=unicode --exclude="LINGUAS" --exclude=".translation_index" --exclude=pootle-terminology.po --exclude=en_US ${SRC_DIR}/locale/ pootle.locamotion.org:/var/www/sites/pootle/translations/pootle/
	ssh pootle.locamotion.org ". /var/www/sites/pootle/env/bin/activate; python /var/www/sites/pootle/src/manage.py update_stores --verbosity=1 --project=pootle"

linguas:
	@${SRC_DIR}/tools/make-LINGUAS.sh 80 de fr es ko ug

lint: lint-python lint-js lint-css lint-docs

lint-docs:
	pydocstyle

lint-py: lint-python

lint-python: lint-flake8 lint-isort lint-pylint

lint-flake8:
	flake8 --config=setup.cfg

lint-isort:
	isort --check-only --diff

lint-pylint:
	pylint --rcfile=.pylint-travisrc pootle tests pytest_pootle docs pootle/settings/*.conf*


lint-js:
	cd ${JS_DIR} \
	&& npm run lint

lint-css:
	cd ${JS_DIR} \
	&& npm run stylelint

test-js:
	cd ${JS_DIR} \
	&& npm test

help:
	@echo "Help"
	@echo "----"
	@echo
	@echo "	 assets - collect and rebuild the static assets"
	@echo "	 build - create sdist with required prep"
	@echo "	 docs - build Sphinx docs"
	@echo "	 docs-review - launch webbrowser to review docs"
	@echo "	 sprite - create CSS sprite"
	@echo "	 pot - update the POT translations templates"
	@echo "	 get-translations - retrieve Pootle translations from server (requires ssh config for pootletranslations)"
	@echo "	 linguas - update the LINGUAS file with languages over 80% complete"
