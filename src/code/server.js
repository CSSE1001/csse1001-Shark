/*
 *
 * Copyright (c) 2015, Samuel Colbran <contact@samuco.net>
 * All rights reserved.
 *
 */

express = require('express');
app     = express();
ejs     = require('ejs');

/**
 *
 * @param req
 * @param res
 * @param html
 * @param options
 */
function render(req, res, html, options) {
    try {
        options = (typeof options !== 'undefined') ? options : {};
        var compiled = ejs.compile(html, { filename: path.join(process.cwd(), './server/file.ejs')});
        html = compiled(options);
        res.send(html);
    } catch (err) {
        console.error(err);
    }
}
module.exports.render = render;

/**
 *
 * @param callback
 */
function setupPlugins(callback) {
    var pluginDir = "./server/";
    fs.readdir(pluginDir, function(err, files) {
        if (err) {
            return console.error(err);
        }

        function nextPlugin(i, files, callback) {
            if (i >= files.length) {
                return callback();
            }

            // What type of file is this?
            if (path.extname(files[i]) == '.js') { // Plugin

                var plugin = require(pluginDir + files[i]);
                plugin(module.exports, app, function (err) {
                    if (err) {
                        return callback(err);
                    }
                    return nextPlugin(i + 1, files, callback);
                });
            } else {
                return nextPlugin(i + 1, files, callback);
            }

            /*
             } else if (path.extname(files[i]) == '.ejs') { // HTML

             console.log("Added route " + '/' + path.basename(files[i]));
             app.route('/' + path.basename(files[i])).get(function (req, res) {
             fs.readFile(pluginDir + files[i], 'utf-8', function (err, html) {
             return render(req, res, html, req.query);
             });
             });
             return nextPlugin(i + 1, files, callback);

             } else {
             */
        }
        nextPlugin(0, files, callback);
    });
}

// Middleware
var methodOverride = require('method-override');
var bodyParser     = require('body-parser')

/**
 *
 * @param callback
 */
function configure(callback) {

    // Start the express server
    app.set('port', config.port);
    app.use(express.static(path.join(process.cwd() , './server/public')));

    // Load middleware
    app.use(methodOverride());
	if (!config.skipAuth) {
		var exsess = 'express-session';
    	app.use(require(exsess)({ resave: true,
        	saveUninitialized: true,
        	secret: 'uwotm8' }));
	}

    app.use(bodyParser.json());
    app.use(bodyParser.urlencoded({ extended: true }));

    // Passport middleware
	if (!config.skipAuth) {
    	app.use(passport.initialize());
   	 	app.use(passport.session());
	}

    // Load plugins
    setupPlugins(function(err) {
        if (err) {
            return callback(err);
        }
        // Complete!
        callback();
    });
}

/**
 *
 * @param callback
 */
function start(callback) {
    http.createServer(app).listen(app.get('port'), function () {
        console.log("Express server listening on port " + app.get('port'));
        callback();
    });
}

module.exports.configure = configure;
module.exports.start     = start;
