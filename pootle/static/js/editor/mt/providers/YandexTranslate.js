/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import MTProvider from '../MTProvider';


class YandexTranslate extends MTProvider {

  constructor(apiKey) {
    super({
      apiKey,
      name: 'yandex-translate',
      displayName: 'Yandex.Translate',
      url: 'https://translate.yandex.net/api/v1.5/tr.json/translate',
      /* For a list of currently supported languages:
       * https://tech.yandex.com/translate/doc/dg/concepts/langs-docpage/
       * The service translates between any of these listed languages.
       *
       * For a list of language pairs:
       * https://translate.yandex.net/api/v1.5/tr.json/getLangs?key=API_KEY
       * The results returned indicate permissible pairs, this code makes no
       * assumptions about directionality.
       */
      supportedLanguages: [
        'ar', 'az', 'be', 'bg', 'bs', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es',
        'et', 'fi', 'fr', 'he', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'ka',
        'ko', 'lt', 'lv', 'mk', 'ms', 'mt', 'nl', 'no', 'pl', 'pt', 'ro', 'ru',
        'sk', 'sl', 'sq', 'sr', 'sv', 'th', 'tr', 'uk', 'vi', 'zh'
      ],
    });
  }

  getRequestBody(opts) {
    return {
      key: this.apiKey,
      text: opts.text,
      lang: `${opts.sourceLanguage}-${opts.targetLanguage}`,
    };
  }

  handleSuccess(response) {
    return {
      translation: response.text[0],
    };
  }

}


export default YandexTranslate;
