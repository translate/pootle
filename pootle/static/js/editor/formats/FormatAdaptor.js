/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import Editor from '../components/Editor';
import UnitSource from '../components/UnitSource';


const FormatAdaptor = {
  editorComponent: Editor,
  unitSourceComponent: UnitSource,
  getProps() {
    return {};
  },
};


export default FormatAdaptor;
