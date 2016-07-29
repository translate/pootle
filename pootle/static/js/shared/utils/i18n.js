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


/**
 * Mark a string for localization and optionally replace placeholders with the
 * components provided in the context argument. This is intended to use in the
 * context of JSX and React components.
 *
 * @param {String} string - The string to internationalize. It accepts a
 * simplified form of printf-style placeholders, however note these must be
 * named, so they need to take the explicit `%(key)s` form, not `%s`.
 * @param {Object} ctx - Components to be injected in the placeholders specified
 * by the keys.
 * @return {Array} - An array with the original `string`, and placeholders
 * replaced by the given components.
 */
export function tct(string, ctx = null) {
  if (!ctx) {
    return [gettext(string)];
  }
  return formatComponent(gettext(string), ctx);
}


/**
 * Mark a string for localization and optionally replace placeholders with the
 * values provided in the context argument.
 *
 * @param {String} string - The string to internationalize. It accepts a
 * simplified form of printf-style placeholders, however note these must be
 * named, so they need to take the explicit `%(key)s` form, not `%s`.
 * @param {Object} ctx - Values to be injected in the placeholders specified by
 * the keys. Note these will be coerced to strings.
 * @return {String} - The original `string` with placeholders replaced by the
 * given context values.
 */
export function t(string, ctx = null) {
  if (!ctx) {
    return gettext(string);
  }
  return interpolate(gettext(string), ctx, true);
}


/**
 * Mark a plural string for localization and optionally replace placeholders
 * with the values provided in the context argument.
 *
 * @param {String} singular - The singular string to internationalize. It
 * accepts the same placeholders as `t()`.
 * @param {String} plural - The plural string to internationalize. It accepts
 * the same placeholders as `t()`.
 * @param {Integer} count - The object count which will determine the
 * translation string o use.
 * @param {Object} ctx - Values to be injected in the placeholders specified by
 * the keys. Note these will be coerced to strings.
 * @return {String} - The translation for `singular` or `plural` (depending on
 * `count`) with placeholders replaced by the given context values.
 */
export function nt(singular, plural, count, ctx = null) {
  if (!ctx) {
    return ngettext(singular, plural, count);
  }
  return interpolate(ngettext(singular, plural, count), ctx, true);
}
