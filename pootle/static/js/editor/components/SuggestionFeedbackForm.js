/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import _ from 'underscore';

import React from 'react';

import FormElement from 'components/FormElement';


const SuggestionFeedBackForm = React.createClass({

  propTypes: {
    suggId: React.PropTypes.number.isRequired,
    initialSuggestionText: React.PropTypes.string.isRequired,
    localeDir: React.PropTypes.string.isRequired,
    onAcceptSuggestion: React.PropTypes.func.isRequired,
    onRejectSuggestion: React.PropTypes.func.isRequired,
    onChange: React.PropTypes.func.isRequired,
  },

  /* Lifecycle */

  getInitialState() {
    this.initialData = {
      comment: '',
      translation: this.props.initialSuggestionText,
    };

    return {
      formData: this.initialData,
    };
  },

  /* Handlers */

  handleAccept(e) {
    const suggestionChanged = (
      this.state.formData.translation !== this.props.initialSuggestionText
    );
    e.preventDefault();
    this.props.onAcceptSuggestion(
      this.props.suggId,
      {
        requestData: this.state.formData,
        isSuggestionChanged: suggestionChanged,
      }
    );
  },

  handleReject(e) {
    e.preventDefault();
    this.props.onRejectSuggestion(this.props.suggId, { requestData: this.state.formData });
  },

  handleChange(name, value) {
    const newData = _.extend({}, this.state.formData);
    newData[name] = value;
    const isDirty = !_.isEqual(newData, this.initialData);
    this.setState({ isDirty, formData: newData });
    this.props.onChange(isDirty);
  },

  /* Layout */

  render() {
    const { formData } = this.state;

    return (
      <form
        id="suggestion-feedback-form"
      >
        <div className="fields">
          <FormElement
            id="suggestion-editor"
            type="textarea"
            label={gettext('Edit the suggestion before accepting, if necessary')}
            placeholder=""
            name="translation"
            handleChange={this.handleChange}
            value={formData.translation}
            data-action="overwrite"
            dir={this.props.localeDir}
            autoFocus
          />
          <FormElement
            type="textarea"
            label={gettext('Provide optional comment (will be publicly visible)')}
            placeholder=""
            name="comment"
            handleChange={this.handleChange}
            value={formData.comment}
          />
        </div>
        <p className="buttons">
          <button
            className="btn btn-success"
            onClick={this.handleAccept}
          ><i className="icon-accept-white"></i>{gettext('Accept')}</button>
          <button
            className="btn btn-danger"
            onClick={this.handleReject}
          ><i className="icon-reject-white"></i>{gettext('Reject')}</button>
        </p>
        <div className="clear" />
      </form>
    );
  },

});


export default SuggestionFeedBackForm;
