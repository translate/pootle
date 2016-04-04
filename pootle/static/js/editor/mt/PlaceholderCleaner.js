/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

const HTML_PAT = /<[\/]?\w+.*?>/g;
// The printf regex based on http://phpjs.org/functions/sprintf:522
// eslint-disable-next-line max-len
const C_PRINTF_PAT = /%%|%(\d+\$)?([-+\'#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuidfegEG])/g;
const C_SHARP_STR_PAT = /{\d+(,\d+)?(:[a-zA-Z ]+)?}/g;
const PERCENT_NUMBER_PAT = /%\d+/g;


class PlaceholderCleaner {

  constructor() {
    this.resetState();
  }

  resetState() {
    this.argSubs = [];
    this.argPos = 0;
    this.replacedSourceText = null;
  }

  collectArguments(s) {
    this.argSubs[this.argPos] = s;
    return `[${this.argPos++}]`;
  }

  replace(text) {
    // Walk through known patterns and replace them with [N] placeholders
    this.replacedSourceText = text
      .replace(HTML_PAT, (s) => this.collectArguments(s))
      .replace(C_PRINTF_PAT, (s) => this.collectArguments(s))
      .replace(C_SHARP_STR_PAT, (s) => this.collectArguments(s))
      .replace(PERCENT_NUMBER_PAT, (s) => this.collectArguments(s));

    return this.replacedSourceText;
  }

  recover(translation) {
    const { argSubs, replacedSourceText } = this;

    if (replacedSourceText === null) {
      throw new Error('Attempted to recover without calling `replace()` first');
    }

    let recoveredTranslation = translation;
    // Fix whitespace which may have been added around [N] blocks
    for (let i = 0; i < argSubs.length; i++) {
      if (replacedSourceText.match(new RegExp(`\\[${i}\\][^\\s]`))) {
        recoveredTranslation = recoveredTranslation.replace(
          new RegExp(`\\[${i}\\]\\s+`), `[${i}]`
        );
      }
      if (replacedSourceText.match(new RegExp(`[^\\s]\\[${i}\\]`))) {
        recoveredTranslation = recoveredTranslation.replace(
          new RegExp(`\\s+\\[${i}\\]`), `[${i}]`
        );
      }
    }

    // Replace temporary [N] placeholders back to their real values
    for (let i = 0; i < argSubs.length; i++) {
      const value = argSubs[i].replace(/\&/g, '&amp;')
                              .replace(/\</g, '&lt;')
                              .replace(/\>/g, '&gt;');
      recoveredTranslation = recoveredTranslation.replace(`[${i}]`, value);
    }

    this.resetState();

    return recoveredTranslation;
  }

}


export default PlaceholderCleaner;
