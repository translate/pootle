/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */


/**
 * The purpose of this module is solely to provide some helper utilities to
 * handle line ending normalization in the `Editor`. This is required because
 * Pootle does not implement line ending normalization on the backend for the
 * time being, and we want the strings that flow down our client-side code to
 * deal with a single line ending value, `\n`.
 */


export function hasCRLF(value) {
  return typeof value === 'string' && value.indexOf('\r\n') !== -1;
}


export function normalize(values) {
  if (!Array.isArray(values)) {
    return [];
  }
  return values.map((value) => value.replace(/\r\n/g, '\n'));
}


export function denormalize(values) {
  if (!Array.isArray(values)) {
    return [];
  }
  return values.map((value) => value.replace(/\n/g, '\r\n'));
}
