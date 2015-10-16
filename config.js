/*
 *
 * Copyright (c) 2015, Samuel Colbran <contact@samuco.net>
 * All rights reserved.
 *
 */

var config = {}
path = require("path");

// General
//---------------------------
// Express
config.port = 3222; // todo: remove hardcoding in src/resources/HTML/public/js/practical.js:2
config.plugins = path.join(process.cwd(), './src/plugins/');

// Shark
//---------------------------
// Authentication
config.skipAuth = true;
config.skipUser = "admin";

// Directory locations
config.pythonDirectory   = "./db";
config.uploadDirectory   = config.pythonDirectory + "/upload";
config.downloadDirectory = config.pythonDirectory + "/download";
config.markingDirectory  = config.pythonDirectory + "/marking";
config.ejsPath           = "./src/resources/HTML/ejs";
config.criteriaPath      = "./src/resources/criteria/2015/s2/a2.json";
config.publicPath        = "./src/resources/HTML/public";
config.supportPath       = "./src/resources/support";

// Python execution
config.pythonPaths = [
    "/usr/local/bin/python3",   // Mac
    "C:/Python34/python.exe"    // Windows (default install)
];

// MyPyTutor
//---------------------------
// Directory locations
config.tuteDirectory   = "../MyPyTutor/CSSE1001Tutorials";
config.tuteConfig      = config.tuteDirectory + "/tutorials.txt";
config.saveDirectory   = "../MyPyTutor/CSSE1001Solutions";
config.tmpDirectory    = config.pythonDirectory + "/support";
config.tmpScript       = "assign1_soln.py";
config.tutorLib        = "../MyPyTutor/code";
config.tutorLaunch     = "MyPyTutor.py";

// Sockets
config.socketPort = 3333;
//---------------------------

module.exports = config;