/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import MTProvider from '../MTProvider';


class CaighdeanTranslate extends MTProvider {

  constructor(apiKey) {
    super({
      apiKey,
      method: 'POST',
      name: 'caighdean-translate',
      displayName: 'Caighdeán Translate',
      url: 'https://borel.slu.edu/cgi-bin/seirbhis3.cgi',
      supportedLanguages: ['gd', 'gv', 'ga', 'ga_IE', 'ga-IE'],
    });
  }

  getRequestBody(opts) {
    return {
      teacs: opts.text,
      foinse: opts.sourceLanguage,
    };
  }

  handleSuccess(response) {
    const trimmed = /^([.,\/;”:!?%})]|<[^>]+>)$/;
    let text = '';
    for (let i = 0; i < response.length; i++) {
      let token = response[i][1];
      if (!token.match(trimmed) && text !== '') {
        token = ` ${token}`;
      }
      text = text + token;
    }
    return {
      translation: text.trim(),
    };
  }
}


export default CaighdeanTranslate;
