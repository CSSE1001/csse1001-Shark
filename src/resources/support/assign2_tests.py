#!/usr/bin/env python3

VERSION = "1.0"

##############################################################################
# DEFAULTS #
CSSE7030 = False
SCRIPT = "assign2"
TEST_DATA = "assign2_testdata"
TEST_DATA_RAW = ''
MAXDIFF=300
SHOW_VERSION = True
# END DEFAULTS #
##############################################################################

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("script",
    help="The script you want to run the tests against.",
    nargs="?",
    default=SCRIPT)
parser.add_argument("-m", "--masters",
    help="Whether or not to utilize master's tests.",
    action='store_true',
    default=CSSE7030)
parser.add_argument("-d", "--diff",
    help="The maximum number of characters in a diff",
    action="store",
    default=MAXDIFF)
parser.add_argument('unittest_args', nargs='*')

args = parser.parse_args()

import unittest
import traceback
import sys

try:
    assign2 = __import__(args.script.rstrip('.py').replace("/","."))
except SyntaxError as e:
    print("/-----------------------------------\\")
    print("| Tests not run due to syntax error |")
    print("\\-----------------------------------/")
    traceback.print_exception(SyntaxError, e, None, file=sys.stdout)
    sys.exit(0)


from io import StringIO
import collections
import warnings
import inspect
import difflib
import tkinter as tk
import contextlib

class CsseTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super(unittest.TextTestResult, self).startTest(test)
        self.runbuffer = StringIO()
        self.runbuffer.write(test.id().split('.')[-1].strip().lstrip('test_'))
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
    def assertImplemented(self, module, name, msg=None):
        if hasattr(module, name):
            fn = getattr(module, name)
        else:
            self.fail(self._formatMessage(msg, "%s is not implemented" % unittest.util.safe_repr(name)))
            return
        lines, line_number = inspect.getsourcelines(fn)
        empty = [x.strip() != "pass" for x in lines[1:] if x.strip()]
        if True not in empty:
            self.fail(self._formatMessage(msg, "%s is not implemented" % unittest.util.safe_repr(name)))


    def id(self):
        return super().id().split('.')[-1].strip()

    class CsseSubtest(unittest.case._SubTest):
        def id(self):
            return super(Csse1001TestCase.CsseSubtest, self).id().split('test_')[-1].strip()

    maxDiff = eval(str(args.diff))
    def __str__(self):
        return "Test "+"_".join(self._testMethodName.split("_")[1:])

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
            diff = '\n' + "\n".join([x for x in diff.split('\n') if x.strip()])
            standardMsg = self._truncateMessage(standardMsg, diff)
            self.fail(self._formatMessage(msg, standardMsg))



class AssignmentTwo(Csse1001TestCase):
    def setUp(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

    def test_No_animals(self):
        self.assertImplemented(assign2, "AnimalData")
        data = assign2.AnimalData()
        with self.subTest("animal names"):
            self.assertImplemented(data, "get_animal_names")
            self.assertEqual([], data.get_animal_names())
        with self.subTest("get_ranges"):
            self.assertImplemented(data, "get_ranges")
            self.assertEqual(
                (None, None, None, None),
                data.get_ranges()
            )
        with self.subTest("no printing or errors"):
            sys.stdout.seek(0)
            self.assertEqual("",sys.stdout.read(), msg="should not print to stdout")
            sys.stderr.seek(0)
            self.assertEqual("",sys.stderr.read(), msg="should not print to stderr")

    def test_One_animal(self):
        self.assertImplemented(assign2, "AnimalData")
        data = assign2.AnimalData()
        with self.subTest("load_data"):
            self.assertImplemented(data, "load_data")
            data.load_data("poodle.csv")
        with self.subTest("get_animal"):
            self.assertImplemented(data, "get_animal")
            self.assertEqual(assign2.AnimalDataSet("poodle.csv"), data.get_animal("poodle"))
        with self.subTest("get_animal_names"):
            self.assertImplemented(data, "get_animal_names")
            self.assertEqual(["poodle"], data.get_animal_names())
        with self.subTest("is_selected"):
            self.assertImplemented(data, "is_selected")
            self.assertTrue(data.is_selected(0))
        with self.subTest("deselect"):
            self.assertImplemented(data, "deselect")
            self.assertImplemented(data, "is_selected", msg="Can't test deselect")
            data.deselect(0)
            self.assertTrue(not data.is_selected(0))
        with self.subTest("select"):
            self.assertImplemented(data, "select")
            self.assertImplemented(data, "is_selected", msg="Can't test select")
            data.select(0)
            self.assertTrue(data.is_selected(0))
        with self.subTest('get_ranges'):
            self.assertImplemented(data, "get_ranges")
            poodle = assign2.AnimalDataSet("poodle.csv")
            ranges = poodle.get_height_range() + poodle.get_weight_range()
            self.assertEqual(ranges, data.get_ranges())
        with self.subTest("deselected ranges"):
            self.assertImplemented(data, "get_ranges")
            data.deselect(0)
            self.assertEqual((None, None, None, None),
                    data.get_ranges()
                )
        with self.subTest("tabbed string"):
            self.assertImplemented(data, "to_tabbed_string")
            files = [("poodle.csv", "Hidden")]
            expected_output = []
            actual_output = []
            for i, (file, visible) in enumerate(files):
                dataset = assign2.AnimalDataSet(file)
                name = dataset.get_name()
                length = len(dataset.get_data_points())
                string = assign2.LABEL_FORMAT.format(name, length, visible)
                expected_output.append(string)
                actual_output.append(data.to_tabbed_string(i))

            returns_none = all(o is None for o in actual_output)

            self.assertFalse(returns_none, msg="should return a string")

            if not returns_none:
                self.assertEqual("\n".join([str(o) for o in actual_output]), "\n".join(expected_output))
        with self.subTest("no printing or errors"):
            sys.stdout.seek(0)
            self.assertEqual("",sys.stdout.read(), msg="should not print to stdout")
            sys.stderr.seek(0)
            self.assertEqual("",sys.stderr.read(), msg="should not print to stderr")

    def test_Two_animals(self):
        self.assertImplemented(assign2, "AnimalData")
        data = assign2.AnimalData()
        poodle = assign2.AnimalDataSet("poodle.csv")
        echidna = assign2.AnimalDataSet("echidna.csv")
        with self.subTest("load_data"):
            self.assertImplemented(data, "load_data")
            data.load_data("poodle.csv")
            data.load_data("echidna.csv")
        with self.subTest("get_animal"):
            self.assertImplemented(data, "get_animal")
            self.assertEqual(poodle, data.get_animal("poodle"))
            self.assertEqual(echidna, data.get_animal("echidna"))
        with self.subTest("get_animal_names"):
            self.assertImplemented(data, "get_animal_names")
            self.assertEqual(["poodle", "echidna"], data.get_animal_names())
        with self.subTest("is_selected"):
            self.assertTrue(data.is_selected(0))
            self.assertTrue(data.is_selected(1))
        with self.subTest("deselect"):
            self.assertImplemented(data, "deselect")
            self.assertImplemented(data, "is_selected", msg="Can't test deselect")
            data.deselect(1)
            self.assertTrue(not data.is_selected(1))
        with self.subTest("select"):
            self.assertImplemented(data, "select")
            self.assertImplemented(data, "is_selected", msg="Can't test select")
            data.select(1)
            self.assertTrue(data.is_selected(1))
        with self.subTest('get_ranges'):
            self.assertImplemented(data, "get_ranges")
            self.assertEqual((22.9, 38.6, 1.49, 12.483),
                data.get_ranges())
            data.deselect(0)
            ranges = echidna.get_height_range() + echidna.get_weight_range()
            self.assertEqual(ranges, data.get_ranges())
        with self.subTest("deselected ranges"):
            self.assertImplemented(data, "get_ranges")
            data.deselect(1)
            self.assertEqual((None, None, None, None),
                    data.get_ranges()
                )
        with self.subTest("tabbed string"):
            files = [("poodle.csv", "Hidden"), ("echidna.csv", "Hidden")]
            expected_output = []
            actual_output = []
            for i, (file, visible) in enumerate(files):
                dataset = assign2.AnimalDataSet(file)
                name = dataset.get_name()
                length = len(dataset.get_data_points())
                string = assign2.LABEL_FORMAT.format(name, length, visible)
                expected_output.append(string)
                actual_output.append(data.to_tabbed_string(i))

            returns_none = all(o is None for o in actual_output)

            self.assertFalse(returns_none, msg="should return a string")

            if not returns_none:
                self.assertEqual("\n".join([str(o) for o in actual_output]), "\n".join(expected_output))
        with self.subTest("no printing or errors"):
            sys.stdout.seek(0)
            self.assertEqual("",sys.stdout.read(), msg="should not print to stdout")
            sys.stderr.seek(0)
            self.assertEqual("",sys.stderr.read(), msg="should not print to stderr")

    def test_Four_animals(self):
        self.assertImplemented(assign2, "AnimalData")
        data = assign2.AnimalData()
        with self.subTest("load_data"):
            self.assertImplemented(data, "load_data")
            data.load_data("poodle.csv")
            data.load_data("echidna.csv")
            data.load_data("slow loris.csv")
            data.load_data("bandicoot.csv")
        with self.subTest("get_animal"):
            self.assertImplemented(data, "get_animal")
            self.assertEqual(assign2.AnimalDataSet("poodle.csv"), data.get_animal("poodle"))
            self.assertEqual(assign2.AnimalDataSet("bandicoot.csv"), data.get_animal("bandicoot"))
        with self.subTest("get_animal_names"):
            self.assertImplemented(data, "get_animal_names")
            names = ["poodle", "echidna", "slow loris", "bandicoot"]
            self.assertEqual(names, data.get_animal_names())
        with self.subTest("is_selected"):
            self.assertImplemented(data, "is_selected")
            for i in range(4):
                self.assertTrue(data.is_selected(i))
        with self.subTest("deselect"):
            self.assertImplemented(data, "deselect")
            self.assertImplemented(data, "is_selected", msg="Can't test deselect")
            data.deselect(1)
            data.deselect(3)
            for i in range(4):
                self.assertEqual(i%2 == 0, data.is_selected(i))
        with self.subTest("select"):
            self.assertImplemented(data, "select")
            self.assertImplemented(data, "is_selected", msg="Can't test select")
            data.select(1)
            data.select(3)
            for i in range(4):
                self.assertTrue(data.is_selected(i))
        with self.subTest("get_ranges"):
            self.assertImplemented(data, "get_ranges")
            self.assertEqual((11.1, 71.9, 0.514, 12.483),
                data.get_ranges())
        with self.subTest("tabbed string"):
            self.assertImplemented(data, "to_tabbed_string")
            files = [("poodle.csv", "Visible"), ("echidna.csv", "Visible"), ("slow loris.csv", "Visible"), ("bandicoot.csv", "Visible")]
            expected_output = []
            actual_output = []
            for i, (file, visible) in enumerate(files):
                dataset = assign2.AnimalDataSet(file)
                name = dataset.get_name()
                length = len(dataset.get_data_points())
                string = assign2.LABEL_FORMAT.format(name, length, visible)
                expected_output.append(string)
                actual_output.append(data.to_tabbed_string(i))

            returns_none = all(o is None for o in actual_output)

            self.assertFalse(returns_none, msg="should return a string")

            if not returns_none:
                self.assertEqual("\n".join([str(o) for o in actual_output]), "\n".join(expected_output))
        with self.subTest("no printing or errors"):
            sys.stdout.seek(0)
            self.assertEqual("",sys.stdout.read(), msg="should not print to stdout")
            sys.stderr.seek(0)
            self.assertEqual("",sys.stderr.read(), msg="should not print to stderr")


    def test_Docstrings(self):
        fns = [
            "load_data",
            "select",
            "deselect",
            "get_animal_names",
            "get_animal",
            "is_selected",
            "get_ranges",
            "to_tabbed_string"
        ]
        for fnname in fns:
            with self.subTest(fnname):
                fail = 0
                try:
                    fn = eval("assign2.AnimalData." + fnname)
                except AttributeError:
                    fail = 1
                if fail:
                    self.fail("No AnimalData function named '" +fnname +"'")
                self.assertTrue(fn.__doc__,
                                     "Function "+fnname+" should have a docstring")
    def test_Inheritance(self):
        clss = [
            ("Plotter", tk.Canvas),
            ("SelectionBox", tk.Listbox),
            ("AnimalDataPlotApp", object)
        ]
        if args.masters:
            clss += [("SummaryWindow", tk.Toplevel)]
        for name, expected in clss:
            with self.subTest(name + " implemented"):
                self.assertImplemented(assign2, name)
            with self.subTest(name +" inheritance"):
                self.assertImplemented(assign2, name)
                cls = getattr(assign2, name)
                self.assertEqual(expected, cls.__base__)

    def tearDown(self):
        sys.stdout = self._stdout
        sys.stderr = self._stderr

def methodCmp(a, b):
    fns = ['test_No_animals', 'test_One_animal', 'test_Two_animals', 'test_Four_animals', 'test_Inheritance', 'test_Docstrings']
    As = [i for i,x in enumerate(fns) if x in a]
    Bs = [i for i,x in enumerate(fns) if x in b]
    return As[0] - Bs[0]

if __name__=="__main__":
    if SHOW_VERSION:
        print("Version {}\n".format(VERSION))

    sys.argv[1:] = args.unittest_args
    runner = unittest.TextTestRunner(verbosity=9, resultclass=CsseTestResult, stream=sys.stdout)
    loader = unittest.defaultTestLoader
    loader.sortTestMethodsUsing=methodCmp
    print("/--------------------\\")
    print("| Summary of Results |")
    print("\\--------------------/")
    unittest.main(testRunner=runner, testLoader=loader)
