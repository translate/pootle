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

import UnitPluralFormLabel from './UnitPluralFormLabel';

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
    id: PropTypes.number.isRequired,
    url: PropTypes.string.isRequired,
    dir: PropTypes.string.isRequired,
    isFuzzy: PropTypes.bool,
    language: PropTypes.string.isRequired,
    values: PropTypes.array.isRequired,
    type: PropTypes.string.isRequired, // original | translation
    innerComponent: React.PropTypes.func,
    labelComponent: React.PropTypes.func,
    getLabel: React.PropTypes.func,
    hasPlurals: React.PropTypes.bool.isRequired,
  },

  getDefaultProps() {
    return {
      innerComponent: InnerDiv,
      labelComponent: UnitPluralFormLabel,
      isFuzzy: false,
    };
  },

  getLabel(index) {
    if (this.props.getLabel) {
      return this.props.getLabel(index);
    }
    return `${index}`;
  },

  createValue(value, index) {
    return (
      <div
        className="translation-text"
        dir={this.props.dir}
        key={`${this.props.type}-value-${index}`}
        lang={this.props.language}
      >
        <this.props.labelComponent
          index={index}
          isShort
          hasPlurals={this.props.hasPlurals}
          getLabel={this.props.getLabel}
        />
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
        id={`${this.props.type}${this.props.id}`}
        data-target={this.props.url}
      >
        {this.props.values.map(this.createValue)}
      </div>
    );
  },

});


export default ViewUnit;
