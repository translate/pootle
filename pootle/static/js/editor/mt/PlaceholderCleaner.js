/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

const HTML_PAT = /<[\/]?\w+.*?>/g;
// The printf regex based on http://phpjs.org/functions/sprintf:522
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
    this.sourceText = null;
  }

  collectArguments(s) {
    this.argSubs[this.argPos] = s;
    return `[${this.argPos++}]`;
  }

  replace(text) {
    this.sourceText = text;

    // Walk through known patterns and replace them with [N] placeholders
    return text.replace(HTML_PAT, (s) => this.collectArguments(s))
               .replace(C_PRINTF_PAT, (s) => this.collectArguments(s))
               .replace(C_SHARP_STR_PAT, (s) => this.collectArguments(s))
               .replace(PERCENT_NUMBER_PAT, (s) => this.collectArguments(s));
  }

  recover(translation) {
    const { argSubs, sourceText } = this;

    if (sourceText === null) {
      throw new Error('Attempted to recover without calling `replace()` first');
    }

    // Fix whitespace which may have been added around [N] blocks
    for (let i=0; i<argSubs.length; i++) {
      if (sourceText.match(new RegExp('\\[' + i + '\\][^\\s]'))) {
        translation = translation.replace(
          new RegExp('\\[' + i + '\\]\\s+'), '[' + i + ']'
        );
      }
      if (sourceText.match(new RegExp('[^\\s]\\[' + i + '\\]'))) {
        translation = translation.replace(
          new RegExp('\\s+\\[' + i + '\\]'), '[' + i + ']'
        );
      }
    }

    // Replace temporary [N] placeholders back to their real values
    for (let i=0; i<argSubs.length; i++) {
      const value = argSubs[i].replace(/\&/g, '&amp;')
                              .replace(/\</g, '&lt;')
                              .replace(/\>/g, '&gt;');
      translation = translation.replace('[' + i + ']', value);
    }

    this.resetState();

    return translation;
  }

}


export default PlaceholderCleaner;
