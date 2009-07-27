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
 * File Name: fckplugin.js
 *  MoinToolbarFontFormatCombo Class: Handles the Fonts combo selector.
 *   modified version of FCKToolbarFontFormatCombo
 *
 * File Authors:
 *   Frederico Caldeira Knabben (fredck@fckeditor.net)
 *   Florian Festi
 */

var MoinToolbarFontFormatCombo = function()
{
  this.CommandName = 'FontFormat';
  this.Command =  FCKCommands.GetCommand(this.CommandName);
}

// Inherit from MoinToolbarSpecialCombo.
MoinToolbarFontFormatCombo.prototype = new FCKToolbarSpecialCombo();

MoinToolbarFontFormatCombo.prototype.GetLabel = function()
{
  return FCKLang.FontFormat;
}

MoinToolbarFontFormatCombo.prototype.CreateItems = function(targetSpecialCombo)
{
  // Get the format names from the language file.
  var aNames = FCKLang['FontFormats'].split(';');
  var oNames = {
    p   : aNames[0],
    pre : aNames[1],
    h1  : aNames[3], // h1 as Title 1, aNames[2] is address
    h2  : aNames[4], // and so on
    h3  : aNames[5], 
    h4  : aNames[6],
    h5  : aNames[7],
    h6  : aNames[8]
  };

  // Get the available formats from the configuration file.
  var aTags = FCKConfig.FontFormats.split(';');

  for (var i in oNames)
  {
    this._Combo.AddItem(i, '<' + i + '>' + oNames[i] + '</' + i + '>', oNames[i]);
  }
}

FCKToolbarItems.RegisterItem( 'MoinFormat', new MoinToolbarFontFormatCombo());
