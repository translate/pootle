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

  const loadFormat = PTL.editor.formats[options.fileType];
  if (loadFormat !== undefined) {
    loadFormat(props, onLoad);
  } else {
    onLoad(props, FormatAdaptor);
  }
}
