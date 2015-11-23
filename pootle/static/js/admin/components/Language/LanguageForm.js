/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { FormElement } from 'components/forms';
import { ModelFormMixin } from 'mixins/forms';

import ItemDelete from '../ItemDelete';


const LanguageForm = React.createClass({
  mixins: [ModelFormMixin],

  propTypes: {
    onSuccess: React.PropTypes.func.isRequired,
  },

  fields: ['code', 'fullname', 'specialchars', 'nplurals', 'pluralequation'],


  /* Handlers */

  handleSuccess(model) {
    // Add models at the beginning of the collection. When models exist,
    // we need to move them to the first position, as Backbone doesn't
    // honor the `at: <pos>` option in that scenario and there's
    // no modified time attribute that could be used for sorting.
    this.props.collection.unshift(model, {merge: true});
    this.props.collection.move(model, 0);

    this.props.onSuccess(model);
  },


  /* Layout */

  render() {
    let model = this.getResource();
    let { errors } = this.state;
    let { formData } = this.state;

    return (
      <form method="post"
            id="item-form"
            onSubmit={this.handleFormSubmit}>
        <div className="fields">
          <FormElement
            autoFocus={true}
            attribute="code"
            label={gettext('Code')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors} />
          <FormElement
            attribute="fullname"
            label={gettext('Full Name')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors} />
          <FormElement
            attribute="specialchars"
            label={gettext('Special Characters')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors} />
          <FormElement
            type="select"
            clearable={false}
            attribute="nplurals"
            options={model.getFieldChoices('nplurals')}
            label={gettext('Number of Plurals')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors} />
          <FormElement
            attribute="pluralequation"
            label={gettext('Plural Equation')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors} />
        </div>
        <div className="buttons">
          <input
            type="submit"
            className="btn btn-primary"
            disabled={!this.state.isDirty}
            value={gettext('Save')} />
        {model.id &&
          <ul className="action-links">
            <li><a href={model.getAbsoluteUrl()}>{gettext('Overview')}</a></li>
            <li><a href={model.getPermissionsUrl()}>{gettext('Permissions')}</a></li>
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
