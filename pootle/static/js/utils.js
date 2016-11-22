/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';

import 'select2';

import { qAll } from 'utils/dom';

import {
  highlightPunctuation, highlightEscapes, highlightHtml,
  highlightSymbols, nl2br,
} from './editor/utils';
import { raw2sym } from './editor/utils/font';


/* Gets current URL's hash */
export function getHash(win) {
  // Mozilla has a bug when it automatically unescapes %26 to '&'
  // when getting hash from `window.location.hash'.
  // So, we have to extract it from the `window.location'.
  // Also, we don't need to decodeURIComponent() the hash
  // as it will break encoded ampersand again
  // (decoding can be done on the higher level, if needed)
  return (win || window).location.toString().split('#', 2)[1] || '';
}


function decodeURIParameter(s) {
  return decodeURIComponent(s.replace(/\+/g, ' '));
}


export function getParsedHash(hash) {
  const params = {};
  const r = /([^&;=]+)=?([^&;]*)/g;

  let h = hash;
  if (h === undefined) {
    h = getHash();
  }

  let e = r.exec(h);
  while (e !== null) {
    params[decodeURIParameter(e[1])] = decodeURIParameter(e[2]);
    e = r.exec(h);
  }
  return params;
}


/* Updates current URL's hash */
export function updateHashPart(part, newVal, removeArray, hash) {
  const r = /([^&;=]+)=?([^&;]*)/g;
  const params = [];
  let h = hash;
  if (h === undefined) {
    h = getHash();
  }
  let ok = false;
  let e = r.exec(h);

  while (e !== null) {
    const p = decodeURIParameter(e[1]);
    if (p === part) {
      // replace with the given value
      params.push([e[1], encodeURIComponent(newVal)].join('='));
      ok = true;
    } else if ($.inArray(p, removeArray) === -1) {
      // use the parameter as is
      params.push([e[1], e[2]].join('='));
    }

    e = r.exec(h);
  }
  // if there was no old parameter, push the param at the end
  if (!ok) {
    params.push([encodeURIComponent(part),
      encodeURIComponent(newVal)].join('='));
  }
  return params.join('&');
}


/* Cross-browser comparison function */
export function strCmp(a, b) {
  let rv;
  if (a === b) {
    rv = 0;
  } else if (a < b) {
    rv = -1;
  } else {
    rv = 1;
  }
  return rv;
}


export function highlightRO(text) {
  return (
    nl2br(
      highlightEscapes(
        highlightHtml(
          raw2sym(
            // FIXME: CRLF => LF replacement happens here because highlighting
            // currently happens via many DOM sources, and this ensures the less
            // error-prone behavior. This won't be needed when the entire editor
            // is managed as a component.
            text.replace(/\r\n/g, '\n')
          )
        )
      )
    )
  );
}


export function highlightRW(text) {
  return (
    highlightSymbols(
      nl2br(
        highlightPunctuation(
          highlightEscapes(
            highlightHtml(
              raw2sym(
                // FIXME: CRLF => LF replacement happens here because highlighting
                // currently happens via many DOM sources, and this ensures the less
                // error-prone behavior. This won't be needed when the entire editor
                // is managed as a component.
                text.replace(/\r\n/g, '\n')
              )
            , 'js-editor-copytext')
          , 'js-editor-copytext')
        , 'js-editor-copytext')
      )
    , 'js-editor-copytext')
  );
}


function highlightNodes(selector, highlightFn) {
  qAll(selector).forEach(
    (translationTextNode) => {
      const dataString = translationTextNode.dataset.string;
      const textValue = (
        dataString ? JSON.parse(`"${dataString}"`) :
        translationTextNode.textContent
      );
      // eslint-disable-next-line no-param-reassign
      translationTextNode.innerHTML = highlightFn(textValue);
    }
  );
}


export function highlightRONodes(selector) {
  return highlightNodes(selector, highlightRO);
}


export function highlightRWNodes(selector) {
  return highlightNodes(selector, highlightRW);
}


/* Converts the elements matched by `selector` into selectable inputs.
 *
 * `onChange` function will be fired when the select choice changes.
 */
export function makeSelectableInput(selector, options, onChange, onSelecting) {
  // XXX: Check if this works with multiple selects per page
  const $el = $(selector);

  if (!$el.length) {
    return;
  }
  $el.select2(options).on('select2:unselecting', function () {
    $(this).data('state', 'unselected');
  }).on('select2:open', function () {
    if ($(this).data('state') === 'unselected') {
      $(this).removeData('state');
      $(this).select2('close');
    }
  });
  $el.on('change', onChange);
  $el.on('select2-selecting', onSelecting);
  $('.select2-selection__rendered').removeAttr('title');
}


export function executeFunctionByName(functionName, ctx, ...args) {
  const namespaces = functionName.split('.');
  const func = namespaces.pop();

  let context = ctx;
  for (let i = 0; i < namespaces.length; i++) {
    context = context[namespaces[i]];
  }

  return context[func].apply(this, args);
}


export function blinkClass($elem, className, n, delay) {
  $elem.toggleClass(className);
  if (n > 1) {
    setTimeout(() => blinkClass($elem, className, n - 1, delay), delay);
  }
}


export default {
  blinkClass,
  executeFunctionByName,
  highlightRO,
  highlightRW,
  highlightRONodes,
  highlightRWNodes,
  getHash,
  getParsedHash,
  makeSelectableInput,
  strCmp,
  updateHashPart,
};
