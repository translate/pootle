#!/bin/sh

# Generate the sprite.png and sprite.css
glue --namespace="" images/sprite/ --css=css/ --img=images/

# Remove initial part from the generated selectors
sed -i -e 's/sprite-//g' css/sprite.css
