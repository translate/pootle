/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

/* eslint-disable no-irregular-whitespace */
const PUNCTUATION_RE = /[™©®]|[℃℉°]|[±πθ×÷−√∞∆Σ′″]|[‘’ʼ‚‛“”„‟]|[«»]|[£¥€]|…|—|–|[ ]/g;
/* eslint-enable no-irregular-whitespace */
// Marks + Degree-related + Maths + Quote characters + Guillemets + Currencies +
// U2026 horizontal ellipsis + U2014 em dash + U2013 en dash +
// U202F narrow no-break space

export function highlightPunctuation(text) {
  function replace(match) {
    return `<span class="highlight-punctuation js-editor-copytext">${match}</span>`;
  }

  return text.replace(PUNCTUATION_RE, replace);
}


const nonPrintable = '<span class="non-printable js-editor-copytext %1$s" ' +
                     'data-string="%2$s"></span>';
const newLineHl = nonPrintable.replace('%1$s', 'newline')
                              .replace('%2$s', '&#10;') + '<br/>';
const tabHl = nonPrintable.replace('%1$s', 'tab').replace('%2$s', '&#9;');
const escapeHl = '<span class="highlight-escape js-editor-copytext">%s</span>';

const ESCAPE_RE = /\r\n|[\r\n\t]|\\r|\\n|\\t/gm;


export function highlightEscapes(text) {
  function replace(match) {
    const submap = {
      '\r\n': newLineHl,
      '\r': newLineHl,
      '\n': newLineHl,
      '\t': tabHl,
      '\\r': escapeHl.replace(/%s/, '\\r'),
      '\\n': escapeHl.replace(/%s/, '\\n'),
      '\\t': escapeHl.replace(/%s/, '\\t'),
    };

    return submap[match];
  }

  return text.replace(ESCAPE_RE, replace);
}


const spaceHl = '<span class="highlight-whitespace js-editor-copytext" data-string="%s"></span>';
const WHITESPACE_RE = /^([ \u{00a0}]+)|([ \u{00a0}]+)$|[ \u{00a0}]{2,}/gmu;

export function highlightWhitespace(text) {
  function replace(match) {
    return (
      Array(match.length + 1)
        .join(spaceHl.replace('%s', `&#${match.charCodeAt()};`))
    );
  }
  return text.replace(WHITESPACE_RE, replace);
}


const htmlHl = '<span class="highlight-html js-editor-copytext">&lt;%s&gt;</span>';
const HTML_RE = /<[^>]+>|[&<>]/gm;

export function highlightHtml(text) {
  function replace(match) {
    const submap = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
    };

    let replaced = submap[match];

    if (replaced === undefined) {
      replaced = htmlHl.replace(
        /%s/,
        highlightHtml(match.slice(1, match.length - 1))
      );
    }

    return replaced;
  }

  return text.replace(HTML_RE, replace);
}
