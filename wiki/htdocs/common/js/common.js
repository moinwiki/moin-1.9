//
// MoinMoin commonly used JavaScript functions
//

// use this instead of assigning to window.onload directly:
function addLoadEvent(func) {
  // alert("addLoadEvent " + func)
  var oldonload = window.onload;
  if (typeof window.onload != 'function') {
    window.onload = func;
  } else {
    window.onload = function() {
      oldonload();
      func();
    }
  }
}

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
    }
    // else if (sAgent.indexOf("safari") != -1 ) {
    //    // Safari - build must be at least 312 (1.3)
    //    return (sAgent.match( /safari\/(\d+)/ )[1] >= 312 );
    // } 
    else {
        // Unknown browser, assume gui editor is not compatible
        return false;
    }
}


function update_edit_links() {
    // Update editlink according if if the browser is compatible
    if (can_use_gui_editor() == false){
        //alert("update_edit_links: can't use gui editor");
        return;
    }
    var editlinks = document.getElementsByName("editlink");
    for (i = 0; i < editlinks.length; i++) {
        var link = editlinks[i];
        href = link.href.replace('editor=textonly','editor=guipossible');
        link.href = href;
        //alert("update_edit_links: modified to guipossible");
    }
}


function add_gui_editor_links() {
    // Add gui editor link after the text editor link
    
    // If the variable is not set or browser is not compatible, exit
    try {gui_editor_link_href}
    catch (e) {
        //alert("add_gui_editor_links: gui_editor_link_href not here");
        return
    }
    if (can_use_gui_editor() == false){
        //alert("add_gui_editor_links: can't use gui_editor");
        return;
    }
    var all = document.getElementsByName('texteditlink');
    for (i = 0; i < all.length; i++) {
        var textEditorLink = all[i];
        // Create a list item with a link
        var guiEditorLink = document.createElement('a');
        guiEditorLink.href = gui_editor_link_href;
        var text = document.createTextNode(gui_editor_link_text);
        guiEditorLink.appendChild(text);
        var listItem = document.createElement('li')
        listItem.appendChild(guiEditorLink);
        // Insert in the editbar
        var editbar = textEditorLink.parentNode.parentNode
        var nextListItem = textEditorLink.parentNode.nextSibling;
        editbar.insertBefore(listItem, nextListItem);
        //alert("add_gui_editor_links: added gui editor link");
    }
}
 

function show_switch2gui() {
    // Show switch to gui editor link if the browser is compatible
    if (can_use_gui_editor() == false) return;
    
    var switch2gui = document.getElementById('switch2gui')
    if (switch2gui) {
        switch2gui.style.display = 'inline';
    }
}


function load() {
    // Do not name this "onload", it does not work with IE :-)
    // TODO: create separate onload for each type of view and set the
    // correct function name in the html. 
    // e.g <body onlod='editor_onload()'>
    
    // Page view stuff
    update_edit_links();
    add_gui_editor_links();
    
    // Editor stuff
    show_switch2gui();
}


function before_unload(evt) {
    // TODO: Better to set this in the editor html, as it does not make
    // sense elsehwere.
    // confirmleaving is available when editing
    try {return confirmleaving();}
    catch (e) {}
}

// Initialize after loading the page
addLoadEvent(load)

// Catch before unloading the page
window.onbeforeunload = before_unload

