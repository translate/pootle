/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { t } from 'utils/i18n';


const EditorPluralFormHeader = React.createClass({
  propTypes: {
    count: React.PropTypes.number.isRequired,
    index: React.PropTypes.number.isRequired,
  },

  render() {
    if (this.props.count === 1) {
      return null;
    }
    return (
      <div className="subheader">
        { t('Plural form %(index)s', { index: this.props.index }) }
      </div>
    );
  },
});


export default EditorPluralFormHeader;
