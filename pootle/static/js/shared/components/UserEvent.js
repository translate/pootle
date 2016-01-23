/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React, { PropTypes } from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';
import _ from 'underscore';

import Avatar from 'components/Avatar';
import TimeSince from 'components/TimeSince';


const UserEvent = React.createClass({

  propTypes: {
    displayDatetime: PropTypes.string.isRequired,
    displayName: PropTypes.string.isRequired,
    email: PropTypes.string.isRequired,
    isoDatetime: PropTypes.string.isRequired,
    type: PropTypes.number.isRequired,
    unitSource: PropTypes.string.isRequired,
    unitUrl: PropTypes.string.isRequired,

    checkName: PropTypes.string,
    checkDisplayName: PropTypes.string,
    translationActionType: PropTypes.number,
    username: PropTypes.string,
  },

  mixins: [PureRenderMixin],

  getActionText() {
    const { checkName } = this.props;
    const { checkDisplayName } = this.props;
    const { translationActionType } = this.props;
    const { type } = this.props;
    const { unitSource } = this.props;
    const { unitUrl } = this.props;

    const sourceString = `<i><a href="${unitUrl}">${_.escape(unitSource)}</a></i>`;

    let check;
    if (checkName !== undefined && checkDisplayName !== undefined) {
      check = `<a href="#${checkName}">${checkDisplayName}</a>`;
    }

    let html;

    /*
     * NORMAL = 1  # Interactive web editing
     * REVERT = 2  # Revert action on the web
     * SUGG_ACCEPT = 3  # Accepting a suggestion
     * UPLOAD = 4  # Uploading an offline file
     * SYSTEM = 5  # Batch actions performed offline
     * MUTE_CHECK = 6  # Mute QualityCheck
     * UNMUTE_CHECK = 7  # Unmute QualityCheck
     * SUGG_ADD = 8  # Add new Suggestion
     * SUGG_REJECT = 9  # Reject Suggestion
     *
     * Translation action types:
     * TRANSLATED = 0
     * EDITED = 1
     * PRE_TRANSLATED = 2
     * REMOVED = 3
     * REVIEWED = 4
     * NEEDS_WORK = 5
     */

    if (type === 2) {
      html = gettext(`removed translation for ${sourceString}`);
    } else if (type === 3) {
      html = gettext(`accepted suggestion for ${sourceString}`);
    } else if (type === 4) {
      html = gettext('uploaded file');
    } else if (type === 6) {
      html = gettext(`muted ${check} for ${sourceString}`);
    } else if (type === 7) {
      html = gettext(`unmuted ${check} for ${sourceString}`);
    } else if (type === 8) {
      html = gettext(`added suggestion for ${sourceString}`);
    } else if (type === 9) {
      html = gettext(`rejected suggestion for ${sourceString}`);
    } else if (type === 1 || type === 5) {
      if (translationActionType === 0) {
        html = gettext(`translated ${sourceString}`);
      } else if (translationActionType === 1) {
        html = gettext(`edited ${sourceString}`);
      } else if (translationActionType === 2) {
        html = gettext(`pre-translated ${sourceString}`);
      } else if (translationActionType === 3) {
        html = gettext(`removed translation for ${sourceString}`);
      } else if (translationActionType === 4) {
        html = gettext(`reviewed ${sourceString}`);
      } else if (translationActionType === 5) {
        html = gettext(`marked as needs work ${sourceString}`);
      }
    }

    return {
      __html: html,
    };
  },

  render() {
    return (
      <div className="last-action">
        <Avatar
          email={this.props.email}
          label={this.props.displayName}
          size={20}
          username={this.props.username}
        />{' '}
        <span
          className="action-text"
          dangerouslySetInnerHTML={this.getActionText()}
        />{' '}
        <TimeSince
          title={this.props.displayDatetime}
          dateTime={this.props.isoDatetime}
        />
      </div>
    );
  },

});


export default UserEvent;
