#!/bin/bash

# Adjust the README.rst for stable/M.N.x branches and release M.N.O tags

# update-readme.sh - will do alterations on the current branch
# update-readme.sh branch some/branch - will do branch some/branch no matter what your current branch is
#
# Doc links are change from latest -> stable-M.N.x only if this is a stable/* branch or a release

change_type="branch"
if [[ $# -eq 0 ]]; then
    change_type="branch"
elif [[ $# -eq 1 ]]; then
    change_type=$1
    if [[ $change_type != "branch" && $change_type != "release" ]]; then
        echo "Valid options are 'release' or 'branch'"
        exit 1
    fi
fi

README=README.rst

VERSION=$(python -m pootle.core.utils.version main)
FULL_VERSION=$(python -m pootle.core.utils.version)

branch=$(git rev-parse --abbrev-ref HEAD)
if [[ $change_type == "branch" ]]; then
    if [[ $# -eq 2 ]]; then
        branch=$2
    fi
fi
branch_escape=$(echo $branch | sed "s#/#%2F#")

docs=latest
if [[ $branch =~ "stable/" ]]; then
    docs="stable-"$(python -m pootle.core.utils.version docs)".x"
fi

# Release Notes
sed -E -i "" "s#releases/[0-9]\.[0-9]\.[0-9]\.html#releases/$VERSION.html#" $README

# Adjust docs away from /latest/
sed -E -i "" "s#/pootle/en/latest/#/pootle/en/$docs/#" $README

### Badge rewrites

# Codecov
if [[ $change_type == "branch" ]]; then
    codecov_badge=$branch
    codecov_link=$branch_escape
else
    codecov_badge=$FULL_VERSION
    codecov_link=$FULL_VERSION
fi
sed -E -i "" "s#codecov.io/gh/translate/pootle/branch/master#codecov.io/gh/translate/pootle/branch/$codecov_link#" $README
sed -E -i "" "s#codecov.io/github/translate/pootle\?branch=master#codecov.io/github/translate/pootle?branch=$codecov_link#" $README
ed -E -i "" "s#shields.io/codecov/c/github/translate/pootle/master#shields.io/codecov/c/github/translate/pootle/$codecov_link#" $README

# Travis - we change only the badge as we can't link directly to anything
if [[ $change_type == "branch" ]]; then
    travis_badge=$branch
else
    travis_badge=$FULL_VERSION
fi
sed -E -i "" "s#travis/translate/pootle/master#travis/translate/pootle/$travis_badge#" $README

# Landscape
sed -E -i "" "s#landscape.io/github/translate/pootle/master#landscape.io/github/translate/pootle/$branch#" $README

# Requires.io
if [[ $change_type == "branch" ]]; then
    sed -E -i "" "s#requires/github/translate/pootle/master#requires/github/translate/pootle/$branch#" $README
    sed -E -i "" "s#requirements/\?branch=master#requirements/?branch=$branch_escape#" $README
else
    sed -E -i "" "s#https://img.shields.io/requires/.*#https://requires.io/github/translate/pootle/requirements.svg?tag=$FULL_VERSION#" $README
    sed -E -i "" "s#requirements/\?branch=master#requirements/?tag=$FULL_VERSION#" $README
fi

echo "Commit and push README.rst, don't forget to check that all the links actually work correctly especially for a release"
