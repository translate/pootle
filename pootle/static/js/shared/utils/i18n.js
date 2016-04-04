/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';


/**
 * Make it possible React components can be added as placeholders.
 *
 * Example:
 * `formatComponent(%(foo)s bar %(baz)s)` returns `[ctx.foo, bar, ctx.baz]` list.
 */
function formatComponent(str, ctx) {
  const result = [];
  let id = 0;
  let _fmt = str;
  let match = [];

  while (_fmt) {
    match = /^[^\x25]+/.exec(_fmt);
    if (match !== null) {
      result.push(match[0]);
    } else {
      match = /^\x25\(([^\)]+)\)s/.exec(_fmt);
      if (match === null) {
        throw new Error('Wrong format');
      }
      if (match[1]) {
        const arg = ctx[match[1]];
        if (React.isValidElement(arg)) {
          result.push(React.cloneElement(arg, { key: id++ }));
        } else {
          result.push(arg);
        }
      }
    }
    _fmt = _fmt.substring(match[0].length);
  }
  return result;
}

export function t(string, ctx = null) {
  if (!ctx) {
    return gettext(string);
  }
  return formatComponent(gettext(string), ctx);
}
