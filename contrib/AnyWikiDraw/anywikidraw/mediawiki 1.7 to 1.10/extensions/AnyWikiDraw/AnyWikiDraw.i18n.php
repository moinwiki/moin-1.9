<?php
/*
 * @(#)AnyWikiDraw.i18n.php
 *
 * Copyright (c) 2007-2008 by the original authors of AnyWikiDraw
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
 * WARNING: This is an extension for MediaWiki 1.7 through 1.10 only.
 * Do not use it with other versions of MediaWiki without extensive testing!
 * --------
 *
 * Internationalisation file for AnyWikiDraw_body.php.
 *
 * @author Werner Randelshofer
 * @version $Id: AnyWikiDraw.i18n.php 127 2009-07-05 12:04:33Z rawcoder $
 */
$messages = array();
$messages['en'] = array(
    'anywikidraw' => 'AnyWikiDraw Drawing Extension',
    'anywikidraw_about' => '<p>On this Wiki the AnyWikiDraw Drawing Extension $1 is installed.</p>'.
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
    'anywikidraw_upload_disabled' => '<p><b>You can not edit drawings using AnyWikiDraw, because File uploads are disabled on $1.</b></p>',
    'anywikidraw_extension_disabled' => '<p><b>You can not edit drawings with extension $2 using AnyWikiDraw, because this extension is disabled on $1.</b></p>',
    'anywikidraw_extensions_disabled' => '<p><b>You can not edit drawings with extensions $2 using AnyWikiDraw, because these extensions are disabled on $1.</b></p>',
);
?>