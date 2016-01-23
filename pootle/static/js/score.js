/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import ReactDOM from 'react-dom';

import Score from 'components/Score';


function init(value) {
  ReactDOM.render(
    <Score value={value} />,
    document.querySelector('.js-score')
  );
}


export default {
  init,
  set: init,
};
