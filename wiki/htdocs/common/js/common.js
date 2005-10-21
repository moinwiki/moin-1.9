//
// MoinMoin commonly used JavaScript functions
//

function can_use_gui_editor() {
    var sAgent = navigator.userAgent.toLowerCase();
 
    if (sAgent.indexOf("msie") != -1 && sAgent.indexOf("mac") == -1 &&
        sAgent.indexOf("opera") == -1 ) {
        // Internet Explorer
        var sBrowserVersion = navigator.appVersion.match(/MSIE (.\..)/)[1];
        return ( sBrowserVersion >= 5.5 );
    } else if (navigator.product == "Gecko" && 
               navigator.productSub >= 20030210) {
        // Gecko
        return true;
    } else if (sAgent.indexOf("safari") != -1 ) {
        // Safari - build must be at least 312 (1.3)
        return (sAgent.match( /safari\/(\d+)/ )[1] >= 312 );
    } else {
        // Unknown browser, assume gui editor is not compatible
        return false;
    }
}

function update_ui() {
    if (can_use_gui_editor()) {
        guieditlink = document.getElementById("guieditlink");
        if (guieditlink) {
            guieditlink.style.display = 'inline';
        }
        editlink = document.getElementById("editlink")
        if (editlink) {
            href = editlink.href.replace('editor=textonly',
                                         'editor=guipossible');
            editlink.href = href;
        }
        switch2gui = document.getElementById('switch2gui')
        if (switch2gui) {
            switch2gui.style.display = 'inline';
        }
    }
}

function onload() {
    update_ui()
    // countdown is available when editing
    try {countdown()} catch (e) {}
}

function beforeunload(evt) {
    // confirmleaving is available when editing
    return confirmleaving()
}

// Initialize after loading the page
window.onload = onload

// Catch before unloading the page
window.onbeforeunload = beforeunload

