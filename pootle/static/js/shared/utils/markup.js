/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */


/**
 * Maps markup module names from settings to CodeMirror mode names
 */
export function getMode(markup) {
  return {
    html: 'htmlmixed',
    restructuredtext: 'rst',
  }[markup] || markup;
}


/**
 * Returns a human-readable name for the markup module
 */
export function getName(markup) {
  return {
    html: 'HTML',
    markdown: 'Markdown',
    restructuredtext: 'reStructuredText',
    textile: 'Textile',
  }[markup] || markup;
}
