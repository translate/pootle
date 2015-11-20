/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */


function getCookie(name) {
  let value = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i=0; i<cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        value = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return value;
}


function setCookie(name, value, options={}) {
  if (value === null) {
    value = '';
    options.expires = -1;
  }

  let expires = '';

  if (options.expires &&
      (typeof options.expires === 'number' || options.expires.toUTCString)) {
    let date;
    if (typeof options.expires === 'number') {
      date = new Date();
      date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
    } else {
      date = options.expires;
    }
    // use expires attribute, max-age is not supported by IE
    expires = `; expires=${date.toUTCString()}`;
  }

  // CAUTION: Needed to parenthesize options.path and options.domain
  // in the following expressions, otherwise they evaluate to undefined
  // in the packed version for some reason...
  const path = options.path ? `; path=${options.path}` : '';
  const domain = options.domain ? `; domain=${options.domain}` : '';
  const secure = options.secure ? '; secure' : '';
  document.cookie = `${name}=${encodeURIComponent(value)}` +
                    `${expires}${path}${domain}${secure}`;
}


export default function cookie(name, value, options) {
  if (value === undefined) {
    return getCookie(name);
  }
  setCookie(name, value, options);
}
