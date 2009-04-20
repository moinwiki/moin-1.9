var noLink = /^(?:H1|H2|H3|H4|H5|H6|PRE|TT|IMG)$/i;

if (1 || !FCKBrowserInfo.IsIE)
{
  function LinkState()
  {
    if (FCKSelection.CheckForNodeNames(noLink))
    {
      return FCK_TRISTATE_DISABLED;
    }
    return (FCK.GetNamedCommandState('CreateLink')==FCK_TRISTATE_ON) ? FCK_TRISTATE_ON : FCK_TRISTATE_OFF;
  }

  // Register the related command.
  FCKCommands.RegisterCommand('Link', new FCKDialogCommand( 'Link', FCKLang.DlgLnkWindowTitle, FCKConfig.WikiBasePath + FCKConfig.WikiPage + '?action=fckdialog&dialog=link', 400, 330, LinkState, 'CreateLink'));
} 
else
{
  FCKCommands.RegisterCommand('Link', new FCKDialogCommand( 'Link', FCKLang.DlgLnkWindowTitle, FCKConfig.WikiBasePath + FCKConfig.WikiPage + '?action=fckdialog&dialog=link', 400, 330, FCK.GetNamedCommandState, 'CreateLink'));
}
