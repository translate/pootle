/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React, { PropTypes } from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';

import Avatar from 'components/Avatar';
import TimeSince from 'components/TimeSince';
import { t } from 'utils/i18n';

const Check = ({ name, displayName }) => (
  <a href={`#${name}`}>{displayName}</a>
);
Check.propTypes = {
  name: PropTypes.string.isRequired,
  displayName: PropTypes.string.isRequired,
};

const SourceString = ({ sourceText, url }) => (
  <i><a href={url}>{sourceText}</a></i>
);
SourceString.propTypes = {
  sourceText: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
};

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

    const sourceString = (
      <SourceString
        url={unitUrl}
        sourceText={unitSource}
      />
    );

    let check;
    if (checkName !== undefined && checkDisplayName !== undefined) {
      check = (
        <Check
          name={checkName}
          displayName={checkDisplayName}
        />
      );
    }

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
      return t('removed translation for %(sourceString)s', { sourceString });
    } else if (type === 3) {
      return t('accepted suggestion for %(sourceString)s', { sourceString });
    } else if (type === 4) {
      return [gettext('uploaded file')];
    } else if (type === 6) {
      return t('muted %(check)s for %(sourceString)s', { check, sourceString });
    } else if (type === 7) {
      return t('unmuted %(check)s for %(sourceString)s', { check, sourceString });
    } else if (type === 8) {
      return t('added suggestion for %(sourceString)s', { sourceString });
    } else if (type === 9) {
      return t('rejected suggestion for %(sourceString)s', { sourceString });
    } else if (type === 1 || type === 5) {
      if (translationActionType === 0) {
        return t('translated %(sourceString)s', { sourceString });
      } else if (translationActionType === 1) {
        return t('edited %(sourceString)s', { sourceString });
      } else if (translationActionType === 2) {
        return t('pre-translated %(sourceString)s', { sourceString });
      } else if (translationActionType === 3) {
        return t('removed translation for %(sourceString)s', { sourceString });
      } else if (translationActionType === 4) {
        return t('reviewed %(sourceString)s', { sourceString });
      } else if (translationActionType === 5) {
        return t('marked as needs work %(sourceString)s', { sourceString });
      }
    }

    return [''];
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
        <span className="action-text">
          {this.getActionText()}
        </span>{' '}
        <TimeSince
          title={this.props.displayDatetime}
          dateTime={this.props.isoDatetime}
        />
      </div>
    );
  },

});


export default UserEvent;
