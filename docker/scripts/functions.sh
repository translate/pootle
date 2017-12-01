#!/bin/bash

function uncomment {
    # $1 = 14,16  # line numbers
    # $1 = "/startStr/,/endStr/"
    # $2 - fileName
    sed -i "$1"'s/^#//' "$2"
}

function comment {
    # $1 = 14,16  # line numbers
    # $1 = "/startStr/,/endStr/"
    # $2 - fileName
    sed -i "$1"'s/^/#/' "$2"
}
