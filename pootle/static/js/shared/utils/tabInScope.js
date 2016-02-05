/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import tabbable from 'tabbable';


export default function tabInScope(scopeNode, e) {
  const tabbableNodes = tabbable(scopeNode);
  const nodeIndex = tabbableNodes.indexOf(document.activeElement);

  // If it's at the edge of tabbable nodes, manually set the next focused node
  if ((e.shiftKey && nodeIndex === 0) ||
      (!e.shiftKey && nodeIndex === (tabbableNodes.length - 1))) {
    e.preventDefault();
    tabbableNodes[e.shiftKey ? tabbableNodes.length - 1 : 0].focus();
  }
}
