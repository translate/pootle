/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import CodeMirror from 'codemirror';
import 'codemirror/lib/codemirror.css';


/**
 * Maps markup module names from settings to CodeMirror mode names
 */
function getMode(markup) {
  return {
    html: 'htmlmixed',
    restructuredtext: 'rst',
  }[markup] || markup;
}


const staticpages = {

  init(opts) {
    const element = document.querySelector(opts.el);
    const mode = getMode(opts.markup);

    // Using webpack's `bundle` loader so each mode goes into a separate chunk
    const bundledResult = require(`bundle!codemirror/mode/${mode}/${mode}.js`);
    bundledResult(() => {
      CodeMirror.fromTextArea(element, {
        mode: mode,
        lineWrapping: true,
      });
    });
  },

}


export default staticpages;
