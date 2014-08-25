'use strict';

var React = require('react/addons');

var linkify = require('autolinker').link;

var FormElement = require('../components/forms').FormElement;
var ModelFormMixin = require('../mixins/forms').ModelFormMixin;


var UserProfileForm = React.createClass({
  mixins: [ModelFormMixin],

  fields: ['full_name', 'twitter', 'linkedin', 'website', 'bio'],


  /* Handlers */

  handleSuccess: function (user) {
    this.props.handleSuccess(user);
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
                       model={model}
                       errors={errors} />
          <p>
            <label>{gettext('Avatar')}</label>
            <img className="gravatar" height="48" width="48"
                 src={model.gravatarUrl()} />
            <span className="helptext"
                  dangerouslySetInnerHTML={{__html: linkify(avatarHelp)}} />
          </p>
          <p className="divider" />
          <FormElement attribute="twitter"
                       label={gettext('Twitter')}
                       handleChange={this.handleChange}
                       placeholder={gettext('Your Twitter username')}
                       formData={formData}
                       model={model}
                       errors={errors}
                       maxLength="15" />
          <FormElement attribute="linkedin"
                       label={gettext('LinkedIn')}
                       handleChange={this.handleChange}
                       placeholder={gettext('Your LinkedIn profile URL')}
                       formData={formData}
                       model={model}
                       errors={errors} />
          <FormElement attribute="website"
                       label={gettext('Website')}
                       handleChange={this.handleChange}
                       placeholder={gettext('Your Personal website/blog URL')}
                       formData={formData}
                       model={model}
                       errors={errors} />
          <FormElement type="textarea"
                       attribute="bio"
                       label={gettext('Short Bio')}
                       handleChange={this.handleChange}
                       placeholder={gettext(
                         'Why are you part of our translation project? ' +
                         'Describe yourself, inspire others!')}
                       formData={formData}
                       model={model}
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
  }

});


module.exports = {
  UserProfileForm: UserProfileForm
};
