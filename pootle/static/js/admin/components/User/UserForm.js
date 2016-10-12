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


const UserForm = React.createClass({

  propTypes: {
    collection: React.PropTypes.object.isRequired,
    onDelete: React.PropTypes.func,
    onSuccess: React.PropTypes.func.isRequired,
  },

  mixins: [ModelFormMixin],

  fields: [
    'username', 'is_active', 'password', 'full_name', 'email',
    'is_superuser', 'twitter', 'linkedin', 'website', 'bio',
  ],


  /* Handlers */

  handleSuccess(model) {
    this.props.onSuccess(model);
  },


  /* Layout */

  render() {
    const model = this.getResource();
    const { errors } = this.state;
    const { formData } = this.state;
    const deleteHelpText = gettext(
      'Note: when deleting a user their contributions to the site, ' +
      'e.g. comments, suggestions and translations, are attributed ' +
      'to the anonymous user (nobody).'
    );

    return (
      <form
        method="post"
        id="item-form"
        autoComplete="off"
        onSubmit={this.handleFormSubmit}
      >
        <div className="fields">
          <FormElement
            autoFocus={!model.isMeta()}
            readOnly={model.isMeta()}
            label={gettext('Username')}
            handleChange={this.handleChange}
            name="username"
            errors={errors.username}
            value={formData.username}
          />
        {!model.isMeta() &&
          <div className="no-meta">
            <FormElement
              type="checkbox"
              label={gettext('Active')}
              handleChange={this.handleChange}
              name="is_active"
              errors={errors.is_active}
              value={formData.is_active}
            />
            <FormElement
              type="password"
              label={gettext('Password')}
              placeholder={gettext('Set a new password')}
              handleChange={this.handleChange}
              name="password"
              errors={errors.password}
              value={formData.password}
            />
          </div>}
          <FormElement
            autoFocus={model.isMeta()}
            label={gettext('Full Name')}
            handleChange={this.handleChange}
            name="full_name"
            errors={errors.full_name}
            value={formData.full_name}
          />
          <FormElement
            label={gettext('Email')}
            handleChange={this.handleChange}
            name="email"
            errors={errors.email}
            value={formData.email}
          />
        {!model.isMeta() &&
          <div className="no-meta">
            <FormElement
              type="checkbox"
              label={gettext('Administrator')}
              handleChange={this.handleChange}
              name="is_superuser"
              errors={errors.is_superuser}
              value={formData.is_superuser}
            />
            <p className="divider" />
            <FormElement
              label={gettext('Twitter')}
              handleChange={this.handleChange}
              placeholder={gettext('Twitter username')}
              maxLength="15"
              name="twitter"
              errors={errors.twitter}
              value={formData.twitter}
            />
            <FormElement
              label={gettext('LinkedIn')}
              handleChange={this.handleChange}
              placeholder={gettext('LinkedIn profile URL')}
              name="linkedin"
              errors={errors.linkedin}
              value={formData.linkedin}
            />
            <FormElement
              label={gettext('Website')}
              handleChange={this.handleChange}
              placeholder={gettext('Personal website URL')}
              name="website"
              errors={errors.website}
              value={formData.website}
            />
            <FormElement
              type="textarea"
              label={gettext('Short Bio')}
              handleChange={this.handleChange}
              placeholder={gettext('Personal description')}
              name="bio"
              errors={errors.bio}
              value={formData.bio}
            />
          </div>}
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
            <li><a href={model.getProfileUrl()}>{gettext('Public Profile')}</a></li>
            <li><a href={model.getSettingsUrl()}>{gettext('Settings')}</a></li>
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
  },

});


export default UserForm;
