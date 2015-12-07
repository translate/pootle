/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import LanguageForm from './LanguageForm';


const LanguageAdd = React.createClass({

  propTypes: {
    collection: React.PropTypes.object.isRequired,
    model: React.PropTypes.func.isRequired,
    onCancel: React.PropTypes.func.isRequired,
    onSuccess: React.PropTypes.func.isRequired,
  },

  render() {
    const Model = this.props.model;
    return (
      <div className="item-add">
        <div className="hd">
          <h2>{gettext('Add Language')}</h2>
          <button
            onClick={this.props.onCancel}
            className="btn btn-primary"
          >
            {gettext('Cancel')}
          </button>
        </div>
        <div className="bd">
          <LanguageForm
            model={new Model()}
            collection={this.props.collection}
            onSuccess={this.props.onSuccess}
          />
        </div>
      </div>
    );
  },

});


export default LanguageAdd;
