/*
 * Copyright (c) 2015, Samuel Colbran <contact@samuco.net>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:

 * Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.

 * Redistributions in binary form must reproduce the above copyright notice, this
 * list of conditions and the following disclaimer in the documentation and/or
 * other materials provided with the distribution.

 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
 * ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

fs = require('fs');
passport = require('passport');
criteria_util = require('../code/criteria.js');

/**
 *
 * @param script
 * @param callback
 */
function getScriptInfo(script, criteria, callback) {
    var name = path.basename(script);
    var savejson = path.join(path.dirname(script), path.basename(script, '.py')+".json");

    // Read the script file
    fs.readFile(script, 'utf-8', function (err, script_data) {
        if (err) return next(err);

        // What is the name of this student?
        var name_regex = /Student Name:(.*)/
        var name_array = name_regex.exec(script_data);
        var student = "";
        if (name_array) {
            student = name_array[1].trim();
        }

        // Does the script have a save file?
        fs.exists(savejson, function(exists) {

            function render(save_json) {
                var mark = -1.0;
                if (typeof save_json !== 'undefined') {
                    mark = criteria_util.calculateMarks(criteria, save_json).toPrecision(2);
                }

                // Read the save file if it exists
                callback(undefined, {
                    name: name,
                    student: student,
                    modified: exists,
                    mark: mark
                })
            }

            if (exists) {
                fs.readFile(savejson, 'utf-8', function (err, save_json) {
                    if (err) return next(err);
                    render(JSON.parse(save_json));
                });
            } else {
                render();
            }
        });
    });
}

/**
 *
 * @param scriptDir
 * @param f
 * @param scripts
 * @param prac
 * @param scriptInfo
 * @param callback
 * @returns {*}
 */
function nextFile(f, args) {
    if (f >= args.files.length) {
        return args.callback(undefined, args.output);
    }

    if (path.extname(args.files[f]) == ".py") {

        // Gather information about this file
        var file = path.join(args.scripts, args.prac, args.files[f]);
        getScriptInfo(file, args.criteria, function(err, info) {
            if (err) {
                return next(err);
            }
            args.output.push(info);
            return nextFile(f + 1, args);
        });
    } else {
        // Ignore this file
        return nextFile( f + 1, args);
    }
}

/**
 *
 * @param scriptDir
 * @param i
 * @param pracs
 * @param pracInfo
 * @param callback
 * @returns {*}
 */
function nextPractical(i, args) {
    if (i >= args.files.length) return args.callback(undefined, args.output);

    // What type of file is this?
    fs.stat(path.join(args.scripts, args.files[i]), function (err, stats) {
        if (err) throw err;
        if (!stats.isDirectory()) {
            return nextPractical(i + 1, args);
        }

        // Read the scripts in this prac
        fs.readdir(path.join(args.scripts, args.files[i]), function (err, files) {
            if (err) return args.callback(err);

            nextFile(0, {
                scripts: args.scripts,
                files: files,
                prac: args.files[i],
                criteria: args.criteria,
                output: [],
                callback: function (err, scriptInfo) {
                    if (err) {
                        return args.callback(err, args.output);
                    }

                    args.output.push({
                        "name": args.files[i],
                        "scripts": scriptInfo
                    })

                    // Process the next practical
                    return nextPractical(i + 1, args);
                }
            });
        });
    });
}

/**
 *
 * @param server
 * @param app
 * @param callback
 */
module.exports = function(server, app, callback) {

    // Load the criteria file
    fs.readFile(config.criteriaPath, 'utf-8', function (err, json_data) {
        var criteria = JSON.parse(json_data);

        // Setup the scripts express page
        app.route('/').get(function (req, res, next) {
            if (!req.user && !config.skipAuth) {
                return res.redirect('/login');
            }

            // GET
            fs.readFile(path.join(config.ejsPath, "mark.ejs"), 'utf-8', function (err, html) {
                if (err) {
                    return next(err);
                }

                function generateScripts(scriptDir) {
                    fs.readdir(scriptDir, function (err, files) {
                        if (err) return next(err);

                        // Gather information about each prac
                        nextPractical(0, {
                            scripts: scriptDir,
                            files: files,
                            output: [],
                            criteria: criteria,
                            callback: function (err, pracInfo) {
                                if (err) return console.error(err);
                                return server.render(req, res, html, {
                                    global_user: (config.skipAuth?config.skipUser:req.user.username),
                                    global_prac: pracInfo,
                                    global_query: req.query
                                });
                            }
                        });
                    });
                }
                generateScripts(path.join(config.markingDirectory, (config.skipAuth?config.skipUser:req.user.username)));
            });
        });
        callback();
    });
}