<cfsetting enablecfoutputonly="true">
<!---
 * FCKeditor - The text editor for Internet - http://www.fckeditor.net
 * Copyright (C) 2003-2008 Frederico Caldeira Knabben
 *
 * == BEGIN LICENSE ==
 *
 * Licensed under the terms of any of the following licenses at your
 * choice:
 *
 *  - GNU General Public License Version 2 or later (the "GPL")
 *    http://www.gnu.org/licenses/gpl.html
 *
 *  - GNU Lesser General Public License Version 2.1 or later (the "LGPL")
 *    http://www.gnu.org/licenses/lgpl.html
 *
 *  - Mozilla Public License Version 1.1 or later (the "MPL")
 *    http://www.mozilla.org/MPL/MPL-1.1.html
 *
 * == END LICENSE ==
 *
 * Sample page for ColdFusion.
--->
<cfoutput>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
	<head>
		<title>FCKeditor - Sample</title>
		<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
		<meta name="robots" content="noindex, nofollow">
		<link href="../sample.css" rel="stylesheet" type="text/css" />
		<script type="text/javascript">

function FCKeditor_OnComplete( editorInstance )
{
	var oCombo = document.getElementById( 'cmbToolbars' ) ;
	oCombo.value = editorInstance.ToolbarSet.Name ;
	oCombo.style.visibility = '' ;
}

function ChangeToolbar( toolbarName )
{
	window.location.href = window.location.pathname + "?Toolbar=" + toolbarName ;
}

		</script>
	</head>
	<body>
		<h1>FCKeditor - ColdFusion - Sample 3</h1>
		This sample shows how to change the editor toolbar.
		<hr>
		<table cellpadding="0" cellspacing="0" border="0">
			<tr>
				<td>
					Select the toolbar to load:&nbsp;
				</td>
				<td>
					<select id="cmbToolbars" onchange="ChangeToolbar(this.value);" style="VISIBILITY: hidden">
						<option value="Default" selected>Default</option>
						<option value="Basic">Basic</option>
					</select>
				</td>
			</tr>
		</table>
		<br>
<form action="sampleposteddata.cfm" method="post" target="_blank">
</cfoutput>

<cfif isDefined( "URL.Toolbar" )>
	<cfset toolbarSet = HTMLEditFormat( URL.Toolbar )>
<cfelse>
	<cfset toolbarSet = "Default">
</cfif>

<!--- Calculate basepath for FCKeditor. It's in the folder right above _samples --->
<cfset basePath = Left( cgi.script_name, FindNoCase( '_samples', cgi.script_name ) - 1 )>

<cfmodule
	template="../../fckeditor.cfm"
	basePath="#basePath#"
	instanceName="myEditor"
	value='<p>This is some <strong>sample text</strong>. You are using <a href="http://www.fckeditor.net/">FCKeditor</a>.</p>'
	width="100%"
	height="200"
	toolbarSet="#toolbarSet#"
>

<cfoutput>
			<br>
			<input type="submit" value="Submit">
		</form>
	</body>
</html>
</cfoutput>
<cfsetting enablecfoutputonly="false">
