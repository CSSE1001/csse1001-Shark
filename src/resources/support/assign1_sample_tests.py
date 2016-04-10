#!/usr/bin/env python3

VERSION = "2016s1_1.0.0"

##############################################################################
# DEFAULTS #
CSSE7030 = False
SCRIPT = "assign1"
TEST_DATA = None
TEST_DATA_RAW = '##################### INPUTS ##########################\nMAKE_INITIAL_STATE_4 = 4\nMAKE_INITIAL_STATE_8 = 8\nMAKE_INITIAL_STATE_12 = 12\nMAKE_INITIAL_STATE_1000 = 1000\n\nMAKE_POSITION_STRING_18 = 18\n\nNUM_DIFFS_4 = "TATATATA__"\n\nPOSITION_OF_BLANKS_8_0 = "TATATATA__"\n\nMAKE_MOVE_STATE_0_0 = "TATATATA__"\nMAKE_MOVE_POSITION_0_0 = 1\nMAKE_MOVE_STATE_0_1 = "T__ATATAAT"\nMAKE_MOVE_POSITION_0_1 = 3\nMAKE_MOVE_STATE_0_2 = "TAT__ATAAT"\n\nMAKE_MOVE_STATE_1 = \'TAATTAAT__\'\nMAKE_MOVE_STATE_2 = \'__TAATTAAT\'\nMAKE_MOVE_STATE_3 = \'TAAT__TAAT\'\nMAKE_MOVE_POSITION_0 = 0\nMAKE_MOVE_POSITION_2 = 2\nMAKE_MOVE_POSITION_4 = 4\nMAKE_MOVE_POSITION_6 = 6\nMAKE_MOVE_POSITION_8 = 8\n\nSTATES_0 = """\nTATATATA__\nT__ATATAAT\nTAT__ATAAT\n""".strip().split()\n\n################### Expected Results ###########################\nMAKE_INITIAL_STATE_4_RESULT = \'TATATATA__\'\n\nMAKE_POSITION_STRING_18_RESULT = \'012345678901234567\'\n\nNUM_DIFFS_4_RESULT = 8\n\nPOSITION_OF_BLANKS_8_0_RESULT = 8\n\nSHOW_CURRENT_STATE_0_0 = """0123456789\nT__ATATAAT 7 1\n"""\n\nSHOW_CURRENT_STATE_0_1 = """0123456789\nTAT__ATAAT 7 2\n"""\n\n###################### Tests #####################################\n\ninitial_states = [\n    ("4 supporters", [MAKE_INITIAL_STATE_4], MAKE_INITIAL_STATE_4_RESULT)\n]\n\nposition_strings = [\n    ("18 length", [MAKE_POSITION_STRING_18], MAKE_POSITION_STRING_18_RESULT)\n]\n\ndiffs = [\n    ("4 supporters (initial)", [NUM_DIFFS_4], NUM_DIFFS_4_RESULT)\n]\n\nblank_positions = [\n    ("8/end", [POSITION_OF_BLANKS_8_0], POSITION_OF_BLANKS_8_0_RESULT),\n]\n\nmoves = [\n    ("Spec 1", [MAKE_MOVE_STATE_0_0, MAKE_MOVE_POSITION_0_0], MAKE_MOVE_STATE_0_1),\n    ("Spec 2", [MAKE_MOVE_STATE_0_1, MAKE_MOVE_POSITION_0_1], MAKE_MOVE_STATE_0_2)\n]\n\ncurrent_states = [\n    ("Spec 1", [STATES_0[:2]], None, "", SHOW_CURRENT_STATE_0_0),\n    ("Spec 2", [STATES_0[:3]], None, "", SHOW_CURRENT_STATE_0_1),\n]\n\nINTERACT_SPEC_STDIN = "8\\n1\\n15\\nb\\n6\\nq\\n"\n\nINTERACT_SPEC_STDOUT = """How many supporters from each team? 012345678901234567\nTATATATATATATATA__ 16 0\n? 012345678901234567\nT__ATATATATATATAAT 15 1\n? 012345678901234567\nTAAATATATATATAT__T 14 2\n? 012345678901234567\nT__ATATATATATATAAT 15 1\n? 012345678901234567\nTTAATA__TATATATAAT 13 2\n? """\n\ninteractions = [\n    ("Spec", [], None, INTERACT_SPEC_STDIN, INTERACT_SPEC_STDOUT)\n]'
MAXDIFF = 2500
SHOW_VERSION = True
# END DEFAULTS #
##############################################################################

import argparse
import unittest
from io import StringIO
import sys
import collections
import difflib
import contextlib
import warnings
import traceback

parser = argparse.ArgumentParser()
parser.add_argument("script",
    help="The script you want to run the tests against.",
    nargs="?",
    default=SCRIPT)
parser.add_argument("test_data",
    help="The file containing test data to use.",
    nargs="?",
    default=TEST_DATA)
parser.add_argument("-d", "--diff",
    help="The maximum number of characters in a diff",
    action="store",
    type=int,
    default=MAXDIFF)
parser.add_argument("-m", "--masters",
    help="Whether or not to utilize master's tests.",
    action='store_true',
    default=CSSE7030)
parser.add_argument('unittest_args', nargs='*')

args = parser.parse_args()

if args.test_data:
    data = __import__(args.test_data.rstrip('.py'))
else:
    import imp
    data = imp.new_module('data')
    exec(TEST_DATA_RAW, data.__dict__)

try:
    assign1 = __import__(args.script.rstrip('.py').replace("/","."))
except SyntaxError as e:
    print("/-----------------------------------\\")
    print("| Tests not run due to syntax error |")
    print("\\-----------------------------------/")
    traceback.print_exception(SyntaxError, e, None, file=sys.stdout)
    sys.exit(0)

class CsseTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super(unittest.TextTestResult, self).startTest(test)
        self.runbuffer = StringIO()
        self.runbuffer.write(test.id().split('.')[-1].strip().split('test_', 1)[-1])
        self.runbuffer.write(": {} \n")
        self.stream.flush()
        self._stcount = 0
        self._stpass = 0

    def addSubTest(self, test, subtest, err):
        self._stcount += 1
        super().addSubTest(test,subtest,err)
        if err:
            self.runbuffer.write("  - ")
        else:
            self._stpass += 1
            self.runbuffer.write("  + ")
        self.runbuffer.write(subtest.id().lstrip(test.id()).strip()[1:-1] + "\n")

    def addFailure(self, test, err):
        self.stream.write("\t" + test.id().lstrip("test_"))
        self.stream.writeln("... FAIL")
        super(unittest.TextTestResult, self).addFailure(test, err)

    def addSuccess(self, test):
        super(unittest.TextTestResult, self).addSuccess(test)
        if self.dots:
            self.stream.write('.')
            self.stream.flush()

    def printErrors(self):
        if self.errors or self.failures:
            self.stream.writeln("\n/--------------\\")
            self.stream.writeln("| Failed Tests |")
            self.stream.writeln("\\--------------/")
        if self.dots or self.showAll:
            self.stream.writeln()
        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)

    def printErrorList(self, flavour, errors):
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s: %s" % (flavour,self.getDescription(test)))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % err)

    def stopTest(self, test):
        super().stopTest(test)
        self.runbuffer.seek(0)
        self.stream.writeln(self.runbuffer.read().format("{}/{}".format(self._stpass,self._stcount)))
        del self.runbuffer

    def _exc_info_to_string(self, err, test):
        """Converts a sys.exc_info()-style tuple of values into a string."""
        exctype, value, tb = err
        # Skip test runner traceback levels
        while tb and self._is_relevant_tb_level(tb):
            tb = tb.tb_next

        if exctype is test.failureException:
            # Skip assert*() traceback levels
            length = self._count_relevant_tb_levels(tb)
            msgLines = traceback.format_exception_only(exctype, value)
        else:
            msgLines = traceback.format_exception(exctype, value, tb)

        if self.buffer:
            output = sys.stdout.getvalue()
            error = sys.stderr.getvalue()
            if output:
                if not output.endswith('\n'):
                    output += '\n'
                msgLines.append(STDOUT_LINE % output)
            if error:
                if not error.endswith('\n'):
                    error += '\n'
                msgLines.append(STDERR_LINE % error)
        return ''.join(msgLines)


class Csse1001TestCase(unittest.TestCase):
    def id(self):
        return super().id().split('.')[-1].strip()

    class CsseSubtest(unittest.case._SubTest):
        def id(self):
            return super(Csse1001TestCase.CsseSubtest, self).id().split('test_')[-1].strip()

    maxDiff = args.diff
    def __str__(self):
        return "Test "+self._testMethodName[5:]

    @contextlib.contextmanager
    def subTest(self, msg=None, **params):
        """Return a context manager that will return the enclosed block
        of code in a subtest identified by the optional message and
        keyword parameters.  A failure in the subtest marks the test
        case as failed but resumes execution at the end of the enclosed
        block, allowing further test code to be executed.
        """
        if not self._outcome.result_supports_subtests:
            yield
            return
        parent = self._subtest
        if parent is None:
            params_map = collections.ChainMap(params)
        else:
            params_map = parent.params.new_child(params)
        self._subtest = Csse1001TestCase.CsseSubtest(self, msg, params_map)
        try:
            with self._outcome.testPartExecutor(self._subtest, isTest=True):
                yield
            if not self._outcome.success:
                result = self._outcome.result
                if result is not None and result.failfast:
                    raise unittest.case._ShouldStop
            elif self._outcome.expectedFailure:
                # If the test is expecting a failure, we really want to
                # stop now and register the expected failure.
                raise unittest.case._ShouldStop
        finally:
            self._subtest = parent
            
    def assertMultiLineEqual(self, first, second, msg=None):
        """Assert that two multi-line strings are equal."""
        self.assertIsInstance(first, str, 'First argument is not a string')
        self.assertIsInstance(second, str, 'Second argument is not a string')

        if first != second:
          # don't use difflib if the strings are too long
          if (len(first) > self._diffThreshold or
              len(second) > self._diffThreshold):
              self._baseAssertEqual(first, second, msg)
          firstlines = first.splitlines(keepends=True)
          secondlines = second.splitlines(keepends=True)
          if len(firstlines) == 1 and first.strip('\r\n') == first:
              firstlines = [first + '\n']
              secondlines = [second + '\n']
          _common_shorten_repr = unittest.util._common_shorten_repr
          standardMsg = '%s != %s' % _common_shorten_repr(first, second)
          diff = '\n' + '\n'.join(difflib.ndiff(firstlines, secondlines))
          diff = "\n".join([x for x in diff.split('\n') if x.strip()])
          standardMsg = self._truncateMessage(standardMsg, "\n" + diff)
          self.fail(self._formatMessage(msg, standardMsg))


def addGetTestCases(fnname,dataname, f=lambda x: x):
    def fn(self):
        for i, args, res in eval("data.{}".format(dataname)):
            with self.subTest(i):
                fail = 0
                try:
                    fn = eval("assign1." + fnname)
                except AttributeError:
                    fail = 1

                    # attempt to guess function
                    guesses = function_best_guess(fnname)
                    if len(guesses) > 0:
                        fn = getattr(assign1, guesses[0])
                        fail = 0

                if fail:
                    self.fail("No function named '" +fnname +"'")

                self.assertEqual(f(fn(*args)),f(res))
    setattr(Csse1001TestCase, "test_{}".format(fnname),fn)


def addIOTestCases(fnname, dataname, fout = lambda x: x, fret = lambda x: x, exit_allowed = True, strict_return = True):
    d = eval("data.{}".format(dataname))
    def fn(self):
        self._in = sys.stdin
        self._out = sys.stdout
        for i, args, res, stdin, stdout in d:
            sys.stdin = StringIO()
            sys.stdout = StringIO()

            with self.subTest(i):
                fail = 0
                try:
                    fn = eval("assign1." + fnname)
                except AttributeError:
                    fail = 1
                if fail:
                    self.fail("No function named '" +fnname +"'")



                sys.stdin.write(stdin)
                sys.stdin.seek(0)

                # ignore quit/exit
                exited = False
                try:
                    real_res = fret(fn(*args))
                    if strict_return:
                        self.assertEqual(real_res,fret(res))
                except SystemExit as e:
                    exited = True
                    if not exit_allowed:
                        raise e

                sys.stdout.seek(0)
                self.assertEqual(fout(sys.stdout.read()), fout(stdout))
        sys.stdin = self._in
        sys.stdout = self._out

    setattr(Csse1001TestCase, "test_{}".format(fnname),fn)

def addDocstringTests(data, label_formatter=lambda i, name: name):
    def fn(self):
        for i, fnname in enumerate(data):
            with self.subTest(label_formatter(i, fnname)):
                fail = 0
                try:
                    fn = eval("assign1." + fnname)
                except AttributeError:
                    fail = 1

                    # attempt to guess function
                    guesses = function_best_guess(fnname)
                    if len(guesses) > 0:
                        fn = getattr(assign1, guesses[0])
                        fail = 0
                if fail:
                    self.fail("No function named '" +fnname +"'")
                self.assertTrue(fn.__doc__ is not None and fn.__doc__.strip(),
                                     "Function "+fnname+" should have a docstring")
    setattr(Csse1001TestCase, "test_docstrings",fn)

def addNoExitTest():
    fnname = "interact"
    name = "Graceful Quit"
    args = []

    oldfn = getattr(Csse1001TestCase, "test_interact")

    def fn(self):
        oldfn(self)

        self._in = sys.stdin
        self._out = sys.stdout

        sys.stdin = StringIO()
        sys.stdout = StringIO()

        with self.subTest("10.  " + name):
            fail = 0
            try:
                fn = eval("assign1." + fnname)
            except AttributeError:
                fail = 1
            if fail:
                self.fail("No function named '" +fnname +"'")

            sys.stdin.write("8\nq\n")
            sys.stdin.seek(0)

            # ignore quit/exit
            exited = False
            try:
                fn(*args)
            except SystemExit as e:
                exited = True
                self.fail("exit()/quit() should not be called (use break/return instead)")
            except Exception as e:
                pass

            sys.stdin = self._in
            sys.stdout = self._out

    setattr(Csse1001TestCase, "test_interact", fn)

def fix_floats(data):
    return [(x,) +tuple(map(lambda x:float(round(x,10)),y)) for x,*y in data]

import re
def duplicate_whitespace_strip(string):
    #string = string.strip()

    # ensure space after prompt
    string = re.sub(r'[?]([^ ])', '? \\1', string)
    string = re.sub(r'[?]', '? ', string)

    # remove excessive spaces
    string = re.sub(r'[ ]{2,}', ' ', string)
    return string

addGetTestCases("make_initial_state","initial_states")
addGetTestCases("make_position_string","position_strings")
addGetTestCases("num_diffs","diffs")
addGetTestCases("position_of_blanks","blank_positions")
addGetTestCases("make_move","moves")

addIOTestCases("show_current_state","current_states", strict_return=False)
addIOTestCases("interact","interactions", duplicate_whitespace_strip)


### any extra masters tests ###
# i.e.
# if args.masters:
#     ...

fns = """
make_initial_state
make_position_string
num_diffs
position_of_blanks
make_move
show_current_state
interact
""".strip().split()

# if args.masters:
#     fns +=["data_comparison", "display_comparison"]


addDocstringTests(fns, label_formatter=lambda i, name: "{i:<4} {name}".format(i=str(i + 1) + ".", name=name))

addNoExitTest()

def function_best_guess(fn):
    return difflib.get_close_matches(fn, dir(assign1))

def addFunctionNameTests(fnnames):
    # Check for correct function names
    def fn(self):
        for i, fnname in enumerate(fnnames):
            with self.subTest('{i:<4} {name}'.format(i=str(i + 1) + '.', name=fnname)):
                if not getattr(assign1, fnname, False):
                    text = "No function named '{}'.".format(fnname)
                    guesses = function_best_guess(fnname)

                    if len(guesses) == 1:
                        text += " Perhaps '{}'".format(guesses[0])
                    elif len(guesses) > 1:
                        guesses = ["'{}'".format(guess) for guess in guesses]
                        guesses[-1] = "or "
                        guesses = ", ".join(guesses)
                        text += " Perhaps {}".format(guesses)
                    self.fail(text)

    setattr(Csse1001TestCase, "test_naming", fn)

addFunctionNameTests(fns)

test_sections = fns + ["docstrings", "naming"]

def methodCmp(a, b):
    global fns
    As = [i for i,x in enumerate(test_sections) if x in a]
    Bs = [i for i,x in enumerate(test_sections) if x in b]
    return As[0] - Bs[0]

def wrap(text, length=80):
    return [text[i:i+length] for i in range(0, len(text), length)]

# exit/quit patching
# real_quit = quit
# real_exit = exit
#
# def fake_exit(*args, **kwargs):
#     raise Warning("exit() should not be used")
#
# def fake_quit(*args, **kwargs):
#     raise Warning("quit() should not be used")
#
#
# sys.__dict__['exit'] = fake_exit
# assign1.__dict__['exit'] = fake_exit
# assign1.__dict__['quit'] = fake_quit



if __name__=="__main__":
    if SHOW_VERSION:
        print("Version {}\n".format(VERSION))

    #print("#" * 79)
    #[print(line) for line in wrap("Note that passing these tests does not necessarily imply that your assignment is complete or correct, but that there are no basic issues.", 79)]
    #print("#" * 79)
    print()

    sys.argv[1:] = args.unittest_args
    runner = unittest.TextTestRunner(verbosity=9, resultclass=CsseTestResult, stream=sys.stdout)
    loader = unittest.defaultTestLoader
    loader.sortTestMethodsUsing=methodCmp
    print("/--------------------\\")
    print("| Summary of Results |")
    print("\\--------------------/")
    unittest.main(testRunner=runner, testLoader=loader)
