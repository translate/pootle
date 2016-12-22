/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React, { PropTypes } from 'react';

import { highlightRO } from '../../utils';


const InnerDiv = ({ value }) => (
  <div
    className="view-unit-value"
    dangerouslySetInnerHTML={
      { __html: highlightRO(value) }
    }
  />
);

InnerDiv.propTypes = {
  value: React.PropTypes.string.isRequired,
};


const ViewUnit = React.createClass({

  propTypes: {
    dir: PropTypes.string.isRequired,
    isFuzzy: PropTypes.bool,
    language: PropTypes.string.isRequired,
    values: PropTypes.array.isRequired,
    type: PropTypes.string.isRequired, // original | translation
    innerComponent: React.PropTypes.func,
    getPluralFormName: React.PropTypes.func,
    hasPlurals: React.PropTypes.bool.isRequired,
  },

  getDefaultProps() {
    return {
      innerComponent: InnerDiv,
      isFuzzy: false,
    };
  },

  getPluralFormName(index) {
    if (this.props.getPluralFormName !== undefined) {
      return this.props.getPluralFormName(index);
    }

    return `[${index}]`;
  },

  createValue(value, index) {
    return (
      <div
        className="translation-text"
        dir={this.props.dir}
        key={`${this.props.type}-value-${index}`}
        lang={this.props.language}
      >
        {this.props.hasPlurals &&
          <div
            className="plural-form-label"
          >{ this.getPluralFormName(index) }</div>
        }
        <this.props.innerComponent value={value} />
      </div>
    );
  },

  render() {
    const classNames = cx(`translate-${this.props.type}`, 'translate-view', {
      'fuzzy-unit': this.props.isFuzzy,
    });

    return (
      <div
        dir={this.props.dir}
        className={classNames}
      >
        {this.props.values.map(this.createValue)}
      </div>
    );
  },

});


export default ViewUnit;
