#!/usr/bin/env python3

import imp
import sys
sys.modules['test'] = imp.new_module('test')
exec('#!/usr/bin/env python3\n\nVERSION = "1.1.0"\n\n# #############################################################################\n# DEFAULTS #\nDEFAULTS = {\n    "VERSION": VERSION,\n    "CSSE7030": False,\n    "SCRIPT": "assign1",\n    "TEST_DATA": "assign1_testdata",\n    "TEST_DATA_RAW": \'\',\n    "MAXDIFF": 2500,\n    "SHOW_VERSION": True,\n    "REMOVE_TRACEBACK_DUPLICATES": True,\n    "HIDE_TRACEBACK_PATHS": False,\n    "USE_JSON": False,\n}\n# END DEFAULTS #\n# #############################################################################\n\n__CSSE1001TEST = True\nGLOBAL = "__CSSE1001TEST"\nUT_GLOBAL = "__unittest"\n\nimport unittest\nimport sys\nimport difflib\nfrom io import StringIO\nimport contextlib\nfrom collections import OrderedDict\nimport traceback\nimport re\nimport json\nimport argparse\nimport time\nimport os\nimport imp\nfrom enum import Enum, unique\n\n\n@unique\nclass TestOutcome(Enum):\n    SUCCEED = 0\n    FAIL = 1\n    SKIP = 2\n\n\ndef relative_import(module_path, module_name=None):\n    """\n    Imports a module relatively, regardless of whether relevant directories are python modules.\n\n    :param module_path: The path to the module to import.\n    :param module_name: The name of the module. If None, the filename of the module_path is used, sans extension.\n    :return: The module.\n    """\n    if module_name is None:\n        module_name = os.path.basename(module_path).split(\'.\')[0]\n\n    with open(module_path, "r") as fd:\n        sys.modules[module_name] = module = imp.new_module(module_name)\n        exec(fd.read(), sys.modules[module_name].__dict__)\n\n    return module\n\n\ndef _is_relevant_tb_level(tb, *globals):\n    """\n    Determines if a given traceback occurred in a file with any of the given globals.\n\n    :param tb: The traceback.\n    :param globals: The globals to check.\n    :return: Returns True iff traceback occurred in a file with ANY of the given globals.\n    """\n    for g in globals:\n        if g in tb.tb_frame.f_globals:\n            return True\n\n    return False\n\n\ndef _exc_info_to_string(err, ignored_exceptions=(AssertionError,),\n                        ignored_module_globals=(), suppress_paths=False,\n                        capture_locals=False):\n    """\n    Converts a sys.exc_info()-style tuple of values into a string.\n\n    :param err: sys.exc_info()-style tuple.\n    :param ignored_exceptions: Collection of Exceptions for which to ignore traceback lines.\n    :param ignored_module_globals: Collection of global flags used to ignore tracebacks that occur in files with any of\n        the given globals.\n    :param suppress_paths: Remove file paths from traceback, leaving only the filename.\n    :param capture_locals: If True, Local variables at the source of the error are included in the output.\n    :return: Formatted error string.\n    """\n    """"""\n    exctype, value, tb = err\n\n    # Skip test runner traceback levels\n    while tb and _is_relevant_tb_level(tb, *ignored_module_globals):\n        tb = tb.tb_next\n\n    # if exctype is test.failureException:\n    # # Skip assert*() traceback levels\n    # length = self._count_relevant_tb_levels(tb)\n    # else:\n    # length = None\n\n    length = None\n\n    tb_e = traceback.TracebackException(\n        exctype, value, tb, limit=length, capture_locals=capture_locals)\n    msgLines = list(tb_e.format())\n\n    if suppress_paths:\n        for i, line in enumerate(msgLines):\n            msgLines[i] = re.sub(r\'File ".*[\\\\/]([^\\\\/]+.py)"\', r\'File "\\1"\',\n                                 line)\n\n    # from unittest.TestResult, but not needed at present\n    # commented due to unresolved reference to STDOUT/STDERR_LINE\n    # if self.buffer:\n    # output = sys.stdout.getvalue()\n    # error = sys.stderr.getvalue()\n    # if output:\n    # if not output.endswith(\'\\n\'):\n    # output += \'\\n\'\n    # msgLines.append(STDOUT_LINE % output)\n    # if error:\n    # if not error.endswith(\'\\n\'):\n    #             error += \'\\n\'\n    #         msgLines.append(STDERR_LINE % error)\n    return \'\'.join(msgLines)\n\n\nclass CsseTestResult(unittest.TestResult):\n    _tb_no_duplicates = True\n    _tb_hide_paths = True\n    _tb_locals = False\n\n    def __init__(self, *args, **kwargs):\n        super().__init__(*args, **kwargs)\n        self._results = OrderedDict()\n        self._test_cases = {}\n        self._skips = []\n\n    def get_test_case_name(self, test):\n        if isinstance(test, OrderedTestCase):\n            return test.get_name()\n\n        return test.__class__.__name__\n\n    @staticmethod\n    def get_test_name(test):\n        return test.id().split(\'.\')[-1].strip().split(\'test_\', 1)[-1]\n\n    def startTest(self, test):\n        name = self.get_test_case_name(test)\n        if name not in self._results:\n            self._results[name] = {\n                "name": name,\n                "total": 0,\n                "passed": 0,\n                "failed": 0,\n                "skipped": 0,\n                "tests": OrderedDict()\n            }\n\n        test_name = self.get_test_name(test)\n        self._results[name][\'tests\'][test_name] = {}\n\n        super().startTest(test)\n\n    def add_outcome(self, test, outcome, message=None):\n        test_case_name = self.get_test_case_name(test)\n        test_name = self.get_test_name(test)\n\n        res = self._results[test_case_name]\n        res[outcome] += 1\n        res[\'total\'] += 1\n\n        res[\'tests\'][test_name] = {\n            "outcome": outcome,\n            # "subTests": OrderedDict()\n        }\n\n        if message:\n            res[\'tests\'][test_name][\'message\'] = message\n\n            # print("{}.{} {}".format(test_case_name, test_name, outcome))\n\n    def addError(self, test, err):\n        type, value, traceback = err\n\n        formatted_err = _exc_info_to_string(err, ignored_module_globals=(\n        GLOBAL, UT_GLOBAL),\n                                            suppress_paths=self._tb_hide_paths,\n                                            capture_locals=self._tb_locals)\n\n        self.add_outcome(test, \'failed\', formatted_err)\n\n        self.errors.append((test, formatted_err))\n        self._mirrorOutput = True\n\n    def addFailure(self, test, err):\n        type, value, traceback = err\n\n        self.add_outcome(test, \'failed\', str(value))\n\n        self.failures.append((test, str(value)))\n        self._mirrorOutput = True\n\n    def addSuccess(self, test):\n        self.add_outcome(test, \'passed\')\n        super().addSuccess(test)\n\n    # def addSubTest(self, test, subtest, err):\n    # print("Adding {} {} {}".format(test.id(), subtest.id(), err))\n\n    def addSkip(self, test, reason):\n        self.add_outcome(test, \'skipped\', reason)\n\n        self._skips.append((test, reason))\n        self._mirrorOutput = True\n\n        super().addSkip(test, reason)\n\n    def getDescription(self, test, include_case=True):\n        key = test.id().split(\'test_\')[-1].strip()\n\n        i = int(key) + 1\n        name = test.get_test(key)\n\n        case = test.get_name()\n        order = test.get_order()\n        # i = order.index("test_" + name) + 1\n\n        width = len(str(len(order) + 1))\n\n        if not include_case:\n            case = ""\n\n        prefix = "{} {}.{} ".format(case, i, (width - len(str(i))) * " ")\n\n        return concatenate_and_indent(prefix, name)\n\n\nclass CssePrintTestResult(CsseTestResult, unittest.TextTestResult):\n    outcome_symbols = {\n        \'failed\': \'-\',\n        \'passed\': \'+\',\n        \'skipped\': \'?\'\n    }\n\n    def startTest(self, test):\n        name = self.get_test_case_name(test)\n        if name not in self._results:\n            print("-" * 80)\n            print(name)\n            print("-" * 80)\n\n        super().startTest(test)\n\n    def add_outcome(self, test, outcome, message=None):\n        super().add_outcome(test, outcome, message)\n\n        symbol = self.outcome_symbols[outcome]\n        test_case_name = self.get_test_name(test).split(\'test_\', 1)[-1].strip()\n        desc = self.getDescription(test, False)\n        prefix = "{:<4}{} ".format("", symbol)\n        print(concatenate_and_indent(prefix, desc))\n\n    def printErrors(self):\n        if self.errors or self.failures:\n            print(\'-\' * 80)\n            print_block("Failed Tests")\n\n        if len(self.errors) and self._tb_no_duplicates:\n            # remove duplicates\n            test, err = self.errors[-1]\n\n            # iterate over indices [n-1, ..., 0]\n            for i in range(len(self.errors) - 2, -1, -1):\n\n                last_test, last_err = self.errors[i]\n                if err == last_err:\n                    self.errors[i + 1] = test, "AS ABOVE"\n\n                test, err = last_test, last_err\n\n        self.printErrorList(\'ERROR\', self.errors)\n        self.printErrorList(\'FAIL\', self.failures)\n        # self.printErrorList(\'SKIP\', self._skips)\n\n    def printErrorList(self, flavour, errors):\n        TAB = " " * 4\n        for test, err in errors:\n            print("=" * 80)\n            print(concatenate_and_indent("{}: ".format(flavour),\n                                         self.getDescription(test)))\n            print("-" * 80)\n\n            print(concatenate_and_indent(TAB, str(err).strip()))\n            print("")\n\n\n# class CsseTextTestResult(unittest.TextTestResult):\n# def __init__(self, *args, **kwargs):\n# super().__init__(*args, **kwargs)\n# self._results = OrderedDict()\n#\n# def get_test_case_name(self, test):\n# if isinstance(test, OrderedTestCase):\n#             return test.get_name()\n#\n#         return test.__class__.__name__\n#\n#     def startTest(self, test):\n#         name = self.get_test_case_name(test)\n#         if name not in self._results:\n#             self._results[name] = {\n#                 "total": 0,\n#                 "passed": 0,\n#                 "failed": 0,\n#                 "skipped": 0,\n#                 "tests": OrderedDict()\n#             }\n#\n#         super().startTest(test)\n#         self.runbuffer = StringIO()\n#         self.runbuffer.write(test.id().split(\'.\')[-1].strip().split(\'test_\', 1)[-1])\n#         self.runbuffer.write(": {} \\n")\n#         self.stream.flush()\n#         self._stcount = 0\n#         self._stpass = 0\n#\n#     def addSubTest(self, test, subtest, err):\n#         self._stcount += 1\n#         super().addSubTest(test, subtest, err)\n#         if err:\n#             self.runbuffer.write("  - ")\n#         else:\n#             self._stpass += 1\n#             self.runbuffer.write("  + ")\n#         self.runbuffer.write(subtest.id().lstrip(test.id()).strip()[1:-1] + "\\n")\n#\n#     def addFailure(self, test, err):\n#         self.stream.write("\\t" + test.id().lstrip("test_"))\n#         self.stream.writeln("... FAIL")\n#         super().addFailure(test, err)\n#\n#     def addSuccess(self, test):\n#         super().addSuccess(test)\n#         if self.dots:\n#             self.stream.write(\'.\')\n#             self.stream.flush()\n#\n#     def printErrors(self):\n#         if self.errors or self.failures:\n#             self.stream.writeln("\\n/--------------\\\\")\n#             self.stream.writeln("| Failed Tests |")\n#             self.stream.writeln("\\\\--------------/")\n#         if self.dots or self.showAll:\n#             self.stream.writeln()\n#         self.printErrorList(\'ERROR\', self.errors)\n#         self.printErrorList(\'FAIL\', self.failures)\n#\n#     def printErrorList(self, flavour, errors):\n#         for test, err in errors:\n#             self.stream.writeln(self.separator1)\n#             self.stream.writeln("%s: %s" % (flavour, self.getDescription(test)))\n#             self.stream.writeln(self.separator2)\n#             self.stream.writeln("%s" % err)\n#\n#     def stopTest(self, test):\n#         super().stopTest(test)\n#         self.runbuffer.seek(0)\n#         self.stream.writeln(self.runbuffer.read().format("{}/{}".format(self._stpass, self._stcount)))\n#         del self.runbuffer\n\ndef concatenate_and_indent(prefix, suffix, offset=0, char=" "):\n    """\n    Concatenates two strings, indenting each line of the suffix to line up with the first.\n\n    :param prefix: The prefix (should be single line only).\n    :param suffix: The suffix (can be multiple lines).\n    :param offset: The amount to increase the indent. Defaults to 0.\n    :param char: The character to use to indent. Defaults to <space>.\n    :return:\n    """\n    return prefix + suffix.replace("\\n", "\\n" + (len(prefix) + offset) * char)\n\n\ndef print_block(text, width=80):\n    print("/" + (width - 2) * \'-\' + "\\\\")\n\n    for i in range(0, len(text), width - 4):\n        line = text[i:i + width - 4]\n\n        space = (width - 4) - len(line)\n\n        if space:\n            line = int(space / 2 + .5) * \' \' + line + int(space / 2) * \' \'\n\n        print(\'| \' + line + \' |\')\n\n    print("\\\\" + (width - 2) * \'-\' + "/")\n\n\ndef attribute_best_guess(object, attribute, guesses=3):\n    """\n    Attempts to guess the most likely attribute belonging to object that matches the given attribute.\n\n    :param object: The object to search.\n    :param attribute: The attribute to search for.\n    :param guesses: The number of guesses to make. Defaults to 3.\n\n    :return: A pair of (has_attribute, possible_matches):\n        has_attribute is True iff object has attribute.\n        possible_matches is a list of potential matches, ordered by likelihood, whose length is <= guesses.\n    """\n\n    if getattr(object, attribute, None):\n        return True, [attribute]\n\n    return False, difflib.get_close_matches(attribute, dir(object), n=guesses)\n\n\ndef end_test(test_case, reason, outcome):\n    """\n    Ends a test by performing the given action.\n\n    :param test_case: The unittest.TestCase to act upon.\n    :param reason: The reason for ending the test.\n    :param outcome: The outcome of the test (i.e. TestOutcome).\n    """\n    if outcome == TestOutcome.FAIL:\n        test_case.fail(reason)\n    elif outcome == TestOutcome.SKIP:\n        test_case.skipTest(reason)\n\n\n@contextlib.contextmanager\ndef hijack_stdio():\n    save_stdout = sys.stdout\n    save_stderr = sys.stderr\n    save_stdin = sys.stdin\n\n    try:\n        sys.stdout = StringIO()\n        sys.stderr = StringIO()\n        sys.stdin = StringIO()\n        yield sys.stdout, sys.stderr, sys.stdin\n    finally:\n        sys.stdout = save_stdout\n        sys.stderr = save_stderr\n        sys.stdin = save_stdin\n\n\n@contextlib.contextmanager\ndef hijack_stdout():\n    save_stdout = sys.stdout\n\n    try:\n        sys.stdout = StringIO()\n        yield sys.stdout\n    finally:\n        sys.stdout = save_stdout\n\n\n@contextlib.contextmanager\ndef hijack_stderr():\n    save_stderr = sys.stderr\n\n    try:\n        sys.stderr = StringIO()\n        yield sys.stderr\n    finally:\n        sys.stderr = save_stderr\n\n\n@contextlib.contextmanager\ndef hijack_stdin():\n    save_stdin = sys.stdin\n\n    try:\n        sys.stdin = StringIO()\n        yield sys.stdin\n    finally:\n        sys.stdin = save_stdin\n\n\nclass TestGenerator(object):\n    class NoReturnValue(object):\n        pass\n\n    @staticmethod\n    def function_naming_test(module, function):\n        """\n        Returns a function that tests whether a module has function.\n\n        :param module: The module that contains function.\n        :param function: The function to check for.\n        """\n\n        def fn(self):\n            match, guesses = attribute_best_guess(module, function)\n\n            if not match:\n                if not len(guesses):\n                    self.fail("No function named {!r}".format(function))\n                guesses = ", ".join([repr(g) for g in guesses])\n                text = "No function named {!r}. Perhaps: {}".format(function,\n                                                                    guesses)\n\n                self.fail(text)\n\n        return fn\n\n    @staticmethod\n    def class_naming_test(module, klass, methods=[]):\n        """\n        Returns a function that tests whether a module has class, and if that class has all of the given methods.\n\n        :param module: The module that contains function.\n        :param klass: The class to check for.\n        :param methods: A list of methods to check for.\n        """\n\n        def fn(self):\n            match, guesses = attribute_best_guess(module, klass)\n\n            if not match:\n                if not len(guesses):\n                    return self.fail("No class named {!r}".format(klass))\n\n                # todo: should this be a subTest?\n                # with self.subTest(klass):\n                guesses_text = ", ".join([repr(g) for g in guesses])\n                self.fail("No class named {!r}. Perhaps: {}".format(klass,\n                                                                    guesses_text))\n\n                # todo: remove or fix; currently handled by class_method_naming_test\n                # guess = guesses[0]\n                # klass_guess = getattr(module, guess)\n                #\n                # for i, method in enumerate(methods):\n                #     with self.subTest("{}.{}".format(klass, method)):\n                #         match, guesses = attribute_best_guess(klass_guess, method)\n                #\n                #         if not match:\n                #             if not len(guesses):\n                #                 self.fail("No method named {!r} on class {!r}".format(method, guess))\n                #\n                #             # todo: should this be a subTest?\n                #             guesses_text = ", ".join([repr(g) for g in guesses])\n                #             self.fail("No method named {!r} on class {!r}. Perhaps: {}".format(method, guess, guesses_text))\n\n        return fn\n\n    @staticmethod\n    def class_method_naming_test(module, klass, method,\n                                 undefined_outcome=TestOutcome.SKIP):\n        """\n        Returns a function that tests whether a module has class, and if that class has all of the given methods.\n\n        :param module: The module that contains function.\n        :param klass: The class to check for.\n        :param method: The method on klass to check for.\n        :param undefined_outcome: Action to perform (i.e. result of test) if the function is undefined,\n            or if there is no close match.\n        """\n\n        def fn(self):\n            # Get most likely function, if not the function itself\n            match, guesses = attribute_best_guess(module, klass)\n\n            if not match and not len(guesses):\n                return end_test(self,\n                                "No method {!r} for undefined class {!r}.".format(\n                                    method, klass),\n                                undefined_outcome)\n\n            guess = guesses[0]\n            klass_guess = getattr(module, guess)\n\n            match, guesses = attribute_best_guess(klass_guess, method)\n\n            if not match:\n                if not len(guesses):\n                    self.fail(\n                        "No method named {!r} on class {!r}".format(method,\n                                                                    guess))\n\n                guesses_text = ", ".join([repr(g) for g in guesses])\n                self.fail(\n                    "No method named {!r} on class {!r}. Perhaps: {}".format(\n                        method, guess, guesses_text))\n\n        return fn\n\n    @staticmethod\n    def function_docstring_test(module, function,\n                                undefined_outcome=TestOutcome.FAIL):\n        """\n        Returns a function that tests whether a module\'s function has a docstring.\n\n        :param module: The module that contains function.\n        :param function: The function to check for a docstring.\n        :param undefined_outcome: Action to perform (i.e. result of test) if the function is undefined,\n            or if there is no close match.\n        """\n\n        def fn(self):\n            # Get most likely function, if not the function itself\n            match, guesses = attribute_best_guess(module, function)\n\n            if match:\n                fn = getattr(module, function)\n            elif len(guesses):\n                fn = getattr(module, guesses[0])\n            else:\n                return end_test(self,\n                                "No docstring for undefined function {!r}.".format(\n                                    function), undefined_outcome)\n\n            # Check for a docstring\n            if fn.__doc__ is None or not fn.__doc__.strip():\n                self.fail("No docstring for function {!r}.".format(function))\n\n        return fn\n\n    @staticmethod\n    def class_docstring_test(module, klass, methods=[],\n                             undefined_outcome=TestOutcome.FAIL):\n        """\n        Returns a function that tests, for a given module, whether class and each of the given methods have docstrings.\n\n        :param module: The containing module.\n        :param klass: The class to check for a docstring.\n        :param methods: A list of methods on klass to check for docstrings.\n        :param undefined_outcome: Action to perform (i.e. result of test) if the class or a method is undefined,\n            or if there is no close match.\n        """\n\n        def fn(self):\n            match, guesses = attribute_best_guess(module, klass)\n\n            # handle undefined class\n            if not len(guesses):\n                return end_test(self,\n                                "No docstring for undefined class {!r}".format(\n                                    klass), undefined_outcome)\n\n                # todo: remove or fix; currently handled by class_method_docstring_test\n                # guess = guesses[0]\n                # klass_guess = getattr(module, guess)\n                #\n                # for i, method in enumerate(methods):\n                #     with self.subTest("{}.{}".format(klass, method)):\n                #         match, guesses = attribute_best_guess(klass_guess, method)\n                #\n                #         if match:\n                #             fn = getattr(klass_guess, method)\n                #         elif len(guesses):\n                #             fn = getattr(klass_guess, guesses[0])\n                #         else:\n                #             reason = "No docstring for undefined method {!r} on class {!r}.".format(method, guess)\n                #\n                #             if undefined_outcome == TestOutcome.FAIL:\n                #                 self.fail(reason)\n                #             elif undefined_outcome == TestOutcome.SKIP:\n                #                 self.skipTest(reason)\n                #             continue\n                #\n                #         # Check for a docstring\n                #         if fn.__doc__ is None or not fn.__doc__.strip():\n                #             self.fail("No docstring for method {!r} on class {!r}.".format(method, guess))\n\n        return fn\n\n    @staticmethod\n    def class_method_docstring_test(module, klass, method,\n                                    undefined_outcome=TestOutcome.SKIP):\n        """\n        Returns a function that tests, for a given module, whether class and each of the given methods have docstrings.\n\n        :param module: The containing module.\n        :param klass: The class to check for a docstring.\n        :param method: The method on klass to check for docstrings.\n        :param undefined_outcome: Action to perform (i.e. result of test) if the class or a method is undefined,\n            or if there is no close match.\n        """\n\n        def fn(self):\n            match, guesses = attribute_best_guess(module, klass)\n\n            # handle undefined class\n            if not len(guesses):\n                return end_test(self,\n                                "No docstring for method {!r} on undefined class {!r}".format(\n                                    method, klass),\n                                undefined_outcome)\n\n            guess = guesses[0]\n            klass_guess = getattr(module, guess)\n\n            match, guesses = attribute_best_guess(klass_guess, method)\n\n            # handle undefined method\n            if not len(guesses):\n                return end_test(self,\n                                "No docstring for undefined method {!r} on class {!r}".format(\n                                    method, klass),\n                                undefined_outcome)\n\n            fn = getattr(klass_guess, guesses[0])\n\n            # Check for a docstring\n            if fn.__doc__ is None or not fn.__doc__.strip():\n                self.fail(\n                    "No docstring for method {!r} on class {!r}.".format(method,\n                                                                         guess))\n\n        return fn\n\n    @staticmethod\n    def class_inheritance_test(module, klass_name, parent_name,\n                               undefined_outcome=TestOutcome.FAIL):\n        """\n        Returns a function that tests, for a given module, whether class inherits from parent.\n\n        :param module: The containing module.\n        :param klass_name: The class to check.\n        :param parent_name: The parent class to check for.\n        :param undefined_outcome: Action to perform (i.e. result of test) if the class is undefined,\n            or if there is no close match.\n        """\n\n        def fn(self):\n            # get class from module\n            klass_match, klass_guesses = attribute_best_guess(module,\n                                                              klass_name)\n\n            # handle undefined class\n            if not len(klass_guesses):\n                return end_test(self,\n                                "No parent class for undefined class {!r}.".format(\n                                    klass_name), undefined_outcome)\n\n            klass_guess = klass_guesses[0]\n            klass_guess_obj = getattr(module, klass_guess)\n\n            # get parent from module\n            parent = getattr(module, parent_name, None)\n            # if not found, try builtins\n            if parent is None:\n                parent = getattr(sys.modules[\'__main__\'].__builtins__,\n                                 parent_name, None)\n\n            # handle undefined parent\n            # no parent is strict fail\n            if parent is None:\n                return end_test(self,\n                                "Class {0!r} must inherit from {1!r}, but {1!r} is not defined.".format(\n                                    klass_name,\n                                    parent_name),\n                                TestOutcome.FAIL)\n\n            if not issubclass(klass_guess_obj, parent):\n                parents_text = ", ".join(\n                    [repr(p.__name__) for p in klass_guess_obj.__bases__])\n                self.fail(\n                    "Class {!r} must inherit from {!r}, but instead inherits from {}.".format(\n                        klass_name,\n                        parent_name, parents_text))\n\n        return fn\n\n    @staticmethod\n    def function_comparison_test(module, function, args, result,\n                                 undefined_outcome=TestOutcome.SKIP, **kwargs):\n        """\n        Returns a function that tests, for a given module, whether function returns result.\n\n        :param module: The containing module.\n        :param function: The function to test.\n        :param args: A tuple of arguments to supply to the function.\n        :param result: The expected return value.\n        :param undefined_outcome: Action to perform (i.e. result of test) if the function is undefined,\n            or if there is no close match.\n        """\n\n        # todo: suppress stdout/stderr?\n        def fn(self):\n            # Get most likely function, if not the function itself\n            match, guesses = attribute_best_guess(module, function)\n\n            if match:\n                fn = getattr(module, function)\n            elif len(guesses):\n                fn = getattr(module, guesses[0])\n            else:\n                return end_test(self,\n                                "Undefined function {!r}.".format(function),\n                                undefined_outcome)\n\n            self.assertEqual(fn(*args), result)\n\n        return fn\n\n    @staticmethod\n    def function_io_test(module, function, args, result, stdin="", stdout="",\n                         stderr="",\n                         undefined_outcome=TestOutcome.SKIP, exit_allowed=False,\n                         exit_error=None, **kwargs):\n        """\n        Returns a function that tests, for a given module, whether function returns result, using stdio.\n\n        :param module: The containing module.\n        :param function: The function to test.\n        :param args: A tuple of arguments to supply to the function.\n        :param result: The expected return value. Use TestGenerator.NoReturnValue to ignore return value.\n        :param stdin: The standard input to supply to the function.\n        :param stdout: The expected standard output from the function. Set to None to ignore comparison.\n        :param stderr: The expected standard error from the function. Set to None to ignore comparison.\n        :param undefined_outcome: Action to perform (i.e. result of test) if the function is undefined,\n            or if there is no close match.\n        :param exit_allowed: If True, the function is allowed to end by calling exit()/quit()/etc.\n        :param exit_error: The error text to use if an unallowed SystemExit occurs.\n        """\n\n        ignore_return = isinstance(result, TestGenerator.NoReturnValue)\n\n        # todo: add timeout\n        def fn(self):\n            # Get most likely function, if not the function itself\n            match, guesses = attribute_best_guess(module, function)\n\n            if match:\n                fn = getattr(module, function)\n            elif len(guesses):\n                fn = getattr(module, guesses[0])\n            else:\n                return end_test(self,\n                                "Undefined function {!r}.".format(function),\n                                undefined_outcome)\n\n            with hijack_stdio() as (stdout_stream, stderr_stream, stdin_stream):\n                sys.stdin.write(stdin)\n                sys.stdin.seek(0)\n\n                # ignore quit/exit\n                exited = False\n                try:\n                    real_res = fn(*args)\n                    if not ignore_return:\n                        self.assertEqual(real_res, result)\n                except SystemExit as e:\n                    exited = True\n                    if not exit_allowed:\n                        if exit_error is not None:\n                            return self.fail(exit_error)\n                        else:\n                            raise e\n\n                sys.stdout.seek(0)\n                if stdout is not None:\n                    self.assertEqual(sys.stdout.read(), stdout)\n\n                sys.stderr.seek(0)\n                if stderr is not None:\n                    self.assertEqual(sys.stderr.read(), stderr)\n\n        return fn\n\n\nDIFF_OMITTED = (\'\\nDiff is %s characters long. \'\n                \'Set --diff to see it.\')\n\n\nclass UnorderedTestCase(unittest.TestCase):\n    _name = None\n\n    def _truncateMessage(self, message, diff):\n        max_diff = self.maxDiff\n        if max_diff is None or len(diff) <= max_diff:\n            return message + diff\n        return message + (DIFF_OMITTED % len(diff))\n\n    def get_name(self):\n        if self._name is not None:\n            return self._name\n\n        return self.__class__.__name__.replace(\'TestCase\', \'\')\n\n    def assertMultiLineEqual(self, first, second, msg=None):\n        """Assert that two multi-line strings are equal."""\n        self.assertIsInstance(first, str, \'First argument is not a string\')\n        self.assertIsInstance(second, str, \'Second argument is not a string\')\n\n        if first != second:\n            # don\'t use difflib if the strings are too long\n            if (len(first) > self._diffThreshold or\n                        len(second) > self._diffThreshold):\n                self._baseAssertEqual(first, second, msg)\n            firstlines = first.splitlines(keepends=True)\n            secondlines = second.splitlines(keepends=True)\n            if len(firstlines) == 1 and first.strip(\'\\r\\n\') == first:\n                firstlines = [first + \'\\n\']\n                secondlines = [second + \'\\n\']\n            _common_shorten_repr = unittest.util._common_shorten_repr\n            standardMsg = \'%s != %s\' % _common_shorten_repr(first, second)\n            diff = \'\\n\' + \'\\n\'.join(difflib.ndiff(firstlines, secondlines))\n            diff = "\\n".join([x for x in diff.split(\'\\n\') if x.strip()])\n            standardMsg = self._truncateMessage(standardMsg,\n                                                "\\n" + diff) + "\\n\\n"\n            self.fail(self._formatMessage(msg, standardMsg))\n\n\nclass OrderedTestCase(UnorderedTestCase):\n    _order = None\n    _subTests = None\n\n    def __init__(self, methodName=\'runTest\'):\n        super().__init__(methodName)\n        self._subTests = {}\n\n    @classmethod\n    def ensure_order(cls):\n        if cls._order is None:\n            cls._order = []\n\n            methods = [getattr(cls, method) for method in dir(cls) if\n                       method.startswith("test_")]\n            tests = [(method, method.__doc__) for method in methods]\n\n            cls.add_test_methods(tests)\n\n    @classmethod\n    def add_test(cls, name, fn):\n        cls.ensure_order()\n\n        key = len(cls._order)\n\n        cls._order.append(name)\n\n        setattr(cls, "test_" + str(key), fn)\n\n    @classmethod\n    def add_test_methods(cls, methods):\n        for method, name in methods:\n            if name is None:\n                if method.startswith(\'test_\'):\n                    name = method.split(\'test_\', 1)[-1]\n                else:\n                    name = method\n\n            cls.add_test(name, method)\n\n    @classmethod\n    def get_order(cls):\n        cls.ensure_order()\n\n        return ["test_" + str(i) for i in range(len(cls._order))]\n\n    @classmethod\n    def get_test(cls, key):\n        return cls._order[int(key)]\n\n        # def subTest(self, msg=None, **params):\n        #     test = self.id().split(\'test_\', 1)[-1]\n        #     subtest = msg\n        #\n        #     self._subTests[test] = self._subTests.get(test, [])\n        #     self._subTests[test].append(subtest)\n        #\n        #     super().subTest(msg, **params)\n\n\ndef create_subclass(name, *parents):\n    return type(name, parents, {})\n\n\ndef create_test_case(name):\n    test_case = create_subclass(name + \'TestCase\', OrderedTestCase)\n    set_test_case_name(name, test_case)\n\n    return test_case\n\n\ndef create_naming_test_case(module, functions=(), klasses=()):\n    test_case = create_test_case(\'Naming\')\n\n    for function in functions:\n        test_case.add_test(function,\n                           TestGenerator.function_naming_test(module, function))\n\n    for klass, methods, *_ in klasses:\n        test_case.add_test(klass,\n                           TestGenerator.class_naming_test(module, klass))\n\n        for method in methods:\n            test_case.add_test("    {}.{}".format(klass, method),\n                               TestGenerator.class_method_naming_test(module,\n                                                                      klass,\n                                                                      method))\n\n    return test_case\n\n\ndef create_docstring_test_case(module, functions=(), klasses=(),\n                               undefined_outcome=TestOutcome.SKIP):\n    test_case = create_test_case(\'Docstrings\')\n\n    for function in functions:\n        test_case.add_test(function,\n                           TestGenerator.function_docstring_test(module,\n                                                                 function,\n                                                                 undefined_outcome=undefined_outcome))\n\n    for klass, methods, *_ in klasses:\n        test_case.add_test(klass,\n                           TestGenerator.class_docstring_test(module, klass))\n\n        for method in methods:\n            test_case.add_test("    {}.{}".format(klass, method),\n                               TestGenerator.class_method_docstring_test(module,\n                                                                         klass,\n                                                                         method))\n\n    return test_case\n\n\ndef create_inheritance_test_case(module, klasses=(),\n                                 undefined_outcome=TestOutcome.SKIP):\n    test_case = create_test_case(\'Inheritance\')\n\n    for klass, _, *parents in klasses:\n        for parent in parents:\n            if parent is None:\n                continue\n            test_case.add_test("{} inherits from {}".format(klass, parent),\n                               TestGenerator.class_inheritance_test(module,\n                                                                    klass,\n                                                                    parent,\n                                                                    undefined_outcome=undefined_outcome))\n\n    return test_case\n\n\ndef create_comparison_test_case(module, function, tests,\n                                undefined_outcome=TestOutcome.SKIP):\n    test_case = create_test_case(function)\n\n    for i, test in enumerate(tests):\n        kwargs = {\n            "undefined_outcome": undefined_outcome\n        }\n\n        kwargs.update(test)\n\n        test_case.add_test(kwargs[\'title\'],\n                           TestGenerator.function_comparison_test(module,\n                                                                  function,\n                                                                  **kwargs))\n\n    return test_case\n\n\ndef create_io_test_case(module, function, tests,\n                        undefined_outcome=TestOutcome.SKIP):\n    test_case = create_test_case(function)\n\n    for i, test in enumerate(tests):\n        kwargs = {\n            "undefined_outcome": undefined_outcome\n        }\n\n        kwargs.update(test)\n\n        test_case.add_test(kwargs[\'title\'],\n                           TestGenerator.function_io_test(module, function,\n                                                          **kwargs))\n\n    return test_case\n\n\ndef set_test_case_name(name, *test_cases):\n    for test_case in test_cases:\n        test_case._name = name\n\n\nclass CsseTestLoader(unittest.TestLoader):\n    def __init__(self, test_cases):\n        super().__init__()\n        self._test_cases = test_cases\n\n    def getTestCaseNames(self, testCaseClass):\n        if issubclass(testCaseClass, OrderedTestCase):\n            return testCaseClass.get_order()\n\n        return super().getTestCaseNames(testCaseClass)\n\n    def loadTestsFromModule(self, module, *args, pattern=None, **kwargs):\n        tests = []\n        for test_case in self._test_cases:\n            obj = test_case\n            if isinstance(obj, type) and issubclass(obj, unittest.TestCase):\n                tests.append(self.loadTestsFromTestCase(obj))\n            else:\n                raise TypeError(\n                    "Class {!r} is not a subclass of unittest.TestCase.".format(\n                        test_case))\n\n        return self.suiteClass(tests)\n\n\nclass TestMaster(object):\n    _tests = None\n\n    def __init__(self, config=DEFAULTS):\n        self._meta = {}\n        self._config = config\n\n        # ensure correct version of Python is used\n        if not self.ensure_version():\n            print(\n                "Unsupported Python version {}".format(tuple(sys.version_info)))\n            exit(1)\n\n    def load_module(self, module_path):\n        try:\n            self._module = __import__(\n                module_path.rstrip(\'.py\').replace("/", "."))\n            return None\n        except ImportError as e:\n            err = sys.exc_info()\n\n            result = {\n                "message": "Tests not run due to file not found",\n                # "details": "File {!r} does not exist.".format(module_path),\n                "error": e,\n                "type": "import",\n                "code": 3\n            }\n\n        except SyntaxError as e:\n            err = sys.exc_info()\n\n            result = {\n                "message": "Tests not run due to syntax error",\n                # "details": "Syntax error in {!r}.".format(module_path),\n                "error": e,\n                "type": "syntax",\n                "code": 4\n            }\n\n        except Exception as e:\n            err = sys.exc_info()\n\n            result = {\n                "message": "Tests not run due to arbitrary exception",\n                # "details": "Syntax error in {!r}.".format(module_path),\n                "error": e,\n                "type": "exception",\n                "code": 5\n            }\n\n        text = _exc_info_to_string(err, ignored_module_globals=(GLOBAL,),\n                                   suppress_paths=True)\n        result[\'details\'] = text\n\n        return result\n\n    def set_meta(self, property, value):\n        self._meta[property] = value\n\n    def get_meta(self, property):\n        return self._meta[property]\n\n    def setup_args(self):\n        parser = argparse.ArgumentParser()\n\n        parser.add_argument("script",\n                            help="The script you want to run the tests against.",\n                            nargs="?",\n                            default=self._config["SCRIPT"])\n        parser.add_argument("test_data",\n                            help="The file containing test data to use.",\n                            nargs="?",\n                            default=self._config["TEST_DATA"])\n        parser.add_argument("-d", "--diff",\n                            help="The maximum number of characters in a diff",\n                            action="store",\n                            type=int,\n                            default=self._config["MAXDIFF"])\n        parser.add_argument("-m", "--masters",\n                            help="Whether or not to utilize master\'s tests.",\n                            action=\'store_true\',\n                            default=self._config["CSSE7030"])\n        parser.add_argument("-j", "--json",\n                            help="Whether or not to display output in JSON format.",\n                            action=\'store_true\',\n                            default=self._config["USE_JSON"])\n        parser.add_argument("--tb-hide-paths",\n                            help="Hide paths from traceback output.",\n                            action="store_true",\n                            default=self._config["HIDE_TRACEBACK_PATHS"])\n        parser.add_argument("--tb-no-duplicates",\n                            help="Remove duplicates from test output.",\n                            action="store_true",\n                            default=self._config["REMOVE_TRACEBACK_DUPLICATES"])\n        parser.add_argument(\'unittest_args\', nargs=\'*\', default=[])\n\n        self._args = parser.parse_args()\n        return self._args\n\n    def prepare(self):\n        raise NotImplemented(\n            "Prepare method must be implemented by TestMaster child class.")\n\n    def ensure_version(self):\n        """\n        Returns None if Python version is okay, else error message.\n        """\n        return sys.version_info >= (3, 5, 1)\n\n    def load_test_data(self):\n        if self._args.test_data:\n            data = __import__(self._args.test_data.rstrip(\'.py\'))\n            # data = relative_import(self._args.test_data, "data")\n        else:\n            if self._config["TEST_DATA_RAW"] is None:\n                self._test_data = None\n                return\n            import imp\n\n            data = imp.new_module(\'data\')\n            exec(self._config["TEST_DATA_RAW"], data.__dict__)\n\n        self._test_data = data.get_data(self._args)\n\n    # todo: clean this up and abstract\n    def main(self):\n        output = {\n            "version": self._config["VERSION"]\n        }\n\n        self.setup_args()\n\n        output_json = self._args.json\n\n        try:\n            self.load_test_data()\n        except Exception as e:\n            err = sys.exc_info()\n            text = _exc_info_to_string(err, ignored_module_globals=(GLOBAL,),\n                                       suppress_paths=True)\n\n            if self._args.json:\n                output[\'error\'] = \'test_data\'\n                output[\n                    \'error_message\'] = "Tests couldn\'t be run due to failure to load test data." + \'\\n\' + text\n            else:\n                print_block("Fatal error loading test_data.")\n                print(text)\n            sys.exit(2)\n\n        if not output_json and self._config[\'SHOW_VERSION\']:\n            print("Version: {}".format(output[\'version\']))\n\n        error = self.load_module(self._args.script)\n\n        if error:\n            output[\'error\'] = error[\'type\']\n            output[\'error_message\'] = error[\'message\'] + \'\\n\' + error[\'details\']\n\n            if output_json:\n                print(json.dumps(output, indent=" " * 4))\n            else:\n                print_block(error[\'message\'])\n                print(error[\'details\'])\n\n            return sys.exit(error[\'code\'])\n\n        self.prepare()\n\n        result_class = CsseTestResult if output_json else CssePrintTestResult\n\n        result_class._tb_no_duplicates = self._args.tb_no_duplicates\n        result_class._tb_hide_paths = self._args.tb_hide_paths\n\n        with hijack_stderr():\n            runner = unittest.TextTestRunner(verbosity=9, stream=None,\n                                             resultclass=result_class)\n\n        for test_case in self._tests:\n            setattr(test_case, "maxDiff", self._args.diff or None)\n\n        loader = CsseTestLoader(self._tests)\n        if not output_json:\n            print_block("Summary of Results")\n        start = time.time()\n        program = unittest.main(exit=False, testRunner=runner,\n                                testLoader=loader,\n                                argv=[sys.argv[0]] + self._args.unittest_args)\n        stop = time.time()\n\n        result = program.result\n\n        output[\'total\'] = result.testsRun\n        fails, skips, errors = map(len, (\n        result.failures, result.skipped, result.errors))\n        output[\'failed\'] = fails + errors\n        output[\'skipped\'] = skips\n        output[\'passed\'] = result.testsRun - (fails + errors + skips)\n\n        output[\'time\'] = stop - start\n\n        output[\'results\'] = result._results\n\n        if not output_json:\n            print("-" * 80)\n            print(\n                "Ran {total} tests in {time:.3f} seconds with {passed} passed/{skipped} skipped/{failed} failed.".format(\n                    **output))\n\n        if output_json:\n            print(json.dumps(output, indent=" " * 4))\n\n\n', sys.modules['test'].__dict__)

from test import *

# #############################################################################
# DEFAULT OVERRIDES #
DEFAULTS['VERSION'] = "2016s1a2_1.0.1"
DEFAULTS['CSSE7030'] = False
DEFAULTS['TEST_DATA'] = None
DEFAULTS['TEST_DATA_RAW'] = None
DEFAULTS['SCRIPT'] = 'assign2.py'
# END DEFAULT OVERRIDES #
# #############################################################################

class PlantTestCase(OrderedTestCase):
    @classmethod
    def setUpClass(cls):
        match, guesses = attribute_best_guess(cls._module, "Plant")

        cls._p1 = None
        cls._p2 = None

        if not len(guesses):
            cls._Plant = None
            return

        cls._Plant = getattr(cls._module, guesses[0])

    def setUp(self):
        if self._Plant is None:
            return self.skipTest("No class Plant defined.")

        return True

    def ensureP1(self):
        p1 = self._Plant([100, 200], "Iron Bark")
        self._p1 = p1

    def ensureP2(self):
        p2 = self._Plant([150, 250], "Yellow Box")
        self._p2 = p2

    def test_0(self):
        """p1 = Plant([100, 200], "Iron Bark")"""
        self.ensureP1()

    def test_1(self):
        """repr(p1)"""
        try:
            self.ensureP1()
        except:
            return self.skipTest("Could not create p1.")

        self.assertEquals(repr(self._p1), "Iron Bark [100, 200] id_2")

    def test_2(self):
        """str(p1)"""
        try:
            self.ensureP1()
        except:
            return self.skipTest("Could not create p1.")

        self.assertEquals(str(self._p1), "Plant\n-----\nName: Iron Bark\nLocation: 100, 200\nID: id_3")

    def test_3(self):
        """p2 = Plant([150, 250], "Yellow Box")"""
        self.ensureP2()

    def test_4(self):
        """repr(p2)"""
        try:
            self.ensureP2()
        except:
            return self.skipTest("Could not create p2.")

        self.assertEquals(repr(self._p2), "Yellow Box [150, 250] id_5")

    def test_5(self):
        """p1.get_position()"""
        try:
            self.ensureP1()
        except:
            return self.skipTest("Could not create p1.")

        self.assertEquals(self._p1.get_position(), [100, 200])

    def test_6(self):
        """p1.get_full_position()"""
        try:
            self.ensureP1()
        except:
            return self.skipTest("Could not create p1.")

        self.assertEquals(self._p1.get_full_position(), [100, 200])

    def test_7(self):
        """p1.get_track()"""
        try:
            self.ensureP1()
        except:
            return self.skipTest("Could not create p1.")

        self.assertEquals(self._p1.get_track(), [])


import time


class AnimalTestCase(OrderedTestCase):
    @classmethod
    def setUpClass(cls):
        match, guesses = attribute_best_guess(cls._module, "Animal")

        cls._a1 = None
        cls._a2 = None

        if not len(guesses):
            cls._Animal = None
            return

        cls._Animal = getattr(cls._module, guesses[0])

    def setUp(self):
        if self._Animal is None:
            return self.skipTest("No class Animal defined.")


        # patch time module
        self._real_time = time.time
        time.time = lambda: 1234567890.1234567

    def tearDown(self):
        # unpatch time module
        time.time = self._real_time

    def ensureA1(self):
        a1 = self._Animal([[[175, 280], time.time()]], "Wallaby", "male", "")
        self._a1 = a1

    def ensureA2(self):
        a2 = self._Animal([[[175, 280], time.time()]], "Wallaby", "male", "1111")
        self._a2 = a2

        a2.add_location([188, 288])

    def test_0(self):
        """Create a1 Animal([[[175,280], time.time()]], "Wallaby", "male", "")
(time is assumed to be 1234567890.1234567 (14/02/09 9:31))"""
        self.ensureA1()

    def test_1(self):
        """repr(a1)"""
        try:
            self.ensureA1()
        except:
            return self.skipTest("Could not create a1.")

        self.assertEquals(repr(self._a1), "Wallaby  male [[[175, 280], 1234567890.1234567]] id_10")

    def test_2(self):
        """str(a1)"""
        try:
            self.ensureA1()
        except:
            return self.skipTest("Could not create a1.")

        self.assertEquals(str(self._a1), "Animal\n------\nName: Wallaby\nGender: male\nLocation: 175, 280\nID: id_12")

    def test_3(self):
        """a2 = Animal([[[175,280], time.time()]], "Wallaby", "male", "1111")
(time is assumed to be 1234567890.1234567 (14/02/09 9:31))"""
        self.ensureA2()

    def test_4(self):
        """str(a2)"""
        try:
            self.ensureA2()
        except:
            return self.skipTest("Could not create a2.")

        self.assertEquals(str(self._a2), "Animal\n------\nName: Wallaby\nGender: male\nLocation: 188, 288\n"
                                         "Time: 14/02/09 09:31\nID: id_14\nTracker ID: 1111")

    def test_5(self):
        """a2.get_position()"""
        try:
            self.ensureA2()
        except:
            return self.skipTest("Could not create a2.")

        self.assertEquals(self._a2.get_position(), [188, 288])

    def test_6(self):
        """a2.get_full_position()"""
        try:
            self.ensureA2()
        except:
            return self.skipTest("Could not create a2.")

        self.assertEquals(self._a2.get_full_position(),
                          [[[175, 280], 1234567890.1234567], [[188, 288], 1234567890.1234567]])

    def test_7(self):
        """a1.get_position()"""
        try:
            self.ensureA1()
        except:
            return self.skipTest("Could not create a1.")

        self.assertEquals(self._a1.get_position(), [175, 280])

    def test_8(self):
        """a1.get_full_position()"""
        try:
            self.ensureA1()
        except:
            return self.skipTest("Could not create a1.")

        self.assertEquals(self._a1.get_full_position(), [[[175, 280], 1234567890.1234567]])

    def test_9(self):
        """a2.get_track()"""
        try:
            self.ensureA2()
        except:
            return self.skipTest("Could not create a2.")

        self.assertEquals(self._a2.get_track(), [[175, 280], [188, 288]])

    def test_10(self):
        """a1.get_track()"""
        try:
            self.ensureA1()
        except:
            return self.skipTest("Could not create a1.")

        self.assertEquals(self._a1.get_track(), [])


class SurveyModelTestCase(OrderedTestCase):
    @classmethod
    def setUpClass(cls):
        match, guesses = attribute_best_guess(cls._module, "SurveyModel")

        if not len(guesses):
            cls._SurveyModel = None
        else:
            cls._SurveyModel = getattr(cls._module, guesses[0])

        # get Plant/Animal
        match, guesses = attribute_best_guess(cls._module, "Plant")
        if not len(guesses):
            cls._Plant = None
        else:
            cls._Plant = getattr(cls._module, guesses[0])

        match, guesses = attribute_best_guess(cls._module, "Animal")
        if not len(guesses):
            cls._Animal = None
        else:
            cls._Animal = getattr(cls._module, guesses[0])

    def setUp(self):
        if self._SurveyModel is None:
            return self.skipTest("No class SurveyModel defined.")


        # patch time module
        self._real_time = time.time

    def tearDown(self):
        # unpatch time module
        time.time = self._real_time

    def ensureM(self):
        m = self._SurveyModel()
        self._m = m

    def test_0(self):
        """m = SurveyModel()"""
        self.ensureM()

    def test_1(self):
        """m.set_name("example")"""
        self.ensureM()
        m = self._m

        m.set_name("example")

        self.assertEquals(m.get_name(), "example")

    def test_2(self):
        """m.set_image_file("area1.gif")"""
        self.ensureM()
        m = self._m

        m.set_image_file("area1.gif")

        self.assertEquals(m.get_image_file(), "area1.gif")

    def test_3(self):
        """Adding/updating/retrieving organisms and dictionaries."""

        self.ensureM()
        m = self._m

        if not self._Plant:
            return self.skipTest("Plant class is undefined.")

        if not self._Animal:
            return self.skipTest("Animal class is undefined.")

        # try:
        time.time = lambda: 1234567890.1234567
        p1 = self._Plant([100, 200], "Iron Bark")

        time.time = lambda: 2345678901.2345678
        p2 = self._Plant([150, 250], "Yellow Box")

        time.time = lambda: 3456789012.3456789
        a1 = self._Animal([[[175, 280], time.time()]], "Wallaby", "male", "")

        time.time = lambda: 4567890123.4567890
        a2 = self._Animal([[[175, 280], time.time()]], "Wallaby", "male", "1111")
        a2.add_location([188, 288])

        # except:
        # return self.fail("Could not create necessary plant and animal instances (p1, p2, a1, a2).")

        m.add_organism(p1)
        m.add_organism(p2)
        m.add_organism(a1)
        m.add_organism(a2)

        m.add_tracker("1111", a2)

        stdout = ""
        for k in sorted(m.get_organism_ids()):
            stdout += str(m.get_organism(k)) + "\n"

        self.assertMultiLineEqual(stdout, """Plant
-----
Name: Iron Bark
Location: 100, 200
ID: id_20
Plant
-----
Name: Yellow Box
Location: 150, 250
ID: id_21
Animal
------
Name: Wallaby
Gender: male
Location: 175, 280
ID: id_22
Animal
------
Name: Wallaby
Gender: male
Location: 188, 288
Time: 02/10/14 12:22
ID: id_23
Tracker ID: 1111
""", "Organism print out does not match.")

        with self.assertRaises(self._module.TrackerError, msg="m.update_location(\"1111\", [200, 300])"):
            m.update_location("222", [200, 300])

        m.update_location("1111", [200, 300])

        self.assertEquals(str(a2), "Animal\n------\nName: Wallaby\nGender: male\nLocation: 200, 300\n"
                                   "Time: 02/10/14 12:22\nID: id_23\nTracker ID: 1111")

        od = m.get_organism_dictionary()
        self.assertEquals(od, {"id_23": {"id": "id_23", "name": "Wallaby", "gender": "male",
                                        "tracker_id": "1111", "type": "animal",
                                        "position": [[[175, 280], 4567890123.456789],
                                                     [[188, 288], 4567890123.456789],
                                                     [[200, 300], 4567890123.456789]]},
                               "id_21": {"id": "id_21", "name": "Yellow Box", "type": "plant",
                                        "position": [150, 250]},
                               "id_20": {"id": "id_20", "name": "Iron Bark", "type": "plant",
                                        "position": [100, 200]},
                               "id_22": {"id": "id_22", "name": "Wallaby", "gender": "male", "tracker_id": "",
                                        "type": "animal", "position": [[[175, 280], 3456789012.3456789]]}},
                          "m.get_organism_dictionary()")

        td = m.get_tracker_dictionary()
        self.assertEquals(td, {"1111": "id_23"}, "m.get_tracker_dictionary()")


class AssignmentOneMaster(TestMaster):
    def prepare(self):
        # fns = []

        # (class_name, [method, ...], super_class_1, super_class_2, ...)
        klasses = [
            ("Organism", """
                get_id
                set_id
                get_position
                get_full_position
                get_name
                get_track
                to_dictionary
            """.strip().split(), "object"),
            ("Plant", """
                __str__
                to_dictionary
            """.strip().split(), "Organism"),
            ("Animal", """
                __str__
                get_position
                add_location
                get_track
            """.strip().split(), "Organism")
        ]

        module = self._module

        data = self._test_data

        self._tests = [
            # create_io_test_case(module, "make_initial_state", data['initial_states']),
            # create_io_test_case(module, "make_position_string", data['position_strings']),
            # create_io_test_case(module, "num_diffs", data['diffs']),
            # create_io_test_case(module, "position_of_blanks", data['blank_positions']),
            # create_io_test_case(module, "make_move", data['moves']),
            #
            # create_io_test_case(module, "show_current_state", data['current_states']),
            # create_io_test_case(module, "interact", data['interactions']),

            create_naming_test_case(module, klasses=klasses),
            create_docstring_test_case(module, klasses=klasses),
            create_inheritance_test_case(module, klasses=klasses),

            PlantTestCase,
            AnimalTestCase,
            SurveyModelTestCase
        ]

        for test_case in self._tests:
            setattr(test_case, "_module", module)


if __name__ == "__main__":
    t = AssignmentOneMaster()
    t.main()