/*
 * FCKeditor - The text editor for internet
 * Copyright (C) 2003-2004 Frederico Caldeira Knabben
 * 
 * Licensed under the terms of the GNU Lesser General Public License:
 *   http://www.opensource.org/licenses/lgpl-license.php
 * 
 * For further information visit:
 *   http://www.fckeditor.net/
 * 
 * File Name: fck_attachment.js
 *  Scripts related to the Attachment dialog window.
 * 
 * Version:  2.0
 * Modified: 2005-03-12 15:16:39
 * 
 * File Authors:
 *   Frederico Caldeira Knabben (fredck@fckeditor.net)
 */

var oEditor  = window.parent.InnerDialogLoaded();
var FCK   = oEditor.FCK;
var FCKLang  = oEditor.FCKLang;
var FCKConfig = oEditor.FCKConfig;

//#### Dialog Tabs

// Set the dialog tabs.
window.parent.AddTab('Info', FCKLang.DlgLnkInfoTab);

// Function called when a dialog tag is selected.
function OnDialogTabChange(tabCode)
{
 ShowE('divInfo'  , (tabCode == 'Info'));
}

//#### Regular Expressions library.
var oRegex = new Object();

oRegex.UriProtocol = new RegExp('');
oRegex.UriProtocol.compile('^(((http|https|ftp|news):\/\/)|mailto:)', 'gi');

oRegex.UrlOnChangeProtocol = new RegExp('');
oRegex.UrlOnChangeProtocol.compile('^(http|https|ftp|news)://(?=.)', 'gi');

oRegex.UrlOnChangeTestOther = new RegExp('');
oRegex.UrlOnChangeTestOther.compile('^(javascript:|#|/)', 'gi');

oRegex.ReserveTarget = new RegExp('');
oRegex.ReserveTarget.compile('^_(blank|self|top|parent)$', 'i');

//#### Parser Functions

var oParser = new Object();

//#### Initialization Code

// oLink: The actual selected link in the editor.
var oLink = FCK.Selection.MoveToAncestorNode('A');
if (oLink)
 FCK.Selection.SelectNode(oLink);

window.onload = function()
{
 // Translate the dialog box texts.
 oEditor.FCKLanguageManager.TranslatePage(document);

 // Load the selected link information (if any).
 LoadSelection();

 // Show the initial dialog content.
 GetE('divInfo').style.display = '';

 // Activate the "OK" button.
 window.parent.SetOkButton(true);
}

function LoadSelection()
{
 if (!oLink) return;

 if (oLink.getAttribute('title') && 
          oLink.getAttribute('title').startsWith('attachment:'))
 {
  GetE('txtAttachmentname').value = decodeUrl(
     oLink.getAttribute('title').remove(0, 'attachment:'.length));
 }

}

//#### Link type selection.
function SetLinkType(linkType)
{
 ShowE('divLinkTypeAttachment' , (linkType == 'attachment'));
}

//#### Called when user selects Wikipage.
function OnChangePagename(pagename)
{
  GetE("txtPagename").value = pagename;
}

//#### Called while the user types the URL.
function OnUrlChange()
{
 var sUrl = GetE('txtUrl').value;
 var sProtocol = oRegex.UrlOnChangeProtocol.exec(sUrl);

 if (sProtocol)
 {
  sUrl = sUrl.substr(sProtocol[0].length);
  GetE('txtUrl').value = sUrl;
 }
 else if (oRegex.UrlOnChangeTestOther.test(sUrl))
 {
  GetE('cmbLinkProtocol').value = '';
 }
}

//#### The OK button was hit.
function Ok()
{
 var sUri;
 var sText = '';

   sUri = GetE('txtAttachmentname').value;
   if (sUri.length == 0)
   {
    alert(FCKLang.DlnLnkMsgNoUrl);
    return false;
   }
   sText = sUri;
   sUri = encodeUrl(sUri);

 if (oLink) // Modifying an existent link.
  oLink.href = sUri;
 else   // Creating a new link.
 {
  oLink = oEditor.FCK.CreateLink(sUri);
  if (! oLink)
  {
    oLink = oEditor.FCK.CreateElement('A');
    oLink.href = sUri;
    oLink.appendChild(oEditor.FCK.EditorDocument.createTextNode(sText)); 
  }
 }

  SetAttribute(oLink, 'title', 'attachment:' + sUri);

 return true;
}

function SetUrl(url)
{
 document.getElementById('txtUrl').value = url;
 OnUrlChange();
}

