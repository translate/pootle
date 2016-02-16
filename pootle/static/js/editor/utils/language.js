/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */


/* Normalizes language codes in order to use them in MT services */
export function normalizeCode(locale) {
  if (!locale) {
    return locale;
  }

  const atIndex = locale.indexOf('@');
  let clean = locale.replace('_', '-');
  if (atIndex !== -1) {
    clean = clean.slice(0, atIndex);
  }
  return clean;
}
