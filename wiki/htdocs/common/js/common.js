//
// MoinMoin commonly used JavaScript functions
//
function check_gui_editor(){
 var sAgent = navigator.userAgent.toLowerCase()
 // Internet Explorer
 if ( sAgent.indexOf("msie") != -1 && sAgent.indexOf("mac") == -1 && sAgent.indexOf("opera") == -1 ){
  var sBrowserVersion = navigator.appVersion.match(/MSIE (.\..)/)[1]
  return ( sBrowserVersion >= 5.5 )
 }
 // Gecko
 else if ( navigator.product == "Gecko" && navigator.productSub >= 20030210 )
  return true
 // Safari
 else if ( sAgent.indexOf("safari") != -1 )
  return ( sAgent.match( /safari\/(\d+)/ )[1] >= 312 ) // Build must be at least 312 (1.3)
 else
  return false
}

function onload(){
 var enable_gui_editor = check_gui_editor()
 if ( enable_gui_editor){
  guieditlink = document.getElementById("guieditlink")
  if ( guieditlink ){
   guieditlink.style.display = 'inline'
  }
  editlink = document.getElementById("editlink")
  if ( editlink ){
   href = editlink.href.replace('editor=textonly', 'editor=guipossible')
   editlink.href = href
  }
  switch2gui = document.getElementById("switch2gui")
  if ( switch2gui ){
   // TODO by some js coder: make the (invisible) "GUI editor" button visible.
  }
 }
}

// Initialize after loading the page
window.onload = onload

