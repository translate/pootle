var React = require('react/addons');

var FormElement = require('../components/forms').FormElement;
var ModelFormMixin = require('../mixins/forms').ModelFormMixin;


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
              model={model}
              errors={errors} />
        {!model.isMeta() &&
          <div className="no-meta">
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
          </div>}
          <FormElement
              autoFocus={model.isMeta()}
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
        {!model.isMeta() &&
          <div className="no-meta">
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
          </div>}
        </div>
        <p className="buttons">
          <input type="submit" className="btn btn-primary"
                 disabled={!this.state.isDirty}
                 value={gettext('Save')} />
        {model.id &&
          <ul className="user-links">
            <li><a href={model.getProfileUrl()}>{gettext("Public Profile")}</a></li>
            <li><a href={model.getStatsUrl()}>{gettext("Statistics")}</a></li>
            <li><a href={model.getDetailedStatsUrl()}>{gettext("Detailed Statistics")}</a></li>
          </ul>}
        </p>
      {(this.props.handleDelete && !model.isMeta()) &&
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
