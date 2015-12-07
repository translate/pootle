/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import { link } from 'autolinker';
import React from 'react';

import FormElement from 'components/FormElement';
import { ModelFormMixin } from 'mixins/forms';

import Avatar from 'components/Avatar';


// XXX: should probably live somewhere else
function linkify(input) {
  return {
    __html: link(input),
  };
}


export const UserProfileForm = React.createClass({

  propTypes: {
    onDirty: React.PropTypes.func.isRequired,
    onSuccess: React.PropTypes.func.isRequired,
  },

  mixins: [ModelFormMixin],

  /* Lifecycle */

  componentWillUpdate(nextProps, nextState) {
    if (nextState.isDirty !== this.state.isDirty) {
      this.props.onDirty(nextState.isDirty);
    }
  },

  fields: ['full_name', 'twitter', 'linkedin', 'website', 'bio'],

  /* Handlers */

  handleSuccess(user) {
    this.props.onSuccess(user);
  },


  /* Layout */

  render() {
    const model = this.getResource();
    const { errors } = this.state;
    const { formData } = this.state;
    const avatarHelpMsg = gettext(
      'To set or change your avatar for your email address ' +
      '(%(email)s), please go to gravatar.com.'
    );
    const avatarHelp = interpolate(avatarHelpMsg, {email: model.get('email')},
                                   true);

    return (
      <form method="post"
            id="item-form"
            autoComplete="off"
            onSubmit={this.handleFormSubmit}>
        <div className="fields">
          <FormElement attribute="full_name"
                       label={gettext('Full Name')}
                       placeholder={gettext('Your Full Name')}
                       autoFocus={true}
                       handleChange={this.handleChange}
                       formData={formData}
                       errors={errors} />
          <p>
            <label>{gettext('Avatar')}</label>
            <Avatar email={model.get('email')} size={48} />
            <span className="helptext"
                  dangerouslySetInnerHTML={linkify(avatarHelp)} />
          </p>
          <p className="divider" />
          <FormElement attribute="twitter"
                       label={gettext('Twitter')}
                       handleChange={this.handleChange}
                       placeholder={gettext('Your Twitter username')}
                       formData={formData}
                       errors={errors}
                       maxLength="15" />
          <FormElement attribute="linkedin"
                       label={gettext('LinkedIn')}
                       handleChange={this.handleChange}
                       placeholder={gettext('Your LinkedIn profile URL')}
                       formData={formData}
                       errors={errors} />
          <FormElement attribute="website"
                       label={gettext('Website')}
                       handleChange={this.handleChange}
                       placeholder={gettext('Your Personal website/blog URL')}
                       formData={formData}
                       errors={errors} />
          <FormElement type="textarea"
                       attribute="bio"
                       label={gettext('Short Bio')}
                       handleChange={this.handleChange}
                       placeholder={gettext(
                         'Why are you part of our translation project? ' +
                         'Describe yourself, inspire others!')}
                       formData={formData}
                       errors={errors} />
        </div>
        <p className="buttons">
          <input type="submit"
                 className="btn btn-primary"
                 disabled={!this.state.isDirty}
                 value={gettext('Save')} />
        </p>
      </form>
    );
  },

});
