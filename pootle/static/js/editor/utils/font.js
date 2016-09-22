/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import _ from 'underscore';


export const CHARACTERS = {
  NULL: '\u0000',
  BELL: '\u0007',
  BS: '\u0008',
  TAB: '\u0009',
  VT: '\u000B',
  FF: '\u000C',
  ESC: '\u001B',
  NBSP: '\u00A0',

  LF: '\u000A',
  CR: '\u000D',

  SPACE: '\u0020',

  ALM: '\u061C',
  ZWS: '\u200B',
  ZWNJ: '\u200C',
  ZWJ: '\u200D',
  LRM: '\u200E',
  RLM: '\u200F',
  LRE: '\u202A',
  RLE: '\u202B',
  PDF: '\u202C',
  LRO: '\u202D',
  RLO: '\u202E',
  WJ: '\u2060',
  LRI: '\u2066',
  RLI: '\u2067',
  FSI: '\u2068',
  PDI: '\u2069',
};


export const SYMBOLS = {
  NULL: '\u2400',
  BELL: '\u2407',
  BS: '\u2408',
  TAB: '\u2409',
  VT: '\u240B',
  FF: '\u240C',
  ESC: '\u241B',
  NBSP: '\u2423',

  LF: '\u240A',
  CR: '\u240D',

  SPACE: '\u2420',

  ALM: '\uF000',
  ZWS: '\uF001',
  ZWNJ: '\uF002',
  ZWJ: '\uF003',
  LRM: '\uF004',
  RLM: '\uF005',
  LRE: '\uF006',
  RLE: '\uF007',
  PDF: '\uF008',
  LRO: '\uF009',
  RLO: '\uF00A',
  WJ: '\uF00B',
  LRI: '\uF00C',
  RLI: '\uF00D',
  FSI: '\uF00E',
  PDI: '\uF00F',
};


/* Character mapping/unmapping definitions for the custom font */

const REGULAR_MAP_COMMON = {
  [CHARACTERS.NULL]: SYMBOLS.NULL,
  [CHARACTERS.BELL]: SYMBOLS.BELL,
  [CHARACTERS.BS]: SYMBOLS.BS,
  [CHARACTERS.TAB]: SYMBOLS.TAB,
  [CHARACTERS.VT]: SYMBOLS.VT,
  [CHARACTERS.FF]: SYMBOLS.FF,
  [CHARACTERS.ESC]: SYMBOLS.ESC,
  [CHARACTERS.NBSP]: SYMBOLS.NBSP,
};

const REGULAR_MAP = assign({}, REGULAR_MAP_COMMON, {
  [CHARACTERS.LF]: `${SYMBOLS.LF}${CHARACTERS.LF}`,
  [CHARACTERS.CR]: `${SYMBOLS.CR}${CHARACTERS.CR}`,
});

const REGULAR_MAP_REV = assign({}, _.invert(REGULAR_MAP_COMMON), {
  [SYMBOLS.LF]: '',
  [SYMBOLS.CR]: '',
});

// Only for highlight purposes
export const REGULAR_MAP_REV_HL = assign({}, _.invert(REGULAR_MAP_COMMON), {
  [SYMBOLS.LF]: CHARACTERS.LF,
  [SYMBOLS.CR]: CHARACTERS.CR,
});


const NEWLINE_SYMBOLS = [SYMBOLS.LF, SYMBOLS.CR];


const RAW_MAP_COMMON = {
  [CHARACTERS.SPACE]: SYMBOLS.SPACE,

  [CHARACTERS.ALM]: SYMBOLS.ALM,
  [CHARACTERS.ZWS]: SYMBOLS.ZWS,
  [CHARACTERS.ZWNJ]: SYMBOLS.ZWNJ,
  [CHARACTERS.ZWJ]: SYMBOLS.ZWJ,
  [CHARACTERS.LRM]: SYMBOLS.LRM,
  [CHARACTERS.RLM]: SYMBOLS.RLM,
  [CHARACTERS.LRE]: SYMBOLS.LRE,
  [CHARACTERS.RLE]: SYMBOLS.RLE,
  [CHARACTERS.PDF]: SYMBOLS.PDF,
  [CHARACTERS.LRO]: SYMBOLS.LRO,
  [CHARACTERS.RLO]: SYMBOLS.RLO,
  [CHARACTERS.WJ]: SYMBOLS.WJ,
  [CHARACTERS.LRI]: SYMBOLS.LRI,
  [CHARACTERS.RLI]: SYMBOLS.RLI,
  [CHARACTERS.FSI]: SYMBOLS.FSI,
  [CHARACTERS.PDI]: SYMBOLS.PDI,
};

const RAW_MAP = assign({}, REGULAR_MAP, RAW_MAP_COMMON);

const RAW_MAP_REV = assign({}, REGULAR_MAP_REV, _.invert(RAW_MAP_COMMON));


/* Helper to create a regexp for a group of code points */
function makeCodePointRegex(codePointList) {
  return new RegExp(`[${codePointList.join('')}]`, 'g');
}


const REGULAR_MODE_PATTERN = makeCodePointRegex(Object.keys(REGULAR_MAP));
export const REGULAR_MODE_PATTERN_REV = makeCodePointRegex(Object.keys(REGULAR_MAP_REV));

const RAW_MODE_PATTERN = makeCodePointRegex(Object.keys(RAW_MAP));
const RAW_MODE_PATTERN_REV = makeCodePointRegex(Object.keys(RAW_MAP_REV));


/* Applies the mapping table for `mode` mode to `value. */
export function applyFontFilter(value, mode = 'regular') {
  // Map characters to mode
  const pattern = mode !== 'raw' ? REGULAR_MODE_PATTERN : RAW_MODE_PATTERN;
  const newValue = value.replace(pattern, (match) => RAW_MAP[match]);

  if (mode === 'raw') {
    return newValue;
  }

  /*
   * Replace extra spaces with the whitespace symbol.
   * This will consider any leading/trailing spaces at the beginning and end of
   * lines, as well as two or more consecutive whitespace characters at any
   * position.
   */
  return newValue.replace(
    /^\u0020+|\u0020+$|\u0020+(?=\u2420$)|\u0020+(?=\u240A$)|\u0020{2,}/mg,
    (match) => new Array(match.length + 1).join(SYMBOLS.SPACE)
  );
}


/* Reverts the mapping table for `mode` mode from `value. */
export function unapplyFontFilter(value, mode = 'regular') {
  // Unmap characters from mode.
  // There's a special case here: since browsers normalize textarea values to
  // `\n`, any `\r` will always be reported as `\n`, hence we need to detect if
  // there's an explicit [CR] symbol followed by a `\n`, in which we need to
  // convert the `\n` back to `\r`. Sigh.
  const pattern = mode !== 'raw' ? REGULAR_MODE_PATTERN_REV : RAW_MODE_PATTERN_REV;
  const newValue = value
    .replace(/\u240D\u000A/g, `${SYMBOLS.CR}${CHARACTERS.CR}`)
    .replace(pattern, (match) => RAW_MAP_REV[match]);

  if (mode === 'raw') {
    return newValue;
  }

  // Remove extra spacing symbols added in `applyFontFilter`.
  return newValue.replace(/\u2420/g, CHARACTERS.SPACE);
}


/* Counts the number of newline symbols present in `value` */
export function countNewlineSymbol(value) {
  return (value.match(makeCodePointRegex(NEWLINE_SYMBOLS)) || []).length;
}
