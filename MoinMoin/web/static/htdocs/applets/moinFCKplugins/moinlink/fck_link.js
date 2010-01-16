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
 * File Name: fck_link.js
 *  Scripts related to the Link dialog window (see fck_link.html).
 * 
 * Version:  2.0 FC (Preview)
 * Modified: 2005-03-12 15:16:39
 * 
 * File Authors:
 *   Frederico Caldeira Knabben (fredck@fckeditor.net)
 */

var dialog	= window.parent ;
var oEditor  = dialog.InnerDialogLoaded();
var FCK   = oEditor.FCK;
var FCKLang  = oEditor.FCKLang;
var FCKConfig = oEditor.FCKConfig;
var isNameRelatedLink = false;

//#### Dialog Tabs

// Set the dialog tabs.
window.parent.AddTab('Info', FCKLang.DlgLnkInfoTab);

// Function called when a dialog tag is selected.
function OnDialogTabChange(tabCode)
{
  ShowE('divInfo'  , (tabCode == 'Info'));
}

// Extends the String object, creating a "EndsWith" method on it.
// this method is part of fckeditor dialog common library
String.prototype.EndsWith = function( value, ignoreCase )
{
  var L1 = this.length ;
  var L2 = value.length ;

  if ( L2 > L1 )
    return false ;

  if ( ignoreCase )
  {
    var oRegex = new RegExp( value + '$' , 'i' ) ;
    return oRegex.test( this ) ;
  }
  else
    return ( L2 == 0 || this.substr( L1 - L2, L2 ) == value ) ;
}

//#### Regular Expressions library.
var oRegex = new Object();

oRegex.UriProtocol = new RegExp('');
oRegex.UriProtocol.compile('^(((http|https|ftp|file|news):\/\/)|mailto:)', 'gi');

oRegex.UrlOnChangeProtocol = new RegExp('');
oRegex.UrlOnChangeProtocol.compile('^(http|https|ftp|file|news)://(?=.)', 'gi');

oRegex.UrlOnChangeTestOther = new RegExp('');
oRegex.UrlOnChangeTestOther.compile('^(javascript:|#)', 'gi'); // was: (...#|/)

oRegex.ReserveTarget = new RegExp('');
oRegex.ReserveTarget.compile('^_(blank|self|top|parent)$', 'i');

//#### Parser Functions

var oParser = new Object();

oParser.ParseEMailUrl = function(emailUrl)
{
  // Initializes the EMailInfo object.
  var oEMailInfo = new Object();
  oEMailInfo.Address = '';
  oEMailInfo.Subject = '';
  oEMailInfo.Body  = '';

  var oParts = emailUrl.match(/^([^\?]+)\??(.+)?/);
  if (oParts)
  {
    // Set the e-mail address.
    oEMailInfo.Address = oParts[1];

    // Look for the optional e-mail parameters.
    if (oParts[2])
    {
      var oMatch = oParts[2].match(/(^|&)subject=([^&]+)/i);
      if (oMatch)
        oEMailInfo.Subject = unescape(oMatch[2]);

      oMatch = oParts[2].match(/(^|&)body=([^&]+)/i);
      if (oMatch)
        oEMailInfo.Body = unescape(oMatch[2]);
    }
  }
  return oEMailInfo;
}

oParser.CreateEMailUri = function(address, subject, body)
{
  var sBaseUri = 'mailto:' + address;

  var sParams = '';

  if (subject.length > 0)
    sParams = '?subject=' + escape(subject);

  if (body.length > 0)
  {
    sParams += (sParams.length == 0 ? '?' : '&');
    sParams += 'body=' + escape(body);
  }

  return sBaseUri + sParams;
}

//#### Initialization Code

// oLink: The actual selected link in the editor.
var oLink = dialog.Selection.GetSelection().MoveToAncestorNode( 'A' ) ;
if ( oLink )
  FCK.Selection.SelectNode( oLink ) ;

window.onload = function()
{
  // Translate the dialog box texts.
  oEditor.FCKLanguageManager.TranslatePage(document);

  // Load the selected link information (if any).
  var firstElement = LoadSelection();

  // Update the dialog box.
  SetLinkType(GetE('cmbLinkType').value);

  // Show the initial dialog content.
  GetE('divInfo').style.display = '';

  // Activate the "OK" button.
  window.parent.SetOkButton(true);

  // select first text input element of dialog for usability
  SelectField(firstElement);
}

function LoadSelection()
{
  // variable for first element of dialog
  var firstElement = 'txtPagename';

  if (!oLink) return firstElement;

  var sType = 'url';

  // Get the actual Link href.
  var sHRef = ''+oLink.getAttribute('href',2);

  // Search for the protocol.
  var sProtocol = oRegex.UriProtocol.exec(sHRef);

  if (sProtocol)
  {
    sProtocol = sProtocol[0].toLowerCase();
    GetE('cmbLinkProtocol').value = sProtocol;

    // Remove the protocol and get the remainig URL.
    var sUrl = sHRef.replace(oRegex.UriProtocol, '');

    if (sProtocol == 'mailto:') // It is an e-mail link.
    {
      var oEMailInfo = oParser.ParseEMailUrl(sUrl);
      GetE('txtUrl').value = oEMailInfo.Address;
    }
    else    // It is a normal link.
    {
      sType = 'url';
      GetE('txtUrl').value = sUrl;
    }

    firstElement  = 'txtUrl';
  }
  else if (oLink.getAttribute('class')=='interwiki' || oLink.getAttribute('class')=='badinterwiki')
  {
    sType = 'interwiki';
    GetE('sctInterwiki').value = oLink.getAttribute('title');
    GetE('txtInterwikipagename').value = decodeUrl(sHRef);
    firstElement = 'txtInterwikipagename';
  }
  else if (sHRef.StartsWith(FCKConfig['WikiBasePath']))
  {
    sType = 'wiki';
    sHRef = sHRef.Remove(0, FCKConfig['WikiBasePath'].length);

    // make links to subpages of own page relative links
    if (sHRef.StartsWith(FCKConfig['WikiPage']))
      sHRef = sHRef.Remove(0, FCKConfig['WikiPage'].length);

    // relative link ../
    if (oLink.innerHTML.StartsWith('../') && sHRef.EndsWith(oLink.innerHTML.substring(3, oLink.innerHTML.length))) 
      sHRef = oLink.innerHTML;

    GetE('txtPagename').value = decodeUrl(sHRef);
    firstElement  = 'txtPagename';
  }
  else     // It is another type of link.
  {
    sType = 'url';

    GetE('cmbLinkProtocol').value = '';
    GetE('txtUrl').value = sHRef;
    firstElement  = 'txtUrl';
  }

  // Update the Link type combo.
  GetE('cmbLinkType').value = sType;

  // when inner html of link and url of link are same set isNameRelatedLink true
  // if isNameRelatedLink is true, inner html is change when url change
  if (sHRef == oLink.innerHTML) {
    isNameRelatedLink = true;
  }

  return firstElement;
}

//#### Link type selection.
function SetLinkType(linkType)
{
  ShowE('divLinkTypeWiki'  , (linkType == 'wiki'));
  ShowE('divLinkTypeInterwiki' , (linkType == 'interwiki'));
  ShowE('divLinkTypeUrl'  , (linkType == 'url'));
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
    GetE('cmbLinkProtocol').value = sProtocol[0].toLowerCase();
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

  switch (GetE('cmbLinkType').value)
  {
    case 'wiki' :
      sUri = GetE('txtPagename').value;
      if (sUri.length == 0)
      {
        alert(FCKLang.DlnLnkMsgNoUrl);
        return false;
      }

      sText = sUri;

      // pages starting with "/" are sub pages of current page, e.g. /SubPage 
      if (sUri[0] == '/')
      {
        sUri = GetE('basepage').value + sUri
      }

      sUri = FCKConfig['WikiBasePath'] + encodeUrl(sUri);
      break;

    case 'interwiki' :
      sUri = GetE('txtInterwikipagename').value;

      if (sUri.length == 0)
      {
        alert(FCKLang.DlnLnkMsgNoUrl);
        return false;
      }

      sText = sUri;
      sUri = encodeUrl(sUri);
      break;

    case 'url' :
      sUri = GetE('txtUrl').value;

      if (sUri.length == 0)
      {
        alert(FCKLang.DlnLnkMsgNoUrl);
        return false;
      }

      sUri = GetE('cmbLinkProtocol').value + sUri;
      sText = sUri;
      sUri = encodeUrl(sUri);
      break;
  }

  // Modifying an existent link.
  if (oLink) {
    oLink.href = sUri;
    SetAttribute( oLink, '_fcksavedurl', sUri ) ;
    if (isNameRelatedLink) {
      oLink.innerHTML = sText;
    }
  }
  else   // Creating a new link.
  {
    oLink = oEditor.FCK.CreateLink(sUri)[0];
    if (! oLink)
    {
      oLink = oEditor.FCK.CreateElement('A');
      oLink.href = sUri;
      oLink.appendChild(oEditor.FCK.EditorDocument.createTextNode(sText)); 
    }
  }

  if (GetE('cmbLinkType').value == 'interwiki')
  { 
    SetAttribute(oLink, 'class', 'badinterwiki'); // Bug on IE.5.5 makes this ineffective! Works on IE6/Moz....
    SetAttribute(oLink, 'title', GetE('sctInterwiki').value);
  }

  return true;
}

function SetUrl(url)
{
  document.getElementById('txtUrl').value = url;
  OnUrlChange();
}
