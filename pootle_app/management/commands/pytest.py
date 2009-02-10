from django.core.management.base import BaseCommand
from optparse import make_option
import sys
import py.test

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--verbosity', action='store', dest='verbosity', default='1',
            type='choice', choices=['0', '1', '2'],
            help='Verbosity level; 0=minimal output, 1=normal output, 2=all output'),
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('-k', '--keyword', action='store', dest='keyword', default=True,
            help='Tells py.test only to execute tests for function names matching keyword.'),
    )
    help = 'Runs the test suite for the specified applications, or the entire site if no apps are specified.'
    args = '[appname ...]'

    requires_model_validation = False

    def handle(self, *test_labels, **options):
        from django.conf import settings

        args = [settings.ROOT_DIR]

        #verbosity = int(options.get('verbosity', 1))
        #interactive = options.get('interactive', True)
        if 'keyword' in options:
            args.extend(['-k', options['keyword']])

        return py.test.cmdline.main(args)
