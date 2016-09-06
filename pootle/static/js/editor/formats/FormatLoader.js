/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';

import FormatAdaptor from './FormatAdaptor';


/* Detects format adaptor by options and runs onLoad callback with it */
export function loadFormatAdaptor(options, onLoad) {
  const props = assign({}, options);
  delete props.fileType;

  switch (options.fileType) {
    // temporary use l20n adaptor for .po files
    case 'po':
    case 'ftl':
    case 'l20n':
      require.ensure(['./l20n/L20nAdaptor.js'], (require) => {
        const adaptor = require('./l20n/L20nAdaptor.js');
        onLoad(props, adaptor.default);
      });
      break;

    default: {
      onLoad(props, FormatAdaptor);
    }
  }
}
