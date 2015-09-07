/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import React from 'react';

import { FormElement } from 'components/forms';
import { ModelFormMixin } from 'mixins/forms';

import ItemDelete from './ItemDelete';


let UserForm = React.createClass({
  mixins: [ModelFormMixin],

  propTypes: {
    onSuccess: React.PropTypes.func.isRequired,
  },

  fields: [
      'username', 'is_active', 'password', 'full_name', 'email',
      'is_superuser', 'twitter', 'linkedin', 'website', 'bio'
  ],


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
    let deleteHelpText = gettext('Note: when deleting a user their contributions to the site, eg comments, suggestions and translations, are attributed to the anonymous user (nobody).');

    return (
      <form method="post"
            id="item-form"
            autoComplete="off"
            onSubmit={this.handleFormSubmit}>
        <div className="fields">
          <FormElement
              autoFocus={!model.isMeta()}
              readOnly={model.isMeta()}
              attribute="username"
              label={gettext('Username')}
              handleChange={this.handleChange}
              formData={formData}
              errors={errors} />
        {!model.isMeta() &&
          <div className="no-meta">
            <FormElement
                type="checkbox"
                attribute="is_active"
                label={gettext('Active')}
                handleChange={this.handleChange}
                formData={formData}
                errors={errors} />
            <FormElement
                type="password"
                attribute="password"
                label={gettext('Password')}
                placeholder={gettext('Set a new password')}
                handleChange={this.handleChange}
                formData={formData}
                errors={errors} />
          </div>}
          <FormElement
              autoFocus={model.isMeta()}
              attribute="full_name"
              label={gettext('Full Name')}
              handleChange={this.handleChange}
              formData={formData}
              errors={errors} />
          <FormElement
              attribute="email"
              label={gettext('Email')}
              handleChange={this.handleChange}
              formData={formData}
              errors={errors} />
        {!model.isMeta() &&
          <div className="no-meta">
            <FormElement
                type="checkbox"
                attribute="is_superuser"
                label={gettext('Administrator')}
                handleChange={this.handleChange}
                formData={formData}
                errors={errors} />
            <p className="divider" />
            <FormElement
                attribute="twitter"
                label={gettext('Twitter')}
                handleChange={this.handleChange}
                placeholder={gettext('Twitter username')}
                formData={formData}
                errors={errors}
                maxLength="15" />
            <FormElement
                attribute="linkedin"
                label={gettext('LinkedIn')}
                handleChange={this.handleChange}
                placeholder={gettext('LinkedIn profile URL')}
                formData={formData}
                errors={errors} />
            <FormElement
                attribute="website"
                label={gettext('Website')}
                handleChange={this.handleChange}
                placeholder={gettext('Personal website URL')}
                formData={formData}
                errors={errors} />
            <FormElement
                type="textarea"
                attribute="bio"
                label={gettext('Short Bio')}
                handleChange={this.handleChange}
                placeholder={gettext('Personal description')}
                formData={formData}
                errors={errors} />
          </div>}
        </div>
        <div className="buttons">
          <input type="submit" className="btn btn-primary"
                 disabled={!this.state.isDirty}
                 value={gettext('Save')} />
        {model.id &&
          <ul className="action-links">
            <li><a href={model.getProfileUrl()}>{gettext("Public Profile")}</a></li>
            <li><a href={model.getSettingsUrl()}>{gettext('Settings')}</a></li>
            <li><a href={model.getStatsUrl()}>{gettext("Statistics")}</a></li>
            <li><a href={model.getReportsUrl()}>{gettext("Reports")}</a></li>
          </ul>}
        </div>
      {(this.props.onDelete && !model.isMeta()) &&
        <div>
          <p className="divider" />
          <div className="buttons">
            <ItemDelete
              item={model}
              onDelete={this.props.onDelete}
              helpText={deleteHelpText}
            />
          </div>
        </div>}
      </form>
    );
  }

});


export default UserForm;
