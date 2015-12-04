/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import MTProvider from '../MTProvider';


class GoogleTranslate extends MTProvider {

  constructor(apiKey) {
    super({
      apiKey,
      name: 'google-translate',
      displayName: 'Google Translate',
      url: 'https://www.googleapis.com/language/translate/v2',
      /* For a list of currently supported languages:
       * https://developers.google.com/translate/v2/using_rest#language-params
       *
       * Google supports translations between any of the supported languages
       * (any combination is acceptable)
       *
       * FIXME Note that an API does exist to query if Google supports
       * a given language
       */
      supportedLanguages: [
        'af', 'sq', 'ar', 'az', 'eu', 'bn', 'be', 'bg', 'ca', 'zh-CN', 'zh-TW', 'hr',
        'cs', 'da', 'nl', 'en', 'eo', 'et', 'tl', 'fi', 'fr', 'gl', 'ka', 'de', 'el',
        'gu', 'ht', 'iw', 'hi', 'hu', 'is', 'id', 'ga', 'it', 'ja', 'kn', 'ko', 'la',
        'lv', 'lt', 'mk', 'ms', 'mt', 'no', 'fa', 'pl', 'pt', 'ro', 'ru', 'sr', 'sk',
        'sl', 'es', 'sw', 'sv', 'ta', 'te', 'th', 'tr', 'uk', 'ur', 'vi', 'cy', 'yi',
      ],
    });
  }

  getRequestBody(opts) {
    return {
      key: this.apiKey,
      q: opts.text,
      source: opts.sourceLanguage,
      target: opts.targetLanguage,
    };
  }

  handleSuccess(response) {
    if (!response.data && !response.error) {
      return {
        msg: 'Malformed response from Google Translate API',
      };
    }

    if (response.error) {
      return {
        msg: `Google Translate Error: ${response.error.message}`,
      };
    }

    return {
      translation: response.data.translations[0].translatedText,
    };
  }

}


export default GoogleTranslate;
