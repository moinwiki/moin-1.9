/*
 * FCKeditor - Configuration for usage within MoinMoin wiki engine
 */

FCKConfig.Debug = false ;

FCKConfig.StylesXmlPath	= '../../moinfckstyles.xml' ;

FCKConfig.EnableXHTML = true ;
FCKConfig.EnableSourceXHTML = true ;

FCKConfig.FillEmptyBlocks = false ;

FCKConfig.FormatSource = true ;
FCKConfig.FormatOutput = false ;

FCKConfig.GeckoUseSPAN = false ;
FCKConfig.IEForceVScroll = true ;

FCKConfig.StartupFocus = true ;

FCKConfig.ForcePasteAsPlainText	= false ;
FCKConfig.TabSpaces = 0 ;
FCKConfig.ShowBorders = true ;

// when true, IE has problems selecting a line of text and tends to select a whole paragraph.
FCKConfig.UseBROnCarriageReturn	= false ;

FCKConfig.ToolbarStartExpanded = true ;
FCKConfig.ToolbarCanCollapse = false ;

FCKConfig.ToolbarSets["MoinDefault"] = [
 ['PasteText','PasteWord'],
 ['Undo','Redo'], ['Find','Replace'],
 ['MoinFormat'],
 // disabled some styles until IE endless loop is fixed:
 //['Bold', 'Italic', 'Typewriter', 'Underline', 'StrikeThrough', '-', 'Big', 'Small', 'Superscript', 'Subscript'],
 ['Bold', 'Italic', 'Underline', 'StrikeThrough', 'RemoveFormat'],
 ['OrderedList','UnorderedList','-','Indent','Outdent'],
 ['Link','Unlink','Attachment','Image','Smiley'],
 ['Table','Rule','SpecialChar'],
 ['Macro'],
 ['Source']
] ;

FCKConfig.ToolbarSets["MoinBig"] = [
 ['SelectAll','Cut','Copy','Paste','PasteText','PasteWord'],
 ['Undo','Redo'], ['Find','Replace'],
 ['Link','Unlink','Image'],
 ['Table','Rule','Smiley','SpecialChar','UniversalKey'],
 ['OrderedList','UnorderedList','-','Indent','Outdent'],
 ['RemoveFormat'], ['MoinFormat'], ['Style'],
 ['Bold','Italic','Underline','StrikeThrough','-','Superscript','Subscript'],
 ['Source', 'Macro']
] ;



FCKConfig.ContextMenu = ['Generic','Link','Image', 'NumberedList','TableCell','Table'] ;

FCKConfig.LinkBrowser = false ;
FCKConfig.LinkDlgHideTarget = true ;
FCKConfig.LinkDlgHideAdvanced = true ;

FCKConfig.ImageBrowser = false ;
FCKConfig.ImageDlgHideLink = true ;
FCKConfig.ImageDlgHideAdvanced = true ;

/*
FCKConfig.PluginsPath = FCKConfig.BasePath + 'plugins/' ;
*/
/*
FCKConfig.Plugins.Add( 'placeholder', 'en,it' ) ;
*/
FCKConfig.Plugins.Add( 'selection') ;
FCKConfig.Plugins.Add( 'moinbehaviour') ;
FCKConfig.Plugins.Add( 'restrict_actions' ) ;
FCKConfig.Plugins.Add( 'moinunlink' );
FCKConfig.Plugins.Add( 'macro', 'en,it' ) ;
FCKConfig.Plugins.Add( 'moinlink' ) ;
FCKConfig.Plugins.Add( 'moinattachment' ) ;
FCKConfig.Plugins.Add( 'moinformat' ) ;
FCKConfig.Plugins.Add( 'moinimage' ) ;
FCKConfig.Plugins.Add( 'smiley' );

/* The list of the smiley images. MUST be done from here, auto-generating in MoinMoin-Code does not work! */

FCKConfig.SmileyImages = [
'alert.png', 
'angry.png', 
'attention.png', 
'biggrin.png', 
'checkmark.png', 
'devil.png', 
'frown.png', 
'icon-error.png', 
'icon-info.png', 
'idea.png', 
'ohwell.png', 
'prio1.png', 
'prio2.png', 
'prio3.png', 
'redface.png', 
'sad.png', 
'smile.png', 
'smile2.png', 
'smile3.png', 
'smile4.png', 
'star_off.png', 
'star_on.png', 
'thumbs-up.png', 
'tired.png', 
'tongue.png'
] ;

// use smiley with this data mapping object. when insert smiley image with gui editor
// smiley plugin insert additional attribute (title, alt) with this data
FCKConfig.SmileyMap = {
	'alert.png' : '/!\\',
	'angry.png' : 'X-(', 
	'attention.png' : '<!>', 
	'biggrin.png' : ':D', 
	'checkmark.png' : '(./)', 
	'devil.png' : '>:>', 
	'frown.png' : '<:(', 
	'icon-error.png' : '{X}', 
	'icon-info.png' : '{i}', 
	'idea.png' : '(!)', 
	'ohwell.png' : ':\\', 
	'prio1.png' : '{1}', 
	'prio2.png' : '{2}', 
	'prio3.png' : '{3}', 
	'redface.png' : ':o', 
	'sad.png' : ':(', 
	'smile.png' : ':)', 
	'smile2.png' : 'B)', 
	'smile3.png' : ':))', 
	'smile4.png' : ';)', 
	'star_off.png' : '{o}', 
	'star_on.png' : '{*}', 
	'thumbs-up.png' : '{OK}', 
	'tired.png' : '|)', 
	'tongue.png' : ':-?'
};


FCKConfig.CustomStyles =
{
	'Red Title'	: { Element : 'h3', Styles : { 'color' : 'Red' } }
};

// Do not add, rename or remove styles here. Only apply definition changes.
FCKConfig.CoreStyles =
{
	// Basic Inline Styles.
	'Bold'			: { Element : 'strong', Overrides : 'b' },
	'Italic'		: { Element : 'em', Overrides : 'i' },
	'Underline'		: { Element : 'u' },
	'StrikeThrough'	: { Element : 'strike' },
	'Subscript'		: { Element : 'sub' },
	'Superscript'	: { Element : 'sup' },

	// Basic Block Styles (Font Format Combo).
	'p'				: { Element : 'p' },
	'div'			: { Element : 'div' },
	'pre'			: { Element : 'pre' },
	'address'		: { Element : 'address' },
	'h1'			: { Element : 'h1' },
	'h2'			: { Element : 'h2' },
	'h3'			: { Element : 'h3' },
	'h4'			: { Element : 'h4' },
	'h5'			: { Element : 'h5' },
	'h6'			: { Element : 'h6' },

	// Other formatting features.
	'FontFace' :
	{
		Element		: 'span',
		Styles		: { 'font-family' : '#("Font")' },
		Overrides	: [ { Element : 'font', Attributes : { 'face' : null } } ]
	},

	'Size' :
	{
		Element		: 'span',
		Styles		: { 'font-size' : '#("Size","fontSize")' },
		Overrides	: [ { Element : 'font', Attributes : { 'size' : null } } ]
	},

	'Color' :
	{
		Element		: 'span',
		Styles		: { 'color' : '#("Color","color")' },
		Overrides	: [ { Element : 'font', Attributes : { 'color' : null } } ]
	},

	'BackColor'		: { Element : 'span', Styles : { 'background-color' : '#("Color","color")' } },

	'SelectionHighlight' : { Element : 'span', Styles : { 'background-color' : 'navy', 'color' : 'white' } }
};
