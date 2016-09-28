/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';

import { t } from 'utils/i18n';


const L20nEditorMode = React.createClass({
  propTypes: {
    onChange: React.PropTypes.func.isRequired,
  },

  getInitialState() {
    return {
      isEnabled: false,
    };
  },

  handleClick() {
    const isEnabled = !this.state.isEnabled;
    this.setState({ isEnabled });
    if (this.props.onChange) {
      this.props.onChange({ enableRichMode: isEnabled });
    }
  },

  render() {
    const classNames = cx('js-toggle-l20n', {
      selected: this.state.isEnabled,
    });

    return (
      <a
        className={classNames}
        onClick={this.handleClick}
      >
        <i className="icon-edit" title={t('L20n Rich Editor')} />
      </a>
    );
  },

});


export default L20nEditorMode;
