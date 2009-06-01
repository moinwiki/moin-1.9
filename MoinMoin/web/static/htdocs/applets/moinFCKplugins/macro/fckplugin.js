var oMacroItem;

if (1 || !FCKBrowserInfo.IsIE){
  // Register the related command.
  FCKCommands.RegisterCommand('Macro', new FCKDialogCommand('Macro', FCKLang.MacroDlgTitle, FCKConfig.WikiBasePath + FCKConfig.WikiPage + '?action=fckdialog&dialog=macro', 440, 300, FCKSelection.CheckForNodeNames, noFormat));

  oMacroItem = new FCKToolbarButton('Macro', FCKLang.MacroBtn, null, null, false, true);
}
else
{
  FCKCommands.RegisterCommand('Macro', new FCKDialogCommand('Macro', FCKLang.MacroDlgTitle, FCKConfig.WikiBasePath + FCKConfig.WikiPage + '?action=fckdialog&dialog=macro', 440, 300, null, null));
  oMacroItem = new FCKToolbarButton('Macro', FCKLang.MacroBtn, null, null, false, false);
}

// Create the "Macro" toolbar button.
oMacroItem.IconPath = FCKPlugins.Items['macro'].Path + 'macro.gif';
FCKToolbarItems.RegisterItem('Macro', oMacroItem);

// The object used for all Macro operations.
var FCKMacros = new Object();

// Add a new macro at the actual selection.
FCKMacros.Add = function(name)
{
  var oSpan = FCK.InsertHtml('<span style="background-color:#ffff11">&lt;&lt;' + name + '&gt;&gt;</span>');
}
