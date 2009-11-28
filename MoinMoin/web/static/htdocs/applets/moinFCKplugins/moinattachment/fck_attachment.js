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

var dialog	= window.parent;
var oEditor = dialog.InnerDialogLoaded();
var FCK   = oEditor.FCK;
var FCKLang  = oEditor.FCKLang;
var FCKConfig = oEditor.FCKConfig;

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
var oLink = dialog.Selection.GetSelection().MoveToAncestorNode('A');
if (oLink)
  FCK.Selection.SelectNode(oLink);

window.onload = function()
{
  // Translate the dialog box texts.
  oEditor.FCKLanguageManager.TranslatePage(document);

  // Load the selected link information (if any).
  LoadSelection();

  HandleOkButton();
}


function LoadSelection()
{
  if (!oLink)
  {
    GetE('requestedPagename').value = GetE('attachmentsPagename').value;
    GetE('txtPagename').value = GetE('attachmentsPagename').value;
    GetE('sctAttachments').style.visibility = "visible";     
    return;
  }

  if (oLink.getAttribute('title') && oLink.getAttribute('title').StartsWith('attachment:'))
  {
    SetBasePageAttachName(oLink.getAttribute('title').Remove(0, 'attachment:'.length));
  }
}


// Try to set selected attachment's name and source page name into the dialog.
function SetBasePageAttachName(path)
{
  path = decodeUrl(path);

  var idx = path.lastIndexOf('/'); // Attachment points to a different page ?
  var requestedPagename = unescapeHTML(GetE('requestedPagename').value);
  var attachmentsPagename = unescapeHTML(GetE('attachmentsPagename').value);
  var currPagename = path.substring(0, idx);
  var currAttachmentname = path.substring(idx+1, path.length);

  // If there is a request for an attachment located on a different page
  // then we request a list of attachments for that page.
  if ((currPagename != "") && (currPagename != attachmentsPagename))
  {
    if (requestedPagename == "")
    {
      GetE('requestedPagename').value = currPagename;
      document.DlgAttachmentForm.submit(); // Transmit the form data and reload attachment dialog.
      return;
    }
  }
  else
  {
    GetE('txtAttachmentname').value = currAttachmentname;
    GetE('sctAttachments').value = currAttachmentname;
  }

  // Initialize the user interface.
  GetE('sctAttachments').style.visibility = "visible";
  GetE('requestedPagename').value = GetE('attachmentsPagename').value;
  GetE('txtPagename').value = GetE('attachmentsPagename').value;
}


//#### Called while the user types the remote page name.
function OnPagenameChange()
{
  GetE('requestedPagename').value = StripWhitespace(GetE('txtPagename').value);

  if(GetE('requestedPagename').value != StripWhitespace(GetE('attachmentsPagename').value))
    GetE('sctAttachments').disabled = true;
  else
    GetE('sctAttachments').disabled = false;

  HandleOkButton();
}


// If the user types in an attachment name in the attachment name edit field,
// we can check just in time if the name exists on the current page.
function OnAttachmentnameChange()
{
  // Unselect the currently selected listbox item.
  var idx = GetE('sctAttachments').selectedIndex;
  if(idx!=-1)
    GetE('sctAttachments').options[idx].selected = false;

  HandleOkButton();
}


function OnAttachmentListChange()
{
  var idx = GetE('sctAttachments').selectedIndex;
  GetE('txtAttachmentname').value = GetE('sctAttachments').options[idx].value;
  HandleOkButton();
}


function StripWhitespace(text)
{
  text = text.replace(/^\s*|\s*$/g,'');
  return text;
}


function HandleOkButton()
{
  var pageName = StripWhitespace(GetE('txtPagename').value);
  var attachmentName = StripWhitespace(GetE('txtAttachmentname').value);

  // Activate the "OK" button.
  if (pageName.length == 0 || attachmentName.length == 0)
    window.parent.SetOkButton(false);
  else
    window.parent.SetOkButton(true);
}


// Escape '<', '>', '&' and '"' to avoid XSS issues.
function escapeHTML(text)
{
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
// Unescape '<', '>', '&' and '"' to avoid XSS issues.
function unescapeHTML(text)
{
  return text.replace(/&quot;/g, "\"").replace(/&gt;/g, ">").replace(/&lt;/g, "<").replace(/&amp;/g, "&");
}


function GetAttachmentURI(pageName, attachmentName)
{
  return encodeURI(FCKConfig['WikiBasePath'] + pageName +
          "?action=AttachFile&do=view&target=" + attachmentName);
}


//#### The OK button was hit.
function Ok()
{
  var pageName = StripWhitespace(GetE('txtPagename').value); // Attachment's source page/URL.
  var attachmentName = StripWhitespace(GetE('txtAttachmentname').value);
  var destinationPagename = StripWhitespace(GetE('destinationPagename').value);
  var indexOfAttachmentList = GetE('sctAttachments').selectedIndex;
  var title = '';
  var fullAttachmentName = '';

  // If attachment is on a different page, than we add a reference to it before
  // the attachment name (e.g.: remotepagename/attachment.pdf).
  // But: If you rename the destination's page name, this link won't be
  // processed by moin and will result in a broken link!
  if (destinationPagename != pageName)
    fullAttachmentName = pageName + "/" + attachmentName;
  else
    fullAttachmentName = attachmentName;

  var linkText = fullAttachmentName;
  var attachmentURI = GetAttachmentURI(pageName, attachmentName);

  if (oLink)
  {
    // Modify an existent link.
    oLink.href = attachmentURI;
    SetAttribute( oLink, '_fcksavedurl', attachmentURI ) ;
  }
  else
  {
    // Creating a new link.
    oLink = oEditor.FCK.CreateLink(fullAttachmentName)[0];
    if (!oLink)
    {
      // If no link text is present...
      oLink = oEditor.FCK.CreateElement('A');
      oLink.href = attachmentURI;
      oLink.appendChild(oEditor.FCK.EditorDocument.createTextNode(linkText));
    }
    else
    {
      // If link text is marked...
      oLink.href = attachmentURI;
    }
  }

  SetAttribute(oLink, 'title', 'attachment:' + fullAttachmentName);
  return true;
}
