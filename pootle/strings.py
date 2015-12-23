# These are additional strings that we need for a fully localised Pootle. They
# come from Django and other dependencies and are not included in our POT file
# otherwise. This file itself is not used for a running Pootle.

# Rationale:
# Pootle sometimes needs one or two strings from an upstream project.  We don't
# want to waste our localisers time translating the whole upstream project when
# we need only a few strings. In addition having them here makes it easy for
# the translator to easily correct linguistic issues.

# Notes:
# 1. Don't change any of these strings unless they changed in Django or the
#    applicable Django app.
# 2. The adding of extra comments to help translators is fine.
# 3. If we ever rely on large parts of text from an upstream app, rather
#    consider having translators work on the upstream translations.

# Fake imports
from django.utils.translation import ugettext as _


#########
# Django
#########

#######
# Apps
#######

###############
# Static pages
###############

# Commonly used terms to refer to Terms of Services, Privacy Policies, etc.
# We're anticipating possible link text for these pages so that the UI will
# remain 100% translated.

# Translators: Label that refers to the site's privacy policy
_("Privacy Policy")
# Translators: Label that refers to the site's legal requirements
_("Legal")
# Translators: Label that refers to the site's license requirements
_("License")
# Translators: Label that refers to the site's license requirements
_("Contributor License")
# Translators: Label that refers to the site's terms of use
_("Terms of Use")
# Translators: Label that refers to the site's terms of service
_("Terms of Service")
