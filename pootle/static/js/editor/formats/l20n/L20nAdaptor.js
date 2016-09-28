/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import L20nEditor from './L20nEditor';
import L20nSource from './L20nSource';
import L20nEditorMode from './L20nEditorMode';


const L20nAdaptor = {
  editorComponent: L20nEditor,
  unitSourceComponent: L20nSource,
  editorModeButton: L20nEditorMode,
  getProps(props) {
    return { enableRichMode: props.enableRichMode };
  },
};


export default L20nAdaptor;
