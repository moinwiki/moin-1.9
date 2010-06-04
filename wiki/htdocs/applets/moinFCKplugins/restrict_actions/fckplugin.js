
/* ##########################################################
 * RestrictedNamedCommand
 *  extends FCKNamedCommand
 * ##########################################################
 */
var RestrictedNamedCommand = function(commandName, forbidden)
{
  this.Name = commandName;
  this.forbidden = forbidden;
}

RestrictedNamedCommand.prototype = new FCKNamedCommand();

RestrictedNamedCommand.prototype.GetState = function()
{
  var bState = FCK.GetNamedCommandState(this.Name);
  if (FCKSelection.GetType() == 'Control')
  {
    return bState;
  }
  else if (FCKSelection.CheckForNodeNames(this.forbidden))
  { 
    return FCK_TRISTATE_DISABLED;
  }
  return bState;
}

/* #######################################################
 * RestrictedUniqueNamedFormat
 *  extends RestrictedNamedCommand
 * #######################################################
 */

var RestrictedUniqueNamedFormat = function(commandName, forbidden)
{
  this.Name = commandName;
  this.forbidden = forbidden;
}

RestrictedUniqueNamedFormat.prototype = new RestrictedNamedCommand();

RestrictedUniqueNamedFormat.prototype.Execute = function()
{
  if (FCK.GetNamedCommandState(this.Name)==FCK_TRISTATE_OFF)
    FCK.ExecuteNamedCommand('RemoveFormat');

  FCK.ExecuteNamedCommand(this.Name);
}

/* #######################################################
 * RestrictedFormatBlockCommand
 *  extends FCKFormatBlockCommand
 * #######################################################
 */
var RestrictedFormatBlockCommand = function(forbidden)
{
  this.Name = 'FormatBlock' ;
  this.forbidden = forbidden;
}

RestrictedFormatBlockCommand.prototype = new FCKFormatBlockCommand();

RestrictedFormatBlockCommand.prototype.GetState = function()
{
  if (FCKSelection.CheckForNodeNames(this.forbidden))
    return FCK_TRISTATE_DISABLED;
 else
   return FCK.GetNamedCommandValue( 'FormatBlock' ) ;
}

RestrictedFormatBlockCommand.prototype.Execute = function( formatName )
{
  if ( formatName == null || formatName == '' || formatName == 'P')
    FCK.ExecuteNamedCommand( 'FormatBlock', '<P>' );
  else
  {
    FCK.ExecuteNamedCommand('RemoveFormat');
    FCK.ExecuteNamedCommand( 'FormatBlock', '<' + formatName + '>' );
  }
}

/* ####################################################################
 *  RestrictedStyleCommand
 *    extends FCKStyleCommand
 * ####################################################################
 */

var RestrictedStyleCommand = function(forbidden)
{
  this.forbidden = forbidden;
}

RestrictedStyleCommand.prototype = new FCKStyleCommand();
RestrictedStyleCommand.prototype.GetState =  function()
{
 if (FCKSelection.CheckForNodeNames(this.forbidden))
   return FCK_TRISTATE_DISABLED;
 else
 {
   var oSelection = FCK.EditorDocument.selection;
   if ( FCKSelection.GetType() == 'Control' )
   {
     var e = FCKSelection.GetSelectedElement();
     if (e)
       return this.StylesLoader.StyleGroups[e.tagName] ? FCK_TRISTATE_OFF : FCK_TRISTATE_DISABLED ;
     else
       FCK_TRISTATE_OFF;
   }
   else
     return FCK_TRISTATE_OFF;
  }
}

RestrictedStyleCommand.prototype.Execute = function(styleName, styleComboItem )
{
  if ( styleComboItem.Selected )
    styleComboItem.Style.RemoveFromSelection() ;
  else
  {
    if (styleName == "Typewriter")
      FCK.ExecuteNamedCommand('RemoveFormat');

    styleComboItem.Style.ApplyToSelection() ;
  }
  FCK.Focus();
  FCK.Events.FireEvent( "OnSelectionChange" );
}

/* ####################################################################
 * StyleButtonCommand
 * ####################################################################
 */

var StyleButtonCommand = function(stylename, unique)
{
  // using FCK.Style instead of fckstylesloader
  this.style = FCK.Styles.GetStyle(stylename);
  this.unique = unique;
}

StyleButtonCommand.prototype = new FCKStyleCommand();

StyleButtonCommand.prototype.Execute = function()
{
  if (this.GetState()==FCK_TRISTATE_ON)
  {
    this.style.RemoveFromSelection();
  }
  else
  {
    if (this.unique) FCK.ExecuteNamedCommand('RemoveFormat');
    this.style.ApplyToSelection();
  }
  //FCKSelection.GetParentElement().normalize();
  FCK.Focus();
  FCK.Events.FireEvent("OnSelectionChange");
}



/* ####################################################################
 * RestrictedStyleButtonCommand
 * ####################################################################
 */

var RestrictedStyleButtonCommand = function(stylename, forbidden, unique)
{
  this.style = FCK.Styles.GetStyle(stylename);      // using FCK.Style instead of fckstylesloader
  this.forbidden = forbidden;
  this.unique = unique;
}

RestrictedStyleButtonCommand.prototype = new StyleButtonCommand();

RestrictedStyleButtonCommand.prototype.GetState = function()
{
  if (FCKSelection.CheckForNodeNames(this.forbidden))
    return FCK_TRISTATE_DISABLED;
  else
  {
    aStyles = this.GetActiveStyles();
    for (i=0;i<aStyles.length;i++)
      if (aStyles[i] == this.style) return FCK_TRISTATE_ON;
    return FCK_TRISTATE_OFF;
  }
}

// ####################################################################

var noformat = "H1|H2|H3|H4|H5|H6|PRE|A|TT|IMG";
var noextendedformat = noformat + "|SUB|SUPER";
var noFormat = new RegExp("^(?:" + noformat + ")$", "i");
var noExtendedFormat = new RegExp("^(?:" + noextendedformat + ")$", "i");
var noFormatandIndent = new RegExp("^(?:" + noformat + "|TABLE|TR|TD)$", "i");
var noTT = /^(?:H1|H2|H3|H4|H5|H6|PRE|A|IMG)$/i;
var noBlock = /^(?:TABLE|TR|TD|A|IMG)$/i;
var noSmileys = /^(?:H1|H2|H3|H4|H5|H6|PRE|A|TT|SUB|SUPER)$/i;
var noTable = new RegExp("^(?:" + noextendedformat + "|TABLE|UL|OL|DL)$", "i");

// Register some context sensitive commands
// register commands every browser

// formats
FCKCommands.RegisterCommand('Bold', 
 new RestrictedNamedCommand('Bold', noExtendedFormat));
FCKCommands.RegisterCommand('Italic', 
 new RestrictedNamedCommand('Italic', noExtendedFormat));

FCKCommands.RegisterCommand('Underline', 
 new RestrictedNamedCommand('Underline', noExtendedFormat));
FCKCommands.RegisterCommand('StrikeThrough',
 new RestrictedNamedCommand('StrikeThrough', noExtendedFormat));


FCKCommands.RegisterCommand('Small',
 new RestrictedStyleButtonCommand('Small', noExtendedFormat));
FCKCommands.RegisterCommand('Big',
 new RestrictedStyleButtonCommand('Big', noExtendedFormat));


// formats no allowing formats inside
FCKCommands.RegisterCommand('Subscript',
 new RestrictedUniqueNamedFormat('Subscript', noFormat));
FCKCommands.RegisterCommand('Superscript',
 new RestrictedUniqueNamedFormat('Superscript', noFormat));


FCKCommands.RegisterCommand('Typewriter',
 new RestrictedStyleButtonCommand('Typewriter', noTT, true));


// lists, hline
FCKCommands.RegisterCommand('Outdent',
 new RestrictedNamedCommand('Outdent', noFormatandIndent));
FCKCommands.RegisterCommand('Indent',
 new RestrictedNamedCommand('Indent', noFormatandIndent));
FCKCommands.RegisterCommand('InsertOrderedList',
 new RestrictedNamedCommand('InsertOrderedList', noFormatandIndent));
FCKCommands.RegisterCommand('InsertUnorderedList',
 new RestrictedNamedCommand('InsertUnorderedList', noFormatandIndent));
FCKCommands.RegisterCommand('InsertHorizontalRule',
 new RestrictedNamedCommand('InsertHorizontalRule', noFormatandIndent));

// Font formats and styles
FCKCommands.RegisterCommand('FontFormat', 
 new RestrictedFormatBlockCommand(noBlock));
FCKCommands.RegisterCommand('Style', 
 new RestrictedStyleCommand(noFormat));

// misc
FCKCommands.RegisterCommand('Smiley',
  new FCKDialogCommand( 'Smiley', FCKLang.DlgSmileyTitle, 
                        'dialog/fck_smiley.html', FCKConfig.SmileyWindowWidth,
                         FCKConfig.SmileyWindowHeight, 
                         FCKSelection.CheckForNodeNames, noSmileys));
FCKCommands.RegisterCommand('Table', new FCKDialogCommand
 ('Table', FCKLang.DlgTableTitle, 'dialog/fck_table.html', 400, 250,
  FCKSelection.CheckForNodeNames, noTable));

// useless code, this code make each menu's icon disapear.
/*
// Make toolbar items context sensitive
FCKToolbarItems.RegisterItem('Smiley', new FCKToolbarButton
 ('Smiley', FCKLang.InsertSmileyLbl, FCKLang.InsertSmiley, null, false, true));
FCKToolbarItems.RegisterItem('Table', new FCKToolbarButton
 ('Table', FCKLang.InsertTableLbl, FCKLang.InsertTable, null, false, true));
*/

FCKToolbarItems.RegisterItem('Big', new FCKToolbarButton
           ('Big', 'Big>', 'Big', 
            FCK_TOOLBARITEM_ONLYICON, false, true));
  FCKToolbarItems.RegisterItem('Small', new FCKToolbarButton
           ('Small', 'Small', 'Small', 
            FCK_TOOLBARITEM_ONLYICON, false, true));
  FCKToolbarItems.RegisterItem('Typewriter', new FCKToolbarButton
           ('Typewriter', 'Typewriter', 'Typewriter', 
            FCK_TOOLBARITEM_ONLYICON, false, true));
