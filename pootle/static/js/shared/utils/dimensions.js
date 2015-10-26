/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */


export function outerHeight(el) {
  const style = window.getComputedStyle(el);

  return (el.offsetHeight +
          parseInt(style.marginTop, 10) +
          parseInt(style.marginBottom, 10));
}


export function outerWidth(el) {
  const style = window.getComputedStyle(el);

  return (el.offsetWidth +
          parseInt(style.marginLeft, 10) +
          parseInt(style.marginRight, 10));
}
