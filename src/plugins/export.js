var JSZip = require('jszip');
util = require('../code/util.js');

module.exports = function(server, app, callback) {

    app.route('/export').get(function (req, res) {
        if (!req.user && !config.skipAuth) {
            return res.redirect('/login');
        }

        var user = (config.skipAuth?config.skipUser:req.user.username);
        function exportZ(zip, userDir) {

            // Loop through the pracs
            fs.readdir(userDir, function (err, pracs) {
                if (err) return next(err);

                util.asyncLoop(pracs.length, function(ploop) {

                    var prac = pracs[ploop.iteration()];
                    var pracPath = path.join(userDir, prac);

                    // What type of file is this?
                    fs.stat(pracPath, function (err, stats) {
                        if (err) throw err;
                        if (!stats.isDirectory()) {
                            return ploop.next();
                        }

                        // This is a practical folder. Loop through the scripts
                        var pracZip = zip.folder(prac);
                        fs.readdir(pracPath, function (err, scripts) {
                            if (err) return next(err);

                            util.asyncLoop(scripts.length, function(sloop) {
                                var script = scripts[sloop.iteration()];
                                var scriptPath = path.join(pracPath, script);

                                if (path.extname(script) == ".py") {
                                    // Looks like we have found a script. Add it to the zip
                                    fs.readFile(scriptPath, 'utf-8', function (err, source) {
                                        if (err) return next(err);

                                        // Source modifier [remove inline comments]
                                        source = source.replace(/#\/\/.*/m, "").replace(/\/\*.*?\*\//m, "");
                                        pracZip.file(script, source);

                                        // Add the next script
                                        sloop.next();
                                    });
                                } else {
                                    // This file isn't relevant.
                                    sloop.next();
                                }
                            }, function() {
                                ploop.next();
                            });
                        });
                    });
                }, function() {

                    // We have finished exporting. Save the zip and download it.
                    var buffer = zip.generate({type:"nodebuffer"});

                    // Send the file to the client
                    res.setHeader('Content-type', 'application/zip')
                    res.setHeader('Content-disposition', 'attachment; filename=' + user+".zip");
                    res.send(buffer)
                })
            });
        }

        var zip = new JSZip();
        exportZ(zip, path.join(config.markingDirectory, (config.skipAuth?config.skipUser:req.user.username)));
    });
    callback();
}