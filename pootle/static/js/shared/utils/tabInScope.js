/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import tabbable from 'tabbable';


export default function tabInScope(scopeNode, e) {
  e.preventDefault();

  const tabbableNodes = tabbable(scopeNode);
  const currentIndex = tabbableNodes.indexOf(document.activeElement);

  const nodesLength = tabbableNodes.length;
  let nextIndex;
  if (e.shiftKey) {
    // JS modulo is not actually modulo: http://stackoverflow.com/a/4467624/783019
    nextIndex = (((currentIndex - 1) % nodesLength) + nodesLength) % nodesLength;
  } else {
    nextIndex = (currentIndex + 1) % nodesLength;
  }

  tabbableNodes[nextIndex].focus();
}
