/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import assign from 'object-assign';

import fetch from 'utils/fetch';
import { normalizeCode } from '../utils';
import PlaceholderCleaner from './PlaceholderCleaner';


class MTProvider {

  constructor(opts) {
    this.method = 'GET';
    assign(this, opts);

    // FIXME: retrieve pairs asynchronously using provider APIs (#3718)
    this.pairs = opts.supportedLanguages.map((langCode) => [langCode, langCode]);

    $(document).on('click', `.js-${opts.name}`, (e) => {
      const sourceLang = e.currentTarget.dataset.sourceLang;
      this.translate(this.unit.sources[sourceLang][0], sourceLang,
                     this.unit.store.target_lang)
          .then(
            (result) => PTL.editor.setTranslation(result)
          );
    });
  }

  init(props) {
    this.unit = props.unit;

    this.injectUI(props);
  }

  /**
   * Checks whether the provided source language is supported
   * @param {string} target - language code
   */
  isSupportedSource(source) {
    return this.pairs.filter((pair) => pair[0] === source).length > 0;
  }

  /**
   * Checks whether the provided target language is supported
   * @param {string} target - language code
   */
  isSupportedTarget(target) {
    return this.pairs.filter((pair) => pair[1] === target).length > 0;
  }

  /**
   * Translates a text into another language
   * @param {string} text - text to be translated
   * @param {string} sourceLanguage - language code
   * @param {string} targetLanguage - language code
   */
  translate(sourceText, sourceLanguage, targetLanguage) {
    const placeholderCleaner = new PlaceholderCleaner();
    const bodyOpts = {
      sourceLanguage,
      targetLanguage,
      text: placeholderCleaner.replace(sourceText),
    };

    return fetch({
      crossDomain: true,
      method: this.method,
      url: this.url,
      body: this.getRequestBody(bodyOpts),
    }).then(
      (response) => this.handleSuccess(response)
    ).then(
      (result) => {
        if (!('translation' in result)) {
          return result;
        }
        const newResult = assign({}, result);
        newResult.translation = placeholderCleaner.recover(result.translation);
        return newResult;
      }
    );
  }

  handleSuccess() {
    throw new Error('Not Implemented');
  }

  /**
   * Injects the controls in the UI.
   * @param {object} props - the current unit
   */
  injectUI(props) {
    const { unit } = props;
    const targetLang = normalizeCode(unit.store.target_lang);

    if (this.isSupportedTarget(targetLang)) {
      Object.keys(unit.sources).forEach((sourceLanguage) => {
        const sourceLang = normalizeCode(sourceLanguage);

        if (this.isSupportedSource(sourceLang)) {
          $(`.js-mt-${sourceLang}`).append(
            this.renderIcon(sourceLang, targetLang)
          );
        }
      });
    }
  }

  renderIcon(sourceLang, targetLang) {
    const hint = `${this.displayName} (${sourceLang.toUpperCase()} &rarr; ` +
                 `${targetLang.toUpperCase()})`;
    return (
      `<a class="translate-mt js-${this.name}" data-source-lang="${sourceLang}">` +
        `<i class="icon-${this.name}" title="${hint}">` +
      '</a>'
    );
  }

}


export default MTProvider;
