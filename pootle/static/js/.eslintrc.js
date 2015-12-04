module.exports = {
  env: {
    browser: true,
    es6: true,
  },
  ecmaFeatures: {
    jsx: true,
    modules: true,
  },
  globals: {
    gettext: false,
    ngettext: false,
    interpolate: false,
    l: false,
    PTL: false,
  },
  plugins: [
    'react',
  ],
  rules: {
    'comma-dangle': [2, 'always-multiline'],
    'comma-spacing': [2, {'before': false, 'after': true}],
    'one-var': [2, 'never'],
    'quotes': [2, 'single', 'avoid-escape'],
    'strict': [2, 'never'],
  },
};
