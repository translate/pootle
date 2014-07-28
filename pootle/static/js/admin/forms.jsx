var React = require('react/addons');

var BackboneMixin = require('../mixins/backbone');
var FormValidationMixin = require('../mixins/forms');

var FormElement = require('../components/forms').FormElement;


var UserForm = React.createClass({
  mixins: [FormValidationMixin, BackboneMixin],

  /* BackboneMixin */
  getResource: function () {
    return this.props.model;
  },

  fields: [
      'username', 'is_active', 'password', 'full_name', 'email',
      'is_superuser', 'twitter', 'linkedin', 'website', 'bio'
  ],


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
    // Add models at the beginning of the collection. When models exist,
    // we need to move them to the first position, as Backbone doesn't
    // honor the `at: <pos>` option in that scenario and there's
    // no modified time attribute that could be used for sorting.
    this.props.collection.unshift(this.props.model, {merge: true});
    this.props.collection.move(this.props.model, 0);

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

    return (
      <form method="post"
            id="item-form"
            autoComplete="off"
            onSubmit={this.handleSubmit}>
        <div className="fields">
          <FormElement
              autoFocus
              attribute="username"
              label={gettext('Username')}
              handleChange={this.handleChange}
              formData={formData}
              model={model}
              errors={errors} />
          <FormElement
              type="checkbox"
              attribute="is_active"
              label={gettext('Active')}
              handleChange={this.handleChange}
              formData={formData}
              model={model}
              errors={errors} />
          <FormElement
              type="password"
              attribute="password"
              label={gettext('Password')}
              placeholder={gettext('Set a new password')}
              handleChange={this.handleChange}
              formData={formData}
              model={model}
              errors={errors} />
          <FormElement
              attribute="full_name"
              label={gettext('Full Name')}
              handleChange={this.handleChange}
              formData={formData}
              model={model}
              errors={errors} />
          <FormElement
              attribute="email"
              label={gettext('Email')}
              handleChange={this.handleChange}
              formData={formData}
              model={model}
              errors={errors} />
          <FormElement
              type="checkbox"
              attribute="is_superuser"
              label={gettext('Administrator')}
              handleChange={this.handleChange}
              formData={formData}
              model={model}
              errors={errors} />
          <p className="divider" />
          <FormElement
              attribute="twitter"
              label={gettext('Twitter')}
              handleChange={this.handleChange}
              placeholder={gettext('Twitter username')}
              formData={formData}
              model={model}
              errors={errors}
              maxLength="15" />
          <FormElement
              attribute="linkedin"
              label={gettext('LinkedIn')}
              handleChange={this.handleChange}
              placeholder={gettext('LinkedIn profile URL')}
              formData={formData}
              model={model}
              errors={errors} />
          <FormElement
              attribute="website"
              label={gettext('Website')}
              handleChange={this.handleChange}
              placeholder={gettext('Personal website URL')}
              formData={formData}
              model={model}
              errors={errors} />
          <FormElement
              type="textarea"
              attribute="bio"
              label={gettext('Short Bio')}
              handleChange={this.handleChange}
              placeholder={gettext('Personal description')}
              formData={formData}
              model={model}
              errors={errors} />
        </div>
        <p className="buttons">
          <input type="submit" className="btn btn-primary"
                 disabled={!this.state.isDirty}
                 value={gettext('Save')} />
        {this.props.model.id &&
          <a href={model.getProfileUrl()}>{gettext("View user's public profile page")}</a>}
        </p>
      {this.props.handleDelete &&
        <div>
          <p className="divider"></p>
          <p className="buttons">
            <ItemDelete item={model} handleDelete={this.props.handleDelete} />
          </p>
        </div>}
      </form>
    );
  }

});


var ItemDelete = React.createClass({

  /* Lifecycle */

  getInitialState: function () {
    return {
      buttonDisabled: true
    };
  },


  /* Handlers */

  toggleButton: function () {
    this.setState({buttonDisabled: !this.state.buttonDisabled});
  },

  onClick: function (e) {
    e.preventDefault();
    this.props.item.destroy().then(this.props.handleDelete);
  },

  render: function () {
    return (
      <div className="item-delete">
        <input type="checkbox"
               checked={!this.state.buttonDisabled}
               onChange={this.toggleButton} />
        <button className="btn btn-danger"
                disabled={this.state.buttonDisabled}
                onClick={this.onClick}>{gettext('Delete')}</button>
        <span className="helptext">{gettext('Note: deleting the user will make its suggestions and translations become attributed to an anonymous user (nobody).')}</span>
      </div>
    );
  }

});


module.exports = {
  UserForm: UserForm
};
