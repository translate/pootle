/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var React = require('react');

var link = require('autolinker').link;

var FormElement = require('components/forms').FormElement;
var ModelFormMixin = require('mixins/forms').ModelFormMixin;

import Avatar from 'components/Avatar';


// XXX: should probably live somewhere else
var linkify = function (input) {
  return {
    __html: link(input),
  };
};


var UserProfileForm = React.createClass({
  mixins: [ModelFormMixin],

  propTypes: {
    onDirty: React.PropTypes.func.isRequired,
    onSuccess: React.PropTypes.func.isRequired,
  },

  fields: ['full_name', 'twitter', 'linkedin', 'website', 'bio'],


  /* Lifecycle */

  componentWillUpdate: function (nextProps, nextState) {
    if (nextState.isDirty !== this.state.isDirty) {
      this.props.onDirty(nextState.isDirty);
    }
  },


  /* Handlers */

  handleSuccess: function (user) {
    this.props.onSuccess(user);
  },


  /* Layout */

  render: function () {
    var model = this.getResource();
    var errors = this.state.errors;
    var formData = this.state.formData;
    var avatarHelp = gettext(
      'To set or change your avatar for your email address ' +
      '(%(email)s), please go to gravatar.com.'
    );
    avatarHelp = interpolate(avatarHelp, {email: model.get('email')}, true);

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


module.exports = {
  UserProfileForm: UserProfileForm,
};
