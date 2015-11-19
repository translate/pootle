/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';

import 'jquery-select2';


const escapeRE = /<[^<]*?>|\r\n|[\r\n\t&<>]/gm;
const whitespaceRE = /^ +| +$|[\r\n\t] +| {2,}/gm;


/* Gets current URL's hash */
export function getHash(win) {
  // Mozilla has a bug when it automatically unescapes %26 to '&'
  // when getting hash from `window.location.hash'.
  // So, we have to extract it from the `window.location'.
  // Also, we don't need to decodeURIComponent() the hash
  // as it will break encoded ampersand again
  // (decoding can be done on the higher level, if needed)
  return (win || window).location.toString().split('#', 2)[1] || '';
}


function decodeURIParameter(s) {
  return decodeURIComponent(s.replace(/\+/g, ' '));
}


export function getParsedHash(hash) {
  const params = {};
  const r = /([^&;=]+)=?([^&;]*)/g;

  let h = hash;
  if (h === undefined) {
    h = getHash();
  }

  let e = r.exec(h);
  while (e !== null) {
    params[decodeURIParameter(e[1])] = decodeURIParameter(e[2]);
    e = r.exec(h);
  }
  return params;
}


/* Updates current URL's hash */
export function updateHashPart(part, newVal, removeArray, hash) {
  const r = /([^&;=]+)=?([^&;]*)/g;
  const params = [];
  let h = hash;
  if (h === undefined) {
    h = getHash();
  }
  let ok = false;
  let e = r.exec(h);

  while (e !== null) {
    const p = decodeURIParameter(e[1]);
    if (p === part) {
      // replace with the given value
      params.push([e[1], encodeURIComponent(newVal)].join('='));
      ok = true;
    } else if ($.inArray(p, removeArray) === -1) {
      // use the parameter as is
      params.push([e[1], e[2]].join('='));
    }

    e = r.exec(h);
  }
  // if there was no old parameter, push the param at the end
  if (!ok) {
    params.push([encodeURIComponent(part),
      encodeURIComponent(newVal)].join('='));
  }
  return params.join('&');
}


/* Cross-browser comparison function */
export function strCmp(a, b) {
  let rv;
  if (a === b) {
    rv = 0;
  } else if (a < b) {
    rv = -1;
  } else {
    rv = 1;
  }
  return rv;
}


/* Fancy escapes to highlight parts of the text such as HTML tags */
export function fancyEscape(text) {
  function replace(match) {
    const escapeHl = '<span class="highlight-escape">%s</span>';
    const htmlHl = '<span class="highlight-html">&lt;%s&gt;</span>';
    const submap = {
      '\r\n': `${escapeHl.replace(/%s/, '\\r\\n')}<br/>\n`,
      '\r': `${escapeHl.replace(/%s/, '\\r')}<br/>\n`,
      '\n': `${escapeHl.replace(/%s/, '\\n')}<br/>\n`,
      '\t': escapeHl.replace(/%s/, '\\t'),
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
    };

    let replaced = submap[match];

    if (replaced === undefined) {
      replaced = htmlHl.replace(
            /%s/,
            fancyEscape(match.slice(1, match.length - 1))
        );
    }

    return replaced;
  }

  return text.replace(escapeRE, replace);
}


/* Highlight spaces to make them easily visible */
function fancySpaces(text) {
  function replace(match) {
    const spaceHl = '<span class="translation-space"> </span>';

    return Array(match.length + 1).join(spaceHl);
  }

  return text.replace(whitespaceRE, replace);
}


/* Fancy highlight: fancy spaces + fancy escape */
export function fancyHl(text) {
  return fancySpaces(fancyEscape(text));
}


export function fancyHlNodes(selector) {
  [...document.querySelectorAll(selector)].forEach(
    (translationTextNode) => {
      // eslint-disable-next-line no-param-reassign
      translationTextNode.innerHTML = fancyHl(translationTextNode.textContent);
    }
  );
}


/* Returns a string representing a relative datetime */
export function relativeDate(date) {
  const delta = Date.now() - date;
  const seconds = Math.round(Math.abs(delta) / 1000);
  const minutes = Math.round(seconds / 60);
  const hours = Math.round(minutes / 60);
  const days = Math.round(hours / 24);
  const weeks = Math.round(days / 7);
  const years = Math.round(days / 365);
  let fmt;
  let count;

  if (years > 0) {
    fmt = years === 1 ? gettext('A year ago') : ngettext('%s year ago', '%s years ago', years);
    count = [years];
  } else if (weeks > 0) {
    fmt = weeks === 1 ? gettext('A week ago') : ngettext('%s week ago', '%s weeks ago', weeks);
    count = [weeks];
  } else if (days > 0) {
    fmt = days === 1 ? gettext('Yesterday') : ngettext('%s day ago', '%s days ago', days);
    count = [days];
  } else if (hours > 0) {
    fmt = hours === 1 ? gettext('An hour ago') : ngettext('%s hour ago', '%s hours ago', hours);
    count = [hours];
  } else if (minutes > 0) {
    fmt = minutes === 1 ?
      gettext('A minute ago') : ngettext('%s minute ago', '%s minutes ago', minutes);
    count = [minutes];
  }

  if (fmt) {
    return interpolate(fmt, count);
  }

  return gettext('A few seconds ago');
}


/* Converts the elements matched by `selector` into selectable inputs.
 *
 * `onChange` function will be fired when the select choice changes.
 */
export function makeSelectableInput(selector, options, onChange, onSelecting) {
  // XXX: Check if this works with multiple selects per page
  const $el = $(selector);

  if (!$el.length) {
    return;
  }

  $el.select2(options);

  $el.on('change', onChange);
  $el.on('select2-selecting', onSelecting);
}


export function executeFunctionByName(functionName, ctx, ...args) {
  const namespaces = functionName.split('.');
  const func = namespaces.pop();

  let context = ctx;
  for (let i = 0; i < namespaces.length; i++) {
    context = context[namespaces[i]];
  }

  return context[func].apply(this, args);
}


export function blinkClass($elem, className, n, delay) {
  $elem.toggleClass(className);
  if (n > 1) {
    setTimeout(() => blinkClass($elem, className, n - 1, delay), delay);
  }
}


export default {
  blinkClass,
  executeFunctionByName,
  fancyHl,
  fancyHlNodes,
  getHash,
  getParsedHash,
  makeSelectableInput,
  relativeDate,
  strCmp,
  updateHashPart,
};
