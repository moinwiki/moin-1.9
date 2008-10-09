# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - feed some FCKeditor dialogues

    @copyright: 2005-2006 Bastian Blank, Florian Festi, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import config, wikiutil
import re

##############################################################################
### Macro dialog
##############################################################################

def macro_dialog(request):
    help = get_macro_help(request)
    request.emit_http_headers()
    request.write(
        '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
 <head>
  <title>Insert Macro</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta content="noindex,nofollow" name="robots">
  <script src="%s/applets/FCKeditor/editor/dialog/common/fck_dialog_common.js" type="text/javascript"></script>
  <script language="javascript">

var oEditor = window.parent.InnerDialogLoaded() ;
var FCKLang = oEditor.FCKLang ;
var FCKMacros = oEditor.FCKMacros ;

window.onload = function ()
{
 // First of all, translate the dialog box texts
 oEditor.FCKLanguageManager.TranslatePage( document ) ;

 OnChange( "BR" );

 // Show the "Ok" button.
 window.parent.SetOkButton( true ) ;
}

function Ok()
{
 if ( document.getElementById('txtName').value.length == 0 )
 {
  alert( FCKLang.MacroErrNoName ) ;
  return false ;
 }

 FCKMacros.Add( txtName.value ) ;
 return true ;
}

function OnChange( sMacro )
{
  // sMacro = GetE("txtName").value;
  oHelp = GetE("help");
  for (var i=0; i<oHelp.childNodes.length; i++)
  {
    var oDiv = oHelp.childNodes[i];
    if (oDiv.nodeType==1)
    {
      // oDiv.style.display = (GetAttribute(oDiv, "id", "")==sMacro) ? '' : 'none';
      if (GetAttribute(oDiv, "id", "") == sMacro)
      {
          oDiv.style.display = '' ;
          // alert("enabled div id " + sMacro) ;
      }
      else
      {
          oDiv.style.display = 'none' ;
      }
    }
  }
}

  </script>
 </head>
 <body scroll="no" style="OVERFLOW: hidden">
  <table height="100%%" cellSpacing="0" cellPadding="0" width="100%%" border="0">
   <tr>
    <td>
     <table cellSpacing="0" cellPadding="0" align="center" border="0">
      <tr>
       <td valign="top">
       <span fckLang="MacroDlgName">Macro Name</span><br>
       <select id="txtName" size="10" onchange="OnChange(this.value);">
''' % request.cfg.url_prefix_static)

    macros = []
    for macro in macro_list(request):
        if macro == "BR":
            selected = ' selected="selected"'
        else:
            selected = ''
        if macro in help:
            macros.append('<option value="%s"%s>%s</option>' %
                          (help[macro].group('prototype'), selected, macro))
        else:
            macros.append('<option value="%s"%s>%s</option>' %
                          (macro, selected, macro))

    request.write('\n'.join(macros))
    request.write('''
       </select>
     </td>
     <td id="help">''')

    helptexts = []
    for macro in macro_list(request):
        if macro in help:
            match = help[macro]
            prototype = match.group('prototype')
            helptext = match.group('help')
        else:
            prototype = macro
            helptext = ""
        helptexts.append(
            '''<div id="%s" style="DISPLAY: none">
               <b>&lt;&lt;%s&gt;&gt;</b>
               <br/>
               <textarea style="color:#000000" cols="37" rows="10" disabled="disabled">%s</textarea>
               </div>'''
            % (prototype, prototype, helptext))

    request.write(''.join(helptexts))
    request.write('''
     </td>
    </tr>
   </table>
  </td>
 </tr>
</table>
</body>
</html>
''')

def macro_list(request):
    from MoinMoin import macro
    macros = macro.getNames(request.cfg)
    macros.sort()
    return macros

def get_macro_help(request):
    """ Read help texts from SystemPage('HelpOnMacros')"""
    helppage = wikiutil.getLocalizedPage(request, "HelpOnMacros")
    content = helppage.get_raw_body()
    macro_re = re.compile(
        r"\|\|(<.*?>)?\{\{\{" +
        r"<<(?P<prototype>(?P<macro>\w*).*)>>" +
        r"\}\}\}\s*\|\|" +
        r"[^|]*\|\|[^|]*\|\|<[^>]*>" +
        r"\s*(?P<help>.*?)\s*\|\|\s*(?P<example>.*?)\s*(<<[^>]*>>)*\s*\|\|$", re.U|re.M)
    help = {}
    for match in macro_re.finditer(content):
        help[match.group('macro')] = match
    return help

##############################################################################
### Link dialog
##############################################################################

def page_list(request):
    from MoinMoin import search
    name = request.form.get("pagename", [""])[0]
    if name:
        searchresult = search.searchPages(request, 't:"%s"' % name)
        pages = [p.page_name for p in searchresult.hits]
    else:
        pages = [name]
    request.emit_http_headers()
    request.write(
        '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
 <head>
  <title>Insert Page Link</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta content="noindex,nofollow" name="robots">
 </head>
 <body scroll="no" style="OVERFLOW: hidden">
  <table height="100%%" cellSpacing="0" cellPadding="0" width="100%%" border="0">
   <tr>
    <td>
     <table cellSpacing="0" cellPadding="0" align="center" border="0">
      <tr>
       <td>
       <span fckLang="PageDlgName">Page Name</span><br>
       <select id="txtName" size="1">
       %s
       </select>
     </td>
    </tr>
   </table>
  </td>
 </tr>
</table>
</body>
</html>
''' % "".join(["<option>%s</option>\n" % p for p in pages]))

def link_dialog(request):
    request.emit_http_headers()
    # list of wiki pages
    name = request.form.get("pagename", [""])[0]
    if name:
        from MoinMoin import search
        # XXX error handling!
        searchresult = search.searchPages(request, 't:"%s"' % name)

        pages = [p.page_name for p in searchresult.hits]
        pages.sort()
        pages[0:0] = [name]
        page_list = '''
         <tr>
          <td colspan=2>
           <select id="sctPagename" size="1" onchange="OnChangePagename(this.value);">
           %s
           </select>
          <td>
         </tr>
''' % "\n".join(['<option value="%s">%s</option>' % (page, page)
                 for page in pages])
    else:
        page_list = ""

    # list of interwiki names
    interwiki_list = wikiutil.load_wikimap(request)
    interwiki = interwiki_list.keys()
    interwiki.sort()
    iwpreferred = request.cfg.interwiki_preferred[:]
    if not iwpreferred or iwpreferred and iwpreferred[-1] is not None:
        resultlist = iwpreferred
        for iw in interwiki:
            if not iw in iwpreferred:
                resultlist.append(iw)
    else:
        resultlist = iwpreferred[:-1]
    interwiki = "\n".join(
        ['<option value="%s">%s</option>' % (key, key) for key in resultlist])

    # wiki url
    url_prefix_static = request.cfg.url_prefix_static
    scriptname = request.getScriptname()
    if not scriptname or scriptname[-1] != "/":
        scriptname += "/"
    action = scriptname
    basepage = request.page.page_name
    request.write(u'''
<!--
 * FCKeditor - The text editor for internet
 * Copyright (C) 2003-2004 Frederico Caldeira Knabben
 *
 * Licensed under the terms of the GNU Lesser General Public License:
 *   http://www.opensource.org/licenses/lgpl-license.php
 *
 * For further information visit:
 *   http://www.fckeditor.net/
 *
 * File Name: fck_link.html
 *  Link dialog window.
 *
 * Version:  2.0 FC (Preview)
 * Modified: 2005-02-18 23:55:22
 *
 * File Authors:
 *   Frederico Caldeira Knabben (fredck@fckeditor.net)
-->
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<meta http-equiv="Content-Type" content="text/html;charset=utf-8">
<meta name="robots" content="index,nofollow">
<html>
 <head>
  <title>Link Properties</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta name="robots" content="noindex,nofollow" />
  <script src="%(url_prefix_static)s/applets/FCKeditor/editor/dialog/common/fck_dialog_common.js" type="text/javascript"></script>
  <script src="%(url_prefix_static)s/applets/moinFCKplugins/moinlink/fck_link.js" type="text/javascript"></script>
  <script src="%(url_prefix_static)s/applets/moinFCKplugins/moinurllib.js" type="text/javascript"></script>
 </head>
 <body scroll="no" style="OVERFLOW: hidden">
  <div id="divInfo" style="DISPLAY: none">
   <span fckLang="DlgLnkType">Link Type</span><br />
   <select id="cmbLinkType" onchange="SetLinkType(this.value);">
    <option value="wiki" selected="selected">WikiPage</option>
    <option value="interwiki">Interwiki</option>
    <option value="url" fckLang="DlgLnkTypeURL">URL</option>
   </select>
   <br />
   <br />
   <div id="divLinkTypeWiki">
    <table height="100%%" cellSpacing="0" cellPadding="0" width="100%%" border="0">
     <tr>
      <td>
       <form action=%(action)s method="GET">
       <input type="hidden" name="action" value="fckdialog">
       <input type="hidden" name="dialog" value="link">
       <input type="hidden" id="basepage" name="basepage" value="%(basepage)s">
       <table cellSpacing="0" cellPadding="0" align="center" border="0">
        <tr>
         <td>
          <span fckLang="PageDlgName">Page Name</span><br>
          <input id="txtPagename" name="pagename" size="30" value="%(name)s">
         </td>
         <td valign="bottom">
           <input id=btnSearchpage type="submit" value="Search">
         </td>
        </tr>
        %(page_list)s
       </table>
       </form>
      </td>
     </tr>
    </table>
   </div>
   <div id="divLinkTypeInterwiki">
    <table height="100%%" cellSpacing="0" cellPadding="0" width="100%%" border="0">
     <tr>
      <td>
       <table cellSpacing="0" cellPadding="0" align="center" border="0">
        <tr>
         <td>
          <span fckLang="WikiDlgName">Wiki:PageName</span><br>
          <select id="sctInterwiki" size="1">
          %(interwiki)s
          </select>:
          <input id="txtInterwikipagename"></input>
         </td>
        </tr>
       </table>
      </td>
     </tr>
    </table>
   </div>
   <div id="divLinkTypeUrl">
    <table cellspacing="0" cellpadding="0" width="100%%" border="0">
     <tr>
      <td nowrap="nowrap">
       <span fckLang="DlgLnkProto">Protocol</span><br />
       <select id="cmbLinkProtocol">
        <option value="http://" selected="selected">http://</option>
        <option value="https://">https://</option>
        <option value="ftp://">ftp://</option>
        <option value="file://">file://</option>
        <option value="news://">news://</option>
        <option value="mailto:">mailto:</option>
        <option value="" fckLang="DlgLnkProtoOther">&lt;other&gt;</option>
       </select>
      </td>
      <td nowrap="nowrap">&nbsp;</td>
      <td nowrap="nowrap" width="100%%">
       <span fckLang="DlgLnkURL">URL</span><br />
       <input id="txtUrl" style="WIDTH: 100%%" type="text" onkeyup="OnUrlChange();" onchange="OnUrlChange();" />
      </td>
     </tr>
    </table>
    <br />
   </div>
  </div>
 </body>
</html>
''' % locals())

##############################################################################
### Attachment dialog
##############################################################################

def attachment_dialog(request):
    request.emit_http_headers()
    # list of wiki pages
    name = request.form.get("pagename", [""])[0]
    if name:
        from MoinMoin import search
        # XXX error handling!
        searchresult = search.searchPages(request, 't:"%s"' % name)

        pages = [p.page_name for p in searchresult.hits]
        pages.sort()
        pages[0:0] = [name]
        page_list = '''
         <tr>
          <td colspan=2>
           <select id="sctPagename" size="1" onchange="OnChangePagename(this.value);">
           %s
           </select>
          <td>
         </tr>
''' % "\n".join(['<option value="%s">%s</option>' % (page, page)
                 for page in pages])
    else:
        page_list = ""

    # wiki url
    url_prefix_static = request.cfg.url_prefix_static
    scriptname = request.getScriptname()
    if not scriptname or scriptname[-1] != "/":
        scriptname += "/"
    action = scriptname
    request.write('''
<!--
 * FCKeditor - The text editor for internet
 * Copyright (C) 2003-2004 Frederico Caldeira Knabben
 *
 * Licensed under the terms of the GNU Lesser General Public License:
 *   http://www.opensource.org/licenses/lgpl-license.php
 *
 * For further information visit:
 *   http://www.fckeditor.net/
 *
 * File Name: fck_attachment.html
 *  Attachment dialog window.
 *
 * Version:  2.0 FC (Preview)
 * Modified: 2005-02-18 23:55:22
 *
 * File Authors:
 *   Frederico Caldeira Knabben (fredck@fckeditor.net)
-->
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<meta http-equiv="Content-Type" content="text/html;charset=utf-8">
<meta name="robots" content="index,nofollow">
<html>
 <head>
  <title>Attachment Properties</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta name="robots" content="noindex,nofollow" />
  <script src="%(url_prefix_static)s/applets/FCKeditor/editor/dialog/common/fck_dialog_common.js" type="text/javascript"></script>
  <script src="%(url_prefix_static)s/applets/moinFCKplugins/moinattachment/fck_attachment.js" type="text/javascript"></script>
  <script src="%(url_prefix_static)s/applets/moinFCKplugins/moinurllib.js" type="text/javascript"></script>
 </head>
 <body scroll="no" style="OVERFLOW: hidden">
  <div id="divInfo">
   <div id="divLinkTypeAttachment">
    <table height="100%%" cellSpacing="0" cellPadding="0" width="100%%" border="0">
     <tr>
      <td>
       <form action=%(action)s method="GET">
       <input type="hidden" name="action" value="fckdialog">
       <input type="hidden" name="dialog" value="attachment">
       <table cellSpacing="0" cellPadding="0" align="center" border="0">
        <tr>
         <td>
          <span fckLang="AttachmentDlgName">Attachment Name</span><br>
          <input id="txtAttachmentname" name="pagename" size="30" value="%(name)s">
         </td>
        </tr>
       </table>
       </form>
      </td>
     </tr>
    </table>
   </div>
  </div>
 </body>
</html>
''' % locals())

##############################################################################
### Image dialog
##############################################################################

def image_dialog(request):
    request.emit_http_headers()
    url_prefix_static = request.cfg.url_prefix_static
    request.write('''
<!--
 * FCKeditor - The text editor for internet
 * Copyright (C) 2003-2004 Frederico Caldeira Knabben
 *
 * Licensed under the terms of the GNU Lesser General Public License:
 *   http://www.opensource.org/licenses/lgpl-license.php
 *
 * For further information visit:
 *   http://www.fckeditor.net/
 *
 * File Authors:
 *   Frederico Caldeira Knabben (fredck@fckeditor.net)
 *   Florian Festi
-->
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
 <head>
  <title>Link Properties</title>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta name="robots" content="noindex,nofollow" />
  <script src="%(url_prefix_static)s/applets/FCKeditor/editor/dialog/common/fck_dialog_common.js" type="text/javascript"></script>
  <script src="%(url_prefix_static)s/applets/moinFCKplugins/moinimage/fck_image.js" type="text/javascript"></script>
  <script src="%(url_prefix_static)s/applets/moinFCKplugins/moinurllib.js" type="text/javascript"></script>
 </head>
 <body scroll="no" style="OVERFLOW: hidden">
    <table cellspacing="0" cellpadding="0" width="100%%" border="0">
     <tr>
      <td nowrap="nowrap">
       <span fckLang="DlgLnkProto">Protocol</span><br />
       <select id="cmbLinkProtocol" onchange="OnProtocolChange();">
        <option value="attachment:" selected="selected">attachment:</option>
        <option value="http://">http://</option>
        <option value="https://">https://</option>
        <!-- crashes often: <option value="drawing:">drawing:</option> -->
        <option value="" fckLang="DlgLnkProtoOther">&lt;other&gt;</option>
       </select>
      </td>
      <td nowrap="nowrap">&nbsp;</td>
      <td nowrap="nowrap" width="100%%">
       <span fckLang="DlgLnkURL">URL or File Name (attachment:)</span><br />
       <input id="txtUrl" style="WIDTH: 100%%" type="text" onkeyup="OnUrlChange();" onchange="OnUrlChange();" />
      </td>
     </tr>
     <tr>
      <td colspan=2>
       <div id="divChkLink">
        <input id="chkLink" type="checkbox"> Link to
       </div>
      </td>
    </table>
 </body>
</html>
''' % locals())


#############################################################################
### Main
#############################################################################

def execute(pagename, request):
    dialog = request.form.get("dialog", [""])[0]

    if dialog == "macro":
        macro_dialog(request)
    elif dialog == "macrolist":
        macro_list(request)
    elif dialog == "pagelist":
        page_list(request)
    elif dialog == "link":
        link_dialog(request)
    elif dialog == "attachment":
        attachment_dialog(request)
    elif dialog == 'image':
        image_dialog(request)
    else:
        from MoinMoin.Page import Page
        request.theme.add_msg("Dialog unknown!", "error")
        Page(request, pagename).send_page()

