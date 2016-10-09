/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';

import AuthContent from './AuthContent';


const AccountActivation = React.createClass({

  propTypes: {
    onClose: React.PropTypes.func.isRequired,
    signUpEmail: React.PropTypes.string,
  },

  mixins: [PureRenderMixin],


  /* Layout */

  render() {
    let emailLinkMsg;

    if (this.props.signUpEmail) {
      emailLinkMsg = interpolate(
        gettext(
          'We have sent an email containing the special link to ' +
          '<span>%s</span>. Please check your spam folder if you do not see' +
          ' the email.'
        ),
        [this.props.signUpEmail]
      );
    } else {
      emailLinkMsg = gettext(
        'We have sent an email containing the special link to the address ' +
        'used to register this account. Please check your spam folder if ' +
        'you do not see the email.'
      );
    }

    const activationWarningMsg = gettext('Your account needs activation.');
    const instructionsMsg = gettext(
      'Please follow that link to continue the account creation.'
    );

    return (
      <AuthContent>
        <div className="actions sign-up">
          <p>{activationWarningMsg}</p>
          <p dangerouslySetInnerHTML={{ __html: emailLinkMsg }} />
          <p>{instructionsMsg}</p>
          {this.props.signUpEmail &&
            <div>
              <button
                className="btn btn-primary"
                onClick={this.props.onClose}
              >
                {gettext('Close')}
              </button>
            </div>
          }
        </div>
      </AuthContent>
    );
  },

});


export default AccountActivation;
