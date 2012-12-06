SRC_DIR = pootle
STATIC_DIR = ${SRC_DIR}/static
CSS_DIR = ${STATIC_DIR}/css
IMAGES_DIR = ${STATIC_DIR}/images
SPRITE_DIR = ${IMAGES_DIR}/sprite

all:

sprite:
		glue --sprite-namespace="" --namespace="" ${SPRITE_DIR} --css=${CSS_DIR} --img=${IMAGES_DIR}

pot:
		@${SRC_DIR}/tools/createpootlepot
