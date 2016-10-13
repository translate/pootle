/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import FormElement from 'components/FormElement';
import ModelFormMixin from 'mixins/ModelFormMixin';

import ItemDelete from '../ItemDelete';


const LanguageForm = React.createClass({

  propTypes: {
    collection: React.PropTypes.object.isRequired,
    onDelete: React.PropTypes.func,
    onSuccess: React.PropTypes.func.isRequired,
  },

  mixins: [ModelFormMixin],

  fields: ['code', 'fullname', 'specialchars', 'nplurals', 'pluralequation'],


  /* Handlers */

  handleSuccess(model) {
    this.props.onSuccess(model);
  },


  /* Layout */

  render() {
    const model = this.getResource();
    const { errors } = this.state;
    const { formData } = this.state;

    return (
      <form
        method="post"
        id="item-form"
        onSubmit={this.handleFormSubmit}
      >
        <div className="fields">
          <FormElement
            autoFocus
            disabled={model.hasOwnProperty('id')}
            label={gettext('Code')}
            handleChange={this.handleChange}
            name="code"
            errors={errors.code}
            value={formData.code}
          />
          <FormElement
            label={gettext('Full Name')}
            handleChange={this.handleChange}
            name="fullname"
            errors={errors.fullname}
            value={formData.fullname}
          />
          <FormElement
            label={gettext('Special Characters')}
            handleChange={this.handleChange}
            name="specialchars"
            errors={errors.specialchars}
            value={formData.specialchars}
          />
          <FormElement
            type="select"
            clearable={false}
            options={model.getFieldChoices('nplurals')}
            label={gettext('Number of Plurals')}
            handleChange={this.handleChange}
            name="nplurals"
            errors={errors.nplurals}
            value={formData.nplurals}
          />
          <FormElement
            label={gettext('Plural Equation')}
            handleChange={this.handleChange}
            name="pluralequation"
            errors={errors.pluralequation}
            value={formData.pluralequation}
          />
        </div>
        <div className="buttons">
          <input
            type="submit"
            className="btn btn-primary"
            disabled={!this.state.isDirty}
            value={gettext('Save')}
          />
        {model.id &&
          <ul className="action-links">
            <li><a href={model.getAbsoluteUrl()}>{gettext('Overview')}</a></li>
            <li><a href={model.getTeamUrl()}>{gettext('Team')}</a></li>
          </ul>}
        </div>
      {this.props.onDelete &&
        <div>
          <p className="divider" />
          <div className="buttons">
            <ItemDelete item={model} onDelete={this.props.onDelete} />
          </div>
        </div>}
      </form>
    );
  },

});


export default LanguageForm;
