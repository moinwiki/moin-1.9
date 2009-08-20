// Register the related commands.
FCKCommands.RegisterCommand( 'Smiley' , new FCKDialogCommand( FCKLang['InsertSmileyLbl'] , FCKLang['InsertSmiley'] , FCKConfig.PluginsPath + 'smiley/fck_smiley.html' , 340, 170 ) ) ;

// Create the "Smiley" toolbar button.
var oSmileyItem = new FCKToolbarButton( 'Smiley', FCKLang['InsertSmiley'] ) ;
oSmileyItem.IconPath = FCKConfig.PluginsPath + 'smiley/smile.png' ;

FCKToolbarItems.RegisterItem( 'Smiley', oSmileyItem) ; 
