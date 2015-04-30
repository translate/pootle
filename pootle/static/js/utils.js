/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var $ = require('jquery');

require('jquery-select2');


var escapeRE = /<[^<]*?>|\r\n|[\r\n\t&<>]/gm,
    whitespaceRE = /^ +| +$|[\r\n\t] +| {2,}/gm;


/* Gets current URL's hash */
var getHash = function (win) {
  // Mozilla has a bug when it automatically unescapes %26 to '&'
  // when getting hash from `window.location.hash'.
  // So, we have to extract it from the `window.location'.
  // Also, we don't need to decodeURIComponent() the hash
  // as it will break encoded ampersand again
  // (decoding can be done on the higher level, if needed)
  return (win || window).location.toString().split('#', 2)[1] || '';
};


var decodeURIParameter = function(s) {
  return decodeURIComponent(s.replace(/\+/g, ' '));
};


var getParsedHash = function (h) {
  var params = {}, e;
  var r = /([^&;=]+)=?([^&;]*)/g;
  if (h === undefined) {
    h = this.getHash();
  }

  while (e = r.exec(h)) {
    params[decodeURIParameter(e[1])] = decodeURIParameter(e[2]);
  }
  return params;
};


/* Updates current URL's hash */
var updateHashPart = function (part, newVal, removeArray) {
  var r = /([^&;=]+)=?([^&;]*)/g;
  var params = [], h = getHash(), e, ok, p;
  while (e = r.exec(h)) {
    p = decodeURIParameter(e[1]);
    if (p === part) {
      // replace with the given value
      params.push([e[1], encodeURIComponent(newVal)].join('='));
      ok = true;
    } else if ($.inArray(p, removeArray) === -1) {
      // use the parameter as is
      params.push([e[1], e[2]].join('='));
    }
  }
  // if there was no old parameter, push the param at the end
  if (!ok) {
    params.push([encodeURIComponent(part),
      encodeURIComponent(newVal)].join('='));
  }
  return params.join('&');
};


/* Cross-browser comparison function */
var strCmp = function (a, b) {
  return a === b ? 0 : a < b ? -1 : 1;
};


/* Cleans '\n' escape sequences and adds '\t' sequences */
var cleanEscape = function (s) {
  return s.replace(/\\t/g, "\t").replace(/\\n/g, "");
};


/* Fancy escapes to highlight parts of the text such as HTML tags */
var fancyEscape = function (text) {

  function replace(match) {
      var replaced,
          escapeHl= '<span class="highlight-escape">%s</span>',
          htmlHl = '<span class="highlight-html">&lt;%s&gt;</span>',
          submap = {
            '\r\n': escapeHl.replace(/%s/, '\\r\\n') + '<br/>\n',
            '\r': escapeHl.replace(/%s/, '\\r') + '<br/>\n',
            '\n': escapeHl.replace(/%s/, '\\n') + '<br/>\n',
            '\t': escapeHl.replace(/%s/, '\\t'),
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;'
          };

      replaced = submap[match];

      if (replaced === undefined) {
        replaced = htmlHl.replace(
            /%s/,
            fancyEscape(match.slice(1, match.length-1))
        );
      }

      return replaced;
  }

  return text.replace(escapeRE, replace);
};


/* Highlight spaces to make them easily visible */
var fancySpaces = function (text) {

  function replace(match) {
      var spaceHl= '<span class="translation-space"> </span>';

      return Array(match.length + 1).join(spaceHl);
  }

  return text.replace(whitespaceRE, replace);
};


/* Fancy highlight: fancy spaces + fancy escape */
var fancyHl = function (text) {
  return fancySpaces(fancyEscape(text));
};


/* Returns a string representing a relative datetime */
var relativeDate = function (date) {
  var fmt, count,
      delta = Date.now() - date,
      seconds = Math.round(Math.abs(delta) / 1000),
      minutes = Math.round(seconds / 60),
      hours = Math.round(minutes / 60),
      days = Math.round(hours / 24),
      weeks = Math.round(days / 7),
      years = Math.round(days / 365);

  if (years > 0) {
    fmt = ngettext('A year ago', '%s years ago', years);
    count = [years];
  } else if (weeks > 0) {
    fmt = ngettext('A week ago', '%s weeks ago', weeks);
    count = [weeks];
  } else if (days > 0) {
    fmt = ngettext('Yesterday', '%s days ago', days);
    count = [days];
  } else if (hours > 0) {
    fmt = ngettext('An hour ago', '%s hours ago', hours);
    count = [hours];
  } else if (minutes > 0) {
    fmt = ngettext('A minute ago', '%s minutes ago', minutes);
    count = [minutes];
  }

  if (fmt) {
    return interpolate(fmt, count);
  }

  return gettext('A few seconds ago');
};


/* Converts the elements matched by `selector` into selectable inputs.
 *
 * `onChange` function will be fired when the select choice changes.
 */
var makeSelectableInput = function (selector, options, onChange) {
  // XXX: Check if this works with multiple selects per page
  var $el = $(selector);

  if (!$el.length) {
    return;
  }

  $el.select2(options);

  $el.on('change', onChange);
};


var executeFunctionByName = function (functionName, context /*, args */) {
  var args = Array.prototype.slice.call(arguments).splice(2),
      namespaces = functionName.split("."),
      func = namespaces.pop();

  for (var i=0; i<namespaces.length; i++) {
    context = context[namespaces[i]];
  }

  return context[func].apply(this, args);
};


var blinkClass = function ($elem, className, n, delay) {
  $elem.toggleClass(className);
  if (n > 1) {
    setTimeout(() => blinkClass($elem, className, n-1, delay), delay);
  }
};


module.exports = {
  getHash: getHash,
  getParsedHash: getParsedHash,
  updateHashPart: updateHashPart,
  strCmp: strCmp,
  cleanEscape: cleanEscape,
  fancyEscape: fancyEscape,
  fancyHl: fancyHl,
  relativeDate: relativeDate,
  makeSelectableInput: makeSelectableInput,
  executeFunctionByName: executeFunctionByName,
  blinkClass: blinkClass,
};
