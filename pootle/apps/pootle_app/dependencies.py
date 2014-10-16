# Minimum Translate Toolkit version required for Pootle to run.
TTK_MINIMUM_REQUIRED_VERSION = (1, 12, 0)

# Minimum Django version required for Pootle to run.
DJANGO_MINIMUM_REQUIRED_VERSION = (1, 6, 5)

# Minimum lxml version required for Pootle to run.
LXML_MINIMUM_REQUIRED_VERSION = (2, 3, 6, 0)


def test_translate():
    try:
        from translate.__version__ import ver, sver
        if ver >= TTK_MINIMUM_REQUIRED_VERSION:
            return True, sver
        else:
            return False, sver
    except ImportError:
        return None, None


def test_django():
    from django import VERSION, get_version
    if VERSION >= DJANGO_MINIMUM_REQUIRED_VERSION:
        return True, get_version()
    else:
        return False, get_version()


def test_lxml():
    try:
        from lxml.etree import LXML_VERSION, __version__
        if LXML_VERSION >= LXML_MINIMUM_REQUIRED_VERSION:
            return True, __version__
        else:
            return False, __version__
    except ImportError:
        return None, None


def test_dependencies():
    dependencies = []

    status, version = test_translate()
    if status:
        text = _("Translate Toolkit version %s installed.", version)
        state = "tick"
    else:
        trans_vars = {
            "installed": version,
            "required": ".".join([str(i) for i in
                                  TTK_MINIMUM_REQUIRED_VERSION]),
        }
        text = _("Translate Toolkit version %(installed)s installed. Pootle "
                 "requires at least version %(required)s.", trans_vars)
        state = "error"

    dependencies.append({
        "priority": "required",
        "dependency": "translate",
        "state": state,
        "text": text,
    })

    status, version = test_django()
    if status:
        text = _("Django version %s is installed.", version)
        state = "tick"
    else:
        trans_vars = {
            "installed": version,
            "required": ".".join([str(i) for i in
                                  DJANGO_MINIMUM_REQUIRED_VERSION]),
        }
        text = _("Django version %(installed)s is installed. Pootle requires "
                 "at least version %(required)s.", trans_vars)
        state = "error"

    dependencies.append({
        "priority": "required",
        "dependency": "django",
        "state": state,
        "text": text,
    })

    status, version = test_lxml()
    if status:
        text = _("lxml version %s is installed.", version)
        state = "tick"
    elif version is not None:
        trans_vars = {
            "installed": version,
            "required": ".".join([str(i) for i in
                                  LXML_MINIMUM_REQUIRED_VERSION]),
        }
        text = _("lxml version %(installed)s is installed. Pootle requires at "
                 "least version %(required)s.", trans_vars)
        state = "error"
    else:
        text = _("lxml is not installed. Pootle requires lxml.")
        state = "error"

    dependencies.append({
        "priority": "required",
        "dependency": "lxml",
        "state": state,
        "text": text,
    })

    return dependencies
