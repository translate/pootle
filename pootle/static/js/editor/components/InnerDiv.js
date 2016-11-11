/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { highlightRW } from '../../utils';


const InnerDiv = ({ value }) => (
  <div
    dangerouslySetInnerHTML={
      { __html: highlightRW(value) }
    }
  />
);

InnerDiv.propTypes = {
  value: React.PropTypes.string.isRequired,
};

export default InnerDiv;
