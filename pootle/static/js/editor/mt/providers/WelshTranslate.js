/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import MTProvider from '../MTProvider';


class WelshTranslate extends MTProvider {

  constructor(apiKey) {
    super({
      apiKey,
      name: 'welsh-translate',
      displayName: 'Welsh Translate',
      url: 'https://api.techiaith.org/translate/v1/translate',
      supportedLanguages: ['en', 'cy'],
    });
  }

  getRequestBody(opts) {
    return {
      api_key: this.apiKey,
      q: opts.text,
      source: opts.sourceLanguage,
      target: opts.targetLanguage,
      engine: 'Meddalwedd',
    };
  }

  handleSuccess(response) {
    return {
      translation: response.translations[0].translatedText,
    };
  }
}


export default WelshTranslate;
