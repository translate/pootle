'use strict';

var React = require('react/addons');

var FormElement = require('../components/forms').FormElement;
var ModelFormMixin = require('../mixins/forms').ModelFormMixin;


var LanguageForm = React.createClass({
  mixins: [ModelFormMixin],

  fields: ['code', 'fullname', 'specialchars', 'nplurals', 'pluralequation'],


  /* Handlers */

  handleSuccess: function (model) {
    // Add models at the beginning of the collection. When models exist,
    // we need to move them to the first position, as Backbone doesn't
    // honor the `at: <pos>` option in that scenario and there's
    // no modified time attribute that could be used for sorting.
    this.props.collection.unshift(model, {merge: true});
    this.props.collection.move(model, 0);

    this.props.handleSuccess(model);
  },


  /* Layout */

  render: function () {
    var model = this.getResource();
    var errors = this.state.errors;
    var formData = this.state.formData;

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
            errors={errors}
          />
          <FormElement
            attribute="fullname"
            label={gettext('Full Name')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors}
          />
          <FormElement
            attribute="specialchars"
            label={gettext('Special Characters')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors}
          />
          <FormElement
            type="select"
            clearable={false}
            attribute="nplurals"
            options={model.getFieldChoices('nplurals')}
            label={gettext('Number of Plurals')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors}
          />
          <FormElement
            attribute="pluralequation"
            label={gettext('Plural Equation')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors}
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
            <li><a href={model.getPermissionsUrl()}>{gettext('Permissions')}</a></li>
          </ul>}
        </div>
      {this.props.handleDelete &&
        <div>
          <p className="divider" />
          <div className="buttons">
            <ItemDelete item={model} handleDelete={this.props.handleDelete} />
          </div>
        </div>}
      </form>
    );
  }

});


var UserForm = React.createClass({
  mixins: [ModelFormMixin],

  fields: [
      'username', 'is_active', 'password', 'full_name', 'email',
      'is_superuser', 'twitter', 'linkedin', 'website', 'bio'
  ],


  /* Handlers */

  handleSuccess: function (model) {
    // Add models at the beginning of the collection. When models exist,
    // we need to move them to the first position, as Backbone doesn't
    // honor the `at: <pos>` option in that scenario and there's
    // no modified time attribute that could be used for sorting.
    this.props.collection.unshift(model, {merge: true});
    this.props.collection.move(model, 0);

    this.props.handleSuccess(model);
  },


  /* Layout */

  render: function () {
    var model = this.getResource();
    var errors = this.state.errors;
    var formData = this.state.formData;
    var deleteHelpText = gettext('Note: deleting the user will make its suggestions and translations become attributed to an anonymous user (nobody).');

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
            <li><a href={model.getStatsUrl()}>{gettext("Statistics")}</a></li>
            <li><a href={model.getReportsUrl()}>{gettext("Reports")}</a></li>
          </ul>}
        </div>
      {(this.props.handleDelete && !model.isMeta()) &&
        <div>
          <p className="divider" />
          <div className="buttons">
            <ItemDelete item={model} handleDelete={this.props.handleDelete}
                helpText={deleteHelpText} />
          </div>
        </div>}
      </form>
    );
  }

});


var ItemDelete = React.createClass({

  propTypes: {
    item: React.PropTypes.object.isRequired,
    handleDelete: React.PropTypes.func.isRequired,
    helpText: React.PropTypes.string,
  },

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
      {this.props.helpText &&
        <span className="helptext">{this.props.helpText}</span>}
      </div>
    );
  }

});


module.exports = {
  LanguageForm: LanguageForm,
  UserForm: UserForm,
};
