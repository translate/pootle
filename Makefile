SRC_DIR = pootle
DOCS_DIR = docs
STATIC_DIR = ${SRC_DIR}/static
ASSETS_DIR = ${SRC_DIR}/assets
CSS_DIR = ${STATIC_DIR}/css
IMAGES_DIR = ${STATIC_DIR}/images
SPRITE_DIR = ${IMAGES_DIR}/sprite

.PHONY: all build sprite pot mo mo-all help docs assets

all: help

build: docs mo assets
	python setup.py sdist

assets:
	mkdir -p ${ASSETS_DIR}
	# NOTE: all files in ASSETS_DIR should be removed using rm -rf because
	# collectstatic does not have a --clear option on Django 1.3.x.
	rm -rf ${ASSETS_DIR}/*
	python manage.py collectstatic --noinput
	python manage.py assets build

docs:
	# Make sure that the submodule with docs theme is pulled and up-to-date.
	git submodule update --init
	# The following creates the HTML docs.
	# NOTE: cd and make should to be in the same line.
	cd ${DOCS_DIR}; make html

sprite:
	glue --sprite-namespace="" --namespace="" ${SPRITE_DIR} --css=${CSS_DIR} --img=${IMAGES_DIR}

pot:
	@${SRC_DIR}/tools/createpootlepot

mo:
	python setup.py build_mo

mo-all:
	python setup.py build_mo --all

help:
	@echo "Help"
	@echo "----"
	@echo
	@echo "  build - create sdist with required prep"
	@echo "  sprite - create CSS sprite"
	@echo "  pot - update the POT translations templates"
	@echo "  mo - build MO files for languages listed in 'pootle/locale/LINGUAS'"
	@echo "  mo-all - build MO files for all languages (only use for testing)"
