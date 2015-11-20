/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import DMP from 'diff-match-patch';

import { fancyEscape } from '../../utils';


const dmp = new DMP();


export default function diff(a, b) {
  const diff = dmp.diff_main(a, b);
  let html = [];

  dmp.diff_cleanupSemantic(diff);

  for (let i=0; i<diff.length; i++) {
    const op = diff[i][0];
    const text = fancyEscape(diff[i][1]);
    if (op === DMP.DIFF_INSERT) {
      html[i] = `<span class="diff-insert">${text}</span>`;
    } else if (op === DMP.DIFF_DELETE) {
      html[i] = `<span class="diff-delete">${text}</span>`;
    } else if (op === DMP.DIFF_EQUAL) {
      html[i] = text;
    }
  }

  return html.join('');
}
