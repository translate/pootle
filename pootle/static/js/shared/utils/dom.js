/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */


/**
 * Queries the DOM for an element matching `selector`.
 *
 * @param {String} selector - The CSS selector
 * @return {Node} - the matched `Node`, `null` otherwise.
 */
export function q(selector) {
  return document.querySelector(selector);
}


/**
 * Queries the DOM for a collection matching `selector`.
 *
 * @param {String} selector - The CSS selector
 * @return {Array} - Array of matched `Node`s
 */
export function qAll(selector) {
  const nodes = document.querySelectorAll(selector);
  // XXX: not using array spread because this requires an extra polyfill to
  // support IE 11
  return Array.prototype.slice.call(nodes);
}
