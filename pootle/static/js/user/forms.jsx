'use strict';

var React = require('react/addons');

var linkify = require('autolinker').link;

var FormElement = require('../components/forms').FormElement;
var BackboneMixin = require('../mixins/backbone');
var FormValidationMixin = require('../mixins/forms');


var UserProfileForm = React.createClass({
  mixins: [FormValidationMixin, BackboneMixin],

  /* BackboneMixin */
  getResource: function () {
    return this.props.model;
  },

  fields: ['full_name', 'twitter', 'linkedin', 'website', 'bio'],


  /* Lifecycle */

  getInitialState: function () {
    var initialData = _.pick(this.props.model.toJSON(), this.fields);
    return {
      initialData: _.extend({}, initialData),
      formData: _.extend({}, initialData),
      isDirty: false
    };
  },


  /* Handlers */

  handleChange: function (name, value) {
    var newData = _.extend({}, this.state.formData);
    newData[name] = value;
    var isDirty = !_.isEqual(newData, this.state.initialData);
    this.setState({formData: newData, isDirty: isDirty});
  },

  handleSubmit: function (e) {
    e.preventDefault();

    this.props.model.save(this.state.formData, {wait: true})
                    .done(this.handleSuccess)
                    .error(this.handleError);

  },

  handleSuccess: function () {
    // Cleanup state
    this.clearValidation();
    this.setState({
      initialData: _.extend({}, this.state.formData),
      isDirty: false
    });

    this.props.handleSuccess(this.props.model);
  },

  handleError: function (xhr) {
    this.validateResponse(xhr);
  },


  /* Layout */

  render: function () {
    var model = this.props.model;
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
            onSubmit={this.handleSubmit}>
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
