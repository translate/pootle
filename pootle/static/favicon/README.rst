favicons
========

We make use of https://realfavicongenerator.net/ to create favicons from
logo-{white,color}.svg

The resultant svg's are optimised using npm's svgo::

  cd pootle/static/js
  npm run svgo [file.svg]
