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
	var oCombo = document.getElementById( 'cmbSkins' ) ;

	// Get the active skin.
	var sSkin = editorInstance.Config['SkinPath'] ;
	sSkin = sSkin.match( /[^\/]+(?=\/$)/g ) ;

	oCombo.value = sSkin ;
	oCombo.style.visibility = '' ;
}

function ChangeSkin( skinName )
{
	window.location.href = window.location.pathname + "?Skin=" + skinName ;
}

		</script>
	</head>
	<body>
		<h1>FCKeditor - ColdFusion - Sample 4</h1>
		This sample shows how to change the editor skin.
		<hr>
		<table cellpadding="0" cellspacing="0" border="0">
			<tr>
				<td>
					Select the skin to load:&nbsp;
				</td>
				<td>
					<select id="cmbSkins" onchange="ChangeSkin(this.value);" style="VISIBILITY: hidden">
						<option value="default" selected>Default</option>
						<option value="office2003">Office 2003</option>
						<option value="silver">Silver</option>
					</select>
				</td>
			</tr>
		</table>
		<br>
		<form action="sampleposteddata.cfm" method="post" target="_blank">
</cfoutput>

<!--- Calculate basepath for FCKeditor. It's in the folder right above _samples --->
<cfset basePath = Left( cgi.script_name, FindNoCase( '_samples', cgi.script_name ) - 1 )>

<cfset config = structNew()>
<cfif isDefined( "URL.Skin" )>
	<cfset config["SkinPath"] = basePath & 'editor/skins/' & HTMLEditFormat( URL.Skin ) & '/'>
</cfif>

<cfmodule
	template="../../fckeditor.cfm"
	basePath="#basePath#"
	instanceName="myEditor"
	value='<p>This is some <strong>sample text</strong>. You are using <a href="http://www.fckeditor.net/">FCKeditor</a>.</p>'
	width="100%"
	height="200"
	config="#config#"
>

<cfoutput>
			<br>
			<input type="submit" value="Submit">
		</form>
	</body>
</html>
</cfoutput>
<cfsetting enablecfoutputonly="false">
