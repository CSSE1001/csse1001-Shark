// Globals
masters_student = false;
//interview = ?   <-- set by the edit.ejs

// Criteria util

/**
 * Calculates the total mark for a
 * @param criteria
 * @param save
 */
function calculateMarks(criteria, save) {
    for (key in save) {
        var value = save[key];
        if (value['checked']) {
            // How many marks is this key worth?

        }
    }
}

/**
 * Returns an identifier string for a child
 * @param child - the child
 * @returns identifier - a unique identifier for a child node
 */
function childIdentifier(child) {
    var identifier = child['id'];
    if (typeof identifier === 'undefined') {
        identifier = "row_" + child["criteria"];
    }
    return identifier;
}

/**
 *
 * @param children
 * @param id
 * @returns {*}
 */
function findCriteria(children, id) {
    for (var i = 0; i < children.length; i++) {
        var child = children[i];
        var weight = child['weight'];
        var subchildren = child['children'];
        var identifier = childIdentifier(child);

        if (identifier == id) {
            return child;
        }
        if (typeof subchildren !== 'undefined') {
            var search = findCriteria(subchildren, id);
            if (typeof search !== 'undefined') {
                return search;
            }
        }
    }
    return undefined;
}

/**
 *
 * @param children
 * @param related
 * @param id
 * @returns {*}
 */
function findRelated(children, related, id) {
    for (var i = 0; i < children.length; i++) {
        var child = children[i];
        if (typeof child['requires'] !== 'undefined' && child['requires'].length > 0) {
            if (child['requires'].indexOf(id) != -1) {
                related.push(child);
            }
        }
        var subchildren = child['children'];
        if (typeof subchildren !== 'undefined') {
            findRelated(subchildren, related, id);
        }
    }
    return related;
}


// Client specific
/**
 *
 * @param children
 * @param output
 */
function exportChildren(children, output) {
    for (var i = 0; i < children.length; i++) {
        var child = children[i];
        var subchildren = child['children'];
        if (!masters_student && child['masters'] == true) {
            continue;
        }
        if (typeof subchildren === 'undefined') {
            var id = childIdentifier(child);
            var textarea = document.getElementById(id + "_textarea");
            var checkbox = document.getElementById(id);

            output[id] = {
                checked: checkbox.checked,
                value: textarea.value
            }
        } else {
            exportChildren(subchildren, output);
        }
    }
}

/**
 * Useful functions
 */
/**
 *
 * @param children
 */
function mark(children) {
    for (var i = 0; i < children.length; i++) {
        var child = children[i];
        child['viewed'] = false;
        var subchildren = child['children'];
        if (typeof subchildren !== 'undefined') {
            mark(subchildren);
        }
    }
}

/**
 *
 * @param children
 * @returns {number}
 */
function updateMarks(children) {
    var total = 0.0;
    for (var i = 0; i < children.length; i++) {
        var child = children[i];
        var id = childIdentifier(child);

        if (!masters_student && child['masters'] == true) {
            continue;
        }

        // Calculate the subtotal
        var subtotal = 0.0;
        var subchildren = child['children'];
        if (typeof subchildren !== 'undefined') {
            subtotal = updateMarks(subchildren);
        } else {
            subtotal = child['weight'] * document.getElementById(id).checked;
        }

        // Update the child mark
        var markfield = document.getElementById(id+"_marks");
        markfield.innerHTML = subtotal.toPrecision(2);
        child.mark = subtotal.toPrecision(2);

        // Update the parent total
        total += subtotal;
    }
    return total;
}

function chunkString(s, len) {
    // FROM http://stackoverflow.com/questions/6632530/chunk-split-a-string-in-javascript-without-breaking-words
    var curr = len, prev = 0;
    var output = [];
    while(s[curr]) {
        if(s[curr++] == ' ') {
            output.push(s.substring(prev,curr));
            prev = curr;
            curr += len;
        }
        else
        {
            var currReverse = curr;
            do {
                if(s.substring(currReverse - 1, currReverse) == ' ')
                {
                    output.push(s.substring(prev,currReverse));
                    prev = currReverse;
                    curr = currReverse + len;
                    break;
                }
                currReverse--;
            } while(currReverse > prev)
        }
    }
    output.push(s.substr(prev));
    return output;
}

function computeComments(children) {
    var output = "";
    for (var i = 0; i < children.length; i++) {
        var child = children[i];
        var subchildren = child['children'];
        if (!masters_student && child['masters'] == true) {
            continue;
        }
        if (typeof subchildren !== 'undefined') {
            output += computeComments(subchildren);
        } else {
            var id = childIdentifier(child);
            var textarea = document.getElementById(id + "_textarea");
            var value = textarea.value.trim();
            if (value != "") {

                // Split value into 80 line segments
                var strings = chunkString(value, 78);
                var display = strings.join("\n  ");
                output += "• " + display + "\n";
            }
        }

    }
    return output;
}

function jumpTo(regex) {
    var start = 0;
    for (var i = 0; i < regex.length; i++) {
        start = editor.find(regex[i], {
            regExp: true,
            start: start,
            preventScroll: (i != regex.length - 1)
        });
    }
}

// TODO - duplicate code
function updateGeneral(final, meeting_mark, row, jump) {
    var codeMark = updateMarks(criteria);

    // Is this a masters student? Apply the formula
    if (masters_student) {
        codeMark = (codeMark / 13.0) * 10.0;
    }
    codeMark = Math.ceil(codeMark);
    var output = "";
    // Only show a code mark if the meeting marks are 10
    if ((final && meeting_mark >= codeMark) || (!final && !interview)) {
        output += " " + codeMark + "/10\n";
    } else {
        output += "\n";
    }
    output += computeComments(criteria);
    var rangeStart = editor.find(/General comments:/,{
        regExp: true,
        preventScroll: true // do not change selection
    })
    var rangeEnd = editor.find(/----------------------------------------------/,{
        regExp: true,
        start: rangeStart,
        preventScroll: true // do not change selection
    })
    rangeStart.end = rangeEnd.end;

    // How many rows were added?
    var oldLines = rangeStart.end.row - rangeStart.start.row;
    var newLines = output.split("\n").length;
    editor.session.replace(rangeStart, "General comments:"+output+"\n----------------------------------------------");
    editor.scrollToRow(row + (newLines-oldLines) + jump);
    return codeMark;
}

//TODO - CSSE1001 specific code
function updateMeeting() {
    var icomm = document.getElementById("interview-comments");
    var strings = chunkString(icomm.value, 78);
    var output = strings.join("\n  ");
    var rangeStart = editor.find(/Meeting comments:/,{
        regExp: true,
        preventScroll: true // do not change selection
    })
    var rangeEnd = editor.find(/General comments:/,{
        regExp: true,
        start: rangeStart,
        preventScroll: true // do not change selection
    })
    rangeStart.end = rangeEnd.start;

    // How many rows were added?
    var oldLines = rangeStart.end.row - rangeStart.start.row;
    var newLines = output.split("\n").length;
    editor.session.replace(rangeStart, "Meeting comments: "+output+"\n");
    return (newLines-oldLines);
}

//TODO - CSSE1001 specific code
function updateTotal(final, meeting_mark, code_mark) {
    var total_mark = Math.min(meeting_mark, code_mark);
    var output = "";
    if (final || !interview) {
        output += total_mark + "/10";
    }
    var rangeStart = editor.find(/Total:/,{
        regExp: true,
        preventScroll: true // do not change selection
    })
    var rangeEnd = editor.find(/Meeting comments:/,{
        regExp: true,
        start: rangeStart,
        preventScroll: true // do not change selection
    })
    rangeStart.end = rangeEnd.start;

    // How many rows were added?
    editor.session.replace(rangeStart, "Total: "+output+"\n\n");
}

//TODO - CSSE1001 specific code
function updateComments(final) {
    var imark = document.getElementById("interview-mark").value;
    var meeting_mark = parseInt(imark);
    if (imark == "") {
        meeting_mark = 10;
    }

    var row = editor.getFirstVisibleRow();
    var jump = updateMeeting();
    var code_mark = updateGeneral(final, meeting_mark, row, jump);
    updateTotal(final, meeting_mark, code_mark);
}


// Analytics
// Activity - http://www.kirupa.com/html5/detecting_if_the_user_is_idle_or_inactive.htm
var timeoutID;
var prev_inactivity = new Date();
function setupActivity() {
    this.addEventListener("mousemove", resetTimer, false);
    this.addEventListener("mousedown", resetTimer, false);
    this.addEventListener("keypress", resetTimer, false);
    this.addEventListener("DOMMouseScroll", resetTimer, false);
    this.addEventListener("mousewheel", resetTimer, false);
    this.addEventListener("touchmove", resetTimer, false);
    this.addEventListener("MSPointerMove", resetTimer, false);

    startTimer();
}
function startTimer() {
    // wait 10 seconds before calling goInactive
    timeoutID = window.setTimeout(goInactive, 10000);
}
function resetTimer(e) {
    window.clearTimeout(timeoutID);

    goActive();
}

function goInactive() {
    var now = new Date();
    activity.push({
        start: prev_inactivity,
        end: now,
        interview: interview
    });
    prev_inactivity = now;
}

function goActive() {
    startTimer();
}


/**
 *
 */
function save() {

    // Show the upload progress bar
    document.getElementById("save").innerHTML = "<span class='glyphicon glyphicon-save'></span> Saving</a>";

    // Save the interview comments
    var imark = document.getElementById("interview-mark").value;
    var icomm = document.getElementById("interview-comments").value;
    var iatte = document.getElementById("interviewed").checked;
    document.getElementById("editor").style.display = "none";

    // Flush analytics
    goInactive();

    // Save the full copy
    updateComments(true);
    var code = editor.getSession().getValue();

    // Save the comment and checkbox values
    var exported = {};
    exportChildren(criteria, exported);

    $.ajax({
        xhr: function()
        {
            var xhr = new window.XMLHttpRequest();
            //Upload progress
            xhr.upload.addEventListener("progress", function(evt) {
                if (evt.lengthComputable) {
                    var percentComplete = evt.loaded / evt.total;
                }
            }, false);
            return xhr;
        },
        type: 'POST',
        url: "/edit",
        data: {
            code: code,
            script: script,
            prac: prac,
            criteria: {
                meeting: {
                    attended: iatte,
                    mark: imark,
                    comments: icomm
                },
                analytics: {
                    activity: activity,
                    opened: opened
                },
                criteria: exported
            }
        },
        success: function(data){
            if (data['success'] == true) {
                document.getElementById("save").innerHTML = "<span class='glyphicon glyphicon-save'></span> Saved</a>";
                window.location = "/" + (interview ? "?interview" : "");
            }
        },
        dataType: "json"
    });

}

$(document).ready(function() {

    // Analytics
    setupActivity();
    opened++;

    // Interview
    var imark = document.getElementById("interview-mark");
    var icomm = document.getElementById("interview-comments");
    function updateInterviewed(start) {
        var interview = $($('#interviewed')).prop('checked');
        if (!interview) {
            imark.readOnly = true;
            imark.value = "0";
            icomm.readOnly = true;
            icomm.value = "Did not show up for interview";
        } else if (!start) {
            imark.readOnly = false;
            imark.value = "";
            icomm.readOnly = false;
            icomm.value = "";
            imark.focus();
        }
        updateComments(false);
    }
    $(function() {
        $('#interviewed').change(function() {
            updateInterviewed(false);
        })
    })
    updateInterviewed(true);

    // Editor
    var code = editor.getSession().getValue();
    masters_student = code.indexOf("##### CSSE7030 #####") > -1;


    /**
     *
     * @param child
     */
    function updateChild(child) {
        if (typeof child !== 'undefined' && child['viewed'] == false) {

            // Populate the text area
            var id = childIdentifier(child);
            var textarea  = document.getElementById(id+"_textarea");
            var markfield = document.getElementById(id+"_marks");
            var checkbox  = document.getElementById(id);

            // Do we require any other criteria
            var required = true;
            if (typeof child['requires'] !== 'undefined' && child['requires'].length > 0) {
                for (var i=0; i < child['requires'].length; i++) {
                    if (!document.getElementById(child['requires'][i]).checked) required = false;
                }
            }

            // Save the current value


            // Update the fields
            if (!required) {
                // disables checkbox that does not meet requirements
                textarea.value   = "";
                checkbox.checked = false;
                
                // enables all requisites
                //child['requires'].forEach(function(requisite) {
                //    var elem = $('#' + requisite);
                //    elem.prop('checked', !elem.prop('checked')).trigger('change');
                //});
            } else {
                if (checkbox.checked) {
                    textarea.value = child['true'] || "";
                } else {
                    textarea.value = child['false'] || "";
                }
            }
            child['viewed'] = true;

            // Find related
            var related = findRelated(criteria, [], id);
            for (var i = 0; i < related.length; i++) {
                updateChild(related[i]);
            }
        }
    }

    // Checkbox listener
    $('input[type=checkbox]').change(
        function(){

            // Find the child
            var id = this.id;
            var child = findCriteria(criteria, id);

            // Mark each child as unread
            mark(criteria);
            updateChild(child);

            // Update the marks
            //updateMarks(criteria);

            // Update the code
            updateComments(false);

    });

    // Textarea listener (potentially laggy!)
    $('textarea').on('keyup', function (event) {
        updateComments(false);
    });

    // Meeting comments listener (potentially laggy!)
    $('input').on('keyup', function (event) {
        updateComments(false);
    });

    // Update the marks
    //updateMarks(criteria);

    // Update the code
    updateComments(false);

});