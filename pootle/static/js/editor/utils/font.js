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

export const BASE_MAP = {
  [CHARACTERS.NULL]: SYMBOLS.NULL,
  [CHARACTERS.BELL]: SYMBOLS.BELL,
  [CHARACTERS.BS]: SYMBOLS.BS,
  [CHARACTERS.TAB]: SYMBOLS.TAB,
  [CHARACTERS.VT]: SYMBOLS.VT,
  [CHARACTERS.FF]: SYMBOLS.FF,
  [CHARACTERS.ESC]: SYMBOLS.ESC,
  [CHARACTERS.NBSP]: SYMBOLS.NBSP,
  [CHARACTERS.CR]: SYMBOLS.CR,
};

export const FULL_MAP = assign({}, BASE_MAP, {
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
});


const BASE_MAP_REV = assign({}, _.invert(BASE_MAP), {
  [SYMBOLS.LF]: '',
  [SYMBOLS.CR]: '',
});

// Only for highlight purposes
export const BASE_MAP_REVERSE_HL = assign({}, BASE_MAP_REV, {
  [SYMBOLS.LF]: CHARACTERS.LF,
  [SYMBOLS.CR]: CHARACTERS.CR,
});


export const RE_BASE_REVERSE = new RegExp(
  `[${Object.keys(BASE_MAP_REV).join('')}]`, 'g'
);


const RAW_BASE = Object.keys(BASE_MAP).join('');
const SYM_BASE = Object.keys(_.invert(BASE_MAP)).join('');

const RAW_FULL = Object.keys(FULL_MAP).join('');
const SYM_FULL = Object.keys(_.invert(FULL_MAP)).join('');


const RE_RAW_BASE = new RegExp(`[${RAW_BASE}]`, 'g');

const RE_RAW_FULL = new RegExp(`[${RAW_FULL}]`, 'g');
const RE_SYM_FULL = new RegExp(`[${SYM_FULL}]`, 'g');


function spaceReplacer(match) {
  return Array(match.length + 1).join(SYMBOLS.SPACE);
}


function leadingSpaceReplacer(match) {
  return CHARACTERS.LF + spaceReplacer(match.substring(1));
}


function surroundingSpaceReplacer(match) {
  return match.substring(0).replace(/ +/g, spaceReplacer);
}


function trailingSpaceReplacer(match) {
  return spaceReplacer(match.substring(1)) + CHARACTERS.LF;
}


function mapSymbol(symbol, source, target) {
  const i = source.indexOf(symbol);
  return i >= 0 ? target.charAt(i) : symbol;
}


function replaceFullSymbol(match) {
  return mapSymbol(match, SYM_FULL, RAW_FULL);
}


function replaceFullRawChar(match) {
  return mapSymbol(match, RAW_FULL, SYM_FULL);
}


function replaceBaseRawChar(match) {
  return mapSymbol(match, RAW_BASE, SYM_BASE);
}


export function raw2sym(value, { isRawMode = false } = {}) {
  // in raw mode, replace all spaces;
  // otherwise, replace two or more spaces in a row
  let newValue = isRawMode ?
    value.replace(/ +/g, spaceReplacer) :
    value.replace(/ {2,}/g, spaceReplacer);
  // leading line spaces
  newValue = newValue.replace(/\n /g, leadingSpaceReplacer);
  // trailing line spaces
  newValue = newValue.replace(/ \n/g, trailingSpaceReplacer);
  // space before TAB or NBSP
  newValue = newValue.replace(/ [\t\u00A0]/g, surroundingSpaceReplacer);
  // space after TAB or NBSP
  newValue = newValue.replace(/[\t\u00A0] /g, surroundingSpaceReplacer);
  // space before punctuation
  newValue = newValue.replace(/ [:!?]/g, surroundingSpaceReplacer);
  // single leading document space
  newValue = newValue.replace(/^ /, spaceReplacer);
  // single trailing document space
  newValue = newValue.replace(/ $/, spaceReplacer);
  // regular newlines to LF + newlines
  newValue = newValue.replace(/\n/g, `${SYMBOLS.LF}${CHARACTERS.LF}`);
  // other symbols
  newValue = isRawMode ?
    newValue.replace(RE_RAW_FULL, replaceFullRawChar) :
    newValue.replace(RE_RAW_BASE, replaceBaseRawChar);

  return newValue;
}


export function sym2raw(value) {
  // LF + newlines to regular newlines
  let newValue = value.replace(/\u240A\n/g, CHARACTERS.LF);
  // orphaned LF to newlines as well
  newValue = newValue.replace(/\u240A/g, CHARACTERS.LF);
  // space dots to regular spaces
  newValue = newValue.replace(/\u2420/g, CHARACTERS.SPACE);
  // other symbols
  newValue = newValue.replace(RE_SYM_FULL, replaceFullSymbol);

  return newValue;
}
