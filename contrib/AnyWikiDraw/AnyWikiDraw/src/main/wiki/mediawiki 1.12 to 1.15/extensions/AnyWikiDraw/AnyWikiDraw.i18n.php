<?php
/*
 * @(#)AnyWikiDraw.i18n.php  
 *
 * Copyright (c) 2007-2009 by the original authors of AnyWikiDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the AnyWikiDraw project ("the copyright holders").
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

/**
 * --------
 * WARNING: This is an extension for MediaWiki 1.12 through 1.15 only.
 * Do not use it with other versions of MediaWiki without extensive testing!
 * --------
 *
 * Internationalisation file for AnyWikiDraw_body.php.
 *
 * @author Werner Randelshofer
 * @version $Id: AnyWikiDraw.i18n.php 120 2009-06-28 08:05:06Z rawcoder $
 */
$messages = array();
$messages['en'] = array(
    'anywikidraw' => 'AnyWikiDraw Drawing Extension',
    'anywikidraw_about' => '<p>On this Wiki the AnyWikiDraw $1 Drawing Extension is installed.</p>'.
        '<p>With this extension, you can edit drawings directly inside of a Wiki page.</p>'.
        '<p>To include a drawing in a page, use a tag of the form '.
        '<b><nowiki>{{&#35;drawing:File.svg|width|height}}</nowiki></b>.</p>'.
        '<p>For example '.
        '<b><nowiki>{{&#35;drawing:HappyFace.svg|400|300}}</nowiki></b>.</p>'.
        '<p>The following filename extensions are supported: .svg, .png, .jpg.</p>'.
        '<p>If the file doesn\'t exist, it will be created the first time a drawing has been edited.</p>'.
        '<p>All files that have been created using this extension are listed on the [[Special:Imagelist|file list]] special page.',
    'anywikidraw_license_terms_new_work' => 'By saving your work you agree to the license terms of this Wiki. '.
        '<br>For more information see $1. ',
    'anywikidraw_license_terms_derived_work' => 'By saving your changes you agree to the terms given by the copyright holder of the original work. '.
        '<br>For more information see $2. ',
    'anywikidraw_upload_disabled' => '<p><b>You can not edit drawings using AnyWikiDraw, because you have not enabled file uploading using <code>$wgEnableUploads=true;</code> in LocalSettings.php.</b></p>',
    'anywikidraw_cookie_http_only' => '<p><b>You can not edit drawings using AnyWikiDraw, because you have not made cookies accessible to Java applets using <code>$wgCookieHttpOnly=false;</code> in LocalSettings.php.</b></p>',
    'anywikidraw_extension_disabled' => '<p><b>You can not edit drawings with extension $2 using AnyWikiDraw, because you have not enabled this extension using <code>$wgFileExtensions[] = \'$2\';</code> in LocalSettings.php.</b></p>',
    'anywikidraw_extensions_blacklisted' => '<p><b>You can not edit drawings with extensions $2 using AnyWikiDraw, because you have explicitly blocked this extension using <code>$wgFileBlacklist = \'$2\';</code> in LocalSettings.php.</b></p>',
);
?>