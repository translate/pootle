/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

export {
  applyFontFilter, unapplyFontFilter, isNewlineSymbol, countNewlineCharacter,
  countNewlineSymbol, removeNewlineChar, convertNewlineSymbolToChar,
} from './font';
export { decodeEntities } from './html';
export {
  highlightPunctuation, highlightEscapes, highlightHtml, nl2br,
} from './highlight';
export { normalizeCode } from './language';
export { escapeUnsafeRegexSymbols, makeRegexForMultipleWords } from './search';


export function getAreaId(index) {
  return `target_f_${index}`;
}
