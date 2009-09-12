<?php
 # Embeds the TWikiDraw Plugin from the TWiki project
 # (http://twiki.org/cgi-bin/view/TWiki/TWikiDrawPlugin) 
 # 
 # This plugin/Cookbook script can be fairly destructive, so
 # be careful, anything and everything that does or could go
 # wrong is your problem not mine, sorry! (I've not had any problems
 # myself, but as it accesses files on your system, it may go horribly
 # wrong, who knows!)
 #
 # docs see http://www.pmwiki.org/wiki/Cookbook/PmWikiDraw
 #
 # Version 03-03-2005_01
 #
 # Original Author: Ciaran Jessup
 # Modifications By: Knut Alboldt
 # TODO: add parameters width= / height= to drawing-directive and applet-call
 # TODO: Remove 'Create Image' when editing a brand new image.
 # TODO: Does drawing recent changes need some translation stuff?

// Security check.
if (!defined('PmWiki')) exit(); 
 
//---------------- Global Configuration Variables ----------------
SDV($PmWikiDrawPubUrl, $PubDirUrl);
SDV($EnableDrawingDebug, false);
SDV($EnableDrawingVersioning , false); 
SDV($EnableDrawingRecentChanges, false);
SDV($drawingExtraColors, ""); 
SDV($drawingCompatibilityMode, false);
SDV($displayDrawingHistoryFmt, "<a class='pmwikidrawlink' href='\$showHistoryUrl' title='$[Image history]'><img src='\$pubdirurl/drawing/news.gif'/></a>");
SDV($displayDrawingEditFmt, "<a class='pmwikidrawlink' href='\$editImageUrl' title='$[Edit Image]'><img src='\$pubdirurl/drawing/edit.gif'/></a>");

// css style for drawing caption
#$HTMLStylesFmt[] = ".pmwikidraweditlink { font-size:70%; font-weight:bold; }\n"; 

// Add extra colors to the fill/color menus.
#$drawingExtraColors = "Aquamarine=#70DB93,New Tan=EBC79E,Sea Green=238E68,Motorola Blue=#3ff"; 
// -----------------------------------------------------------------------------------------------------------------

//-------------------- Globally executed code --------------------

// Work out which version of PmWiki we're looking at :)
preg_match('/.*-(\\d+)/',$Version,$match);
$pmwikiver = $match[1];
if($pmwikiver <= 1) {
     echo "PmWikiDraw no longer supports PmWiki1, please upgrade to PmWiki2. Thanks.";
	exit();
}

// Add in our required file extensions and associate the new markup. 
SDVA($UploadExts,  array('gif' => 'image/gif', 'draw' => 'text/plain', 'map' => 'text/plain'));
Markup('drawing','inline', "/\\(:drawing\\s*(\\w[-.\\w]*\\w)\\s*:\\)/e", "drawing('$1')");
SDV($HandleActions['imagehistory'],'HandleImageHistory');
SDV($HandleActions['postDrawing'], 'HandlePostDrawing');

// Modify global variables based on the current action type.
if ($action=='editimage')
  { $editImage = true; } 
else 
  { $editImage = false; }

if($action=='print' || $action=='publish' || $action=='editimage' || $action=='edit') { 
	 // Hide the edit & history links when printing/publishing/editing
	$displayDrawingEditFmt = ""; 
	$displayDrawingHistoryFmt = "";
} 

if (!$EnableDrawingVersioning)
  { $displayDrawingHistoryFmt = ""; }

// ------------------- Handle the drawing markup --------------------------------
function drawing($str) {
  global $action, $group, $pagename, $ScriptUrl, $UploadPrefixFmt;
  global $UploadUrlFmt, $UploadDir, $editImage, $displayDrawingEditFmt, $EnableDrawingDebug; 
  global $drawing, $editImageUrl, $drawingExtraColors, $EnableDrawingVersioning;
  global $pubdirurl, $PmWikiDrawPubUrl, $showHistoryUrl, $displayDrawingHistoryFmt;
  global $FmtV, $GCount, $drawingCompatibilityMode, $scripturl;
  global $EnableUpload;
  global $Now;

  $drawing = $str;
  
  $output = "";

  if($EnableUpload != 1) { // Helpful hint to make sure people turn on uploads!
     $output.= "<b>Please note your administrator *NEEDS* to enable uploads before you can save your drawings.</b><br/>";
  } 
	
  // expand to full URL (incl http://) if url is relative:
  if (!preg_match('/^http:/',$ScriptUrl)) 
    { $scripturl = "http://".$_SERVER['HTTP_HOST'] . $ScriptUrl; }
  else 
    { $scripturl = $ScriptUrl; }

 
  // expand to full URL (incl http://) if url is relative:
  if (!preg_match('/^http:/',$PmWikiDrawPubUrl)) 
    { $pubdirurl = "http://".$_SERVER['HTTP_HOST'] . $PmWikiDrawPubUrl; }
  else 
    { $pubdirurl = $PmWikiDrawPubUrl; }

  // Work out the uploads path, both as a url and as an absolute path on the disk.
  $uploadsUrl = FmtPageName("$UploadUrlFmt$UploadPrefixFmt", $pagename)."/";

  // expand to full URL (incl http://) if url is relative:
  if (!preg_match('/^http:/',$uploadsUrl)) 
    { $uploadsUrl = "http://".$_SERVER['HTTP_HOST'] . $uploadsUrl; }
  
  $uploadsPath = FmtPageName("$UploadDir$UploadPrefixFmt",$pagename)."/";

  //Change for tegan, different urls used for direct-downloads...
  if( $EnableDirectDownload != 1 )
  {
	$uploadsUrl= "$scripturl?n=$pagename&action=download&upname=";
  }

  if ( isset($_GET['image']) )
    { $imageToEdit = $_GET['image']; }
	
  $currentlyExists = file_exists($uploadsPath.$drawing.".gif");
  $mapCurrentlyExists = file_exists($uploadsPath.$drawing.".map");


  $editImageUrl = $scripturl.'?pagename='.$pagename.'&action=editimage&image='.$drawing;
  $showHistoryUrl = $scripturl.'?pagename='.$pagename.'&action=imagehistory&image='.$drawing;
  
  if ($mapCurrentlyExists && $editImage == false) {
    // Add the map :)
    $filename = $uploadsPath.$drawing.".map";
    $fp = fopen($filename, "r");
    $contents = fread($fp, filesize($filename));
    fclose($fp);
//    $contents = str_replace("%BUILDEDITLINK%", $editImageUrl, $contents);

####CJ: I still can't get this to work, any ideas Knut?
//  	if($pmwikiver >1) {
//  		$FmtV['$scripturl'] = $scripturl;
//  		$FmtV['$editImageUrl'] = $editImageUrl;
//  	}
//  	else {
	  	$GCount = 0;	
// 	}  
  	
    // Translate all global pmwiki $variables included in map
    $contents = FmtPageName($contents,$pagename); 
	
    // Write the MAP into the outgoing HTML code.
    $output .= "\n".$contents."\n";
  }

  if ($currentlyExists ) {
    $output .= '<img ';
    
	if ($mapCurrentlyExists ) {
      $output .= ' usemap="#'.$drawing.'" ';
	}

  	// Put a nice red border around the current image we're editing.
	if($editImage == true && isset($imageToEdit) && $imageToEdit == $drawing) {
      $output .= ' style="border:4px solid red;" alt="Image being edited" class="pmwikidrawing_editing"';
	}
	else {
	 $output .= ' class="pmwikidrawing" ';
	}

    $output .= ' src="'.$uploadsUrl.$drawing.'.gif"/>';
  	
  	// Mechanism to ensure that our urls get properly added into the variables that
  	// FmtPagename references.
####CJ: I still can't get this to work, any ideas Knut?
//  	if($pmwikiver >1) {
//	  	$FmtV['$editImageUrl'] = $editImageUrl;
//  		$FmtV['$showHistoryUrl'] = $showHistoryUrl;
//  		$FmtV['$pubdirurl'] = $pubdirurl;
//  		$FmtV['$scripturl'] = $scripturl;
//  	}
//  	else {
	  	$GCount = 0;	
//  	}  

    $output .= FmtPagename($displayDrawingEditFmt,$pagename); 
    $output .= FmtPagename($displayDrawingHistoryFmt, $pagename);

    /* KAL: debugging only:
    DEBUG(htmlentities($editImageUrl),1);
    DEBUG(htmlentities($displayDrawingEditFmt),1);
    DEBUG(htmlentities(FmtPagename($displayDrawingEditFmt,$pagename)),1);
    DEBUG(htmlentities($displayDrawingHistoryFmt),1);
    DEBUG(htmlentities(FmtPagename($displayDrawingHistoryFmt, $pagename)),1);
    /* */
  }
  else 
    { $output .= FmtPageName('<a href="'.$editImageUrl.'">$[Create Image]('.$drawing.')</a>'."\n",$pagename); }

  if ($editImage == true && isset($imageToEdit) && $imageToEdit == $drawing) {

	#### CJ: Hmm this might be an issue, as we can't determine whether a user
	#### is *allowed* to edit a picture until the point they save it we might end up 
	#### creating version files when there's no need to, or more to the point, shouldn't
	#### do as we'll be creating new files taking up space when its impossible for the user
	#### to modify the drawing anyway?
	#### Possible work arounds:
	####    1) Always modify a 'tmp' drawing file and have the applet return to this page with
	####       a particular action 'postDrawingEdit' for example.  And at this point check if the 
	####       tmp file was modified i.e. diff between the 'original' and the 'tmp' if so then do 
	####       versioning and redirect to 'browse' on the current page.
	####    2) Too tired.. there must be others..ideas ?
	
    
    // copy of drawing file(s) for versioning
    if($EnableDrawingVersioning == true)  {
      $drawfileprefix = $uploadsPath.$drawing;
      
      if (file_exists("$drawfileprefix.draw")) {
        
        $drawfilelastchanged  = filemtime("$drawfileprefix.draw");
        $drawbackupfileprefix = "$drawfileprefix,$drawfilelastchanged";
        
        if (!file_exists("$drawbackupfileprefix.draw")) {
          // backupfile does not exist
          
          // Copy drawing source file
          if (!@copy("$drawfileprefix.draw", "$drawbackupfileprefix.draw"))
            { $output .= "<pre class='error'>failed to create backup $drawfileprefix.draw to $drawbackupfileprefix.draw</pre>\n"; }
          else
            { $output .= "<pre class='msg'>backuped ".basename("$drawfileprefix.draw")." to ".basename("$drawbackupfileprefix.draw")."</pre>\n"; }
  
          ### KAL: TODO: if copy-ok-messages not wanted, possibly en/disable display of msg by variable ?
          ###            copy messages will only be displayed under then image when in image-edit-mode
          ### KAL: TODO: check if needed to copy all files of drawing
          
          // Copy the map-file
          if (!@copy("$drawfileprefix.map", "$drawbackupfileprefix.map"))
            { $output .= "<pre class='error'>failed to backup $drawfileprefix.map  to $drawbackupfileprefix.map</pre>\n"; }
          else
            { $output .= "<pre class='msg'>backuped ".basename("$drawfileprefix.map")."  to ".basename("$drawbackupfileprefix.map")."</pre>\n"; }
            
          // Copy the gif file (better for displaying old versions)
          if (!@copy("$drawfileprefix.gif", "$drawbackupfileprefix.gif"))
            { $output .= "<pre class='error'>failed to backup $drawfileprefix.gif  to $drawbackupfileprefix.gif</pre>\n"; }
          else
            { $output .= "<pre class='msg'>backuped ".basename("$drawfileprefix.gif")."  to ".basename("$drawbackupfileprefix.gif")."</pre>\n"; }
  
          ### versioning the draw-file and gif-file could be enough, versions could be displayed via (:attachlist:) or via an own
          ### directive that allows display (then possibly better version map and gif too) and / or editing / recovery of older versions
        }
     
        /* for debugging only: (add # in front of this statement to activate !
        $output .= "<pre class='debug'>";
        $output .= "drawfileprefix=$drawfileprefix\n";
        $output .= "drawbackupfileprefix=$drawbackupfileprefix\n";
        $output .= "drawfilelastchanged=$drawfilelastchanged\n";
        $output .= "</pre>";
        /* */
      }
    }    
     // Build the applet string.
//     if( $drawingCompatibilityMode == false) {
      $output .= '<applet code="com.wombatinvasion.pmwikidraw.PmWikiDraw.class" archive="'.$pubdirurl.'/drawing/PmWikiDraw.jar" width="0" height="0">'."\n";
      $output .= '<param name="drawingname" value="'.$drawing.'"/>'."\n";
      $output .= '<param name="wikiurl" value="'.$scripturl.'"/>'."\n";
      $output .= '<param name="pagename" value="'.$pagename.'"/>'."\n";  
      $output .= '<param name="resourcesurl" value="'.$pubdirurl.'/drawing/"/>'."\n";
      $output .= '<param name="drawingbasetime" value="'.$Now.'"/>'."\n";
      $output .= '<param name="drawingloadpath" value="'.$uploadsUrl.$drawing.'.draw"/>'."\n";

      // Configurable parameters.
      if( $EnableDrawingDebug == true) 
        { $output .= '<param name="debug" value="true"/>'."\n"; }

      if ( $drawingExtraColors != "") 
        { $output .= '<param name="extracolors" value="'.$drawingExtraColors.'"/>'."\n"; }
      $output .= '</applet>'."\n";
  //  }
//    else { // Compatibility mode...painful...
//      // In theory, IE should see the OBJECt and run that, but Mozilla should see the comment and run the embed... in theory....
//      $output .= '<OBJECT classid="clsid:8AD9C840-044E-11D1-B3E9-00805F499D93" width="0" height="0" align="baseline" codebase="http://javaweb.eng/plugin/jre-1_3-win.exe#Version=1,3,0,0">'."\n";
//      $output .= '  <PARAM NAME="code" VALUE="CH.ifa.draw.twiki.TWikiDraw.class">'."\n";
//      $output .= '  <PARAM NAME="archive" VALUE="'.$pubdirurl.'/drawing/PmWikiDraw.jar"/>'."\n";
//      $output .= '  <PARAM NAME="type" VALUE="application/x-java-applet;version=1.3" />'."\n";
//     $output .= '  <param name="drawingname" value="'.$drawing.'"/>'."\n";
//      $output .= '  <param name="wikiurl" value="'.$scripturl.'"/>'."\n";
//      $output .= '  <param name="pagename" value="'.$pagename.'"/>'."\n";  
//      $output .= '  <param name="resourcesurl" value="'.$pubdirurl.'/drawing/"/>'."\n";
//      $output .= '  <param name="drawingloadpath" value="'.$uploadsUrl.$drawing.'.draw"/>'."\n";
//      $output .= '  <COMMENT>'."\n";  // This fella should be picked up by mozilla/netscape et al.
//      $output .= '    <EMBED type                  ="application/x-java-applet;version=1.3" width="0" height="0"'."\n";
//      $output .= '                  align                  ="baseline" code="CH.ifa.draw.twiki.TWikiDraw.class"'."\n";
//      $output .= '                  drawingname     ="'.$drawing.'"'."\n";
//      $output .= '                  wikiurl               ="'.$scripturl.'"'."\n";
 //     $output .= '                  pagename          ="'.$pagename.'"'."\n";
 //     $output .= '                  resourcesurl      ="'.$pubdirurl.'/drawing/"'."\n";
 //     $output .= '                  drawingloadpath ="'.$uploadsUrl.$drawing.'.draw"'."\n";
 //     $output .= '                  archive               ="'.$pubdirurl.'/drawing/PmWikiDraw.jar"'."\n";
 //     $output .= '     >'."\n";
  //    $output .= '    <NOEMBED></COMMENT>'."\n";
   //   $output .= '         No JDK 1.3 support for APPLET!! (Fall back to 1.1 Put original pmwikidraw applet here and swap the other two to use the most recent one)'."\n";
   //   $output .='     </NOEMBED>'."\n";
   //   $output .='   </EMBED>'."\n";
    //  $output .= '</OBJECT>'."\n";
    //}
  }
 
  return Keep($output);
}

// ------------ Revision history code. ---------------
// Handle Image History
function HandleImageHistory($pagename) {
  global $HandleDiffFmt,$PageStartFmt,$PageDiffFmt,$PageEndFmt;
  Lock(1);

  if ( isset($_GET['image']) )
    { $imageToSeeHistory = $_GET['image']; }

  $page = ReadPage($pagename,'');
  if (!$page) { Abort("?cannot diff $pagename"); }
//  SDV($HandleDiffFmt,array(&$PageStartFmt,
//    &$PageDiffFmt,'function:PrintDiff',
//    &$PageEndFmt));

  SDV($HandleDiffFmt,array(&$PageStartFmt,
    &$PageDiffFmt,"image history of $imageToSeeHistory",
    &$PageEndFmt));

  PrintFmt($pagename,$HandleDiffFmt);
}

// ---------------------------------------------------
function HandlePostEditImage($pagename) {
  global $PageUrl;
  Redirect($pagename,"\$PageUrl");
}

// ---------------------------------------------------
function HandlePostEditImage2($pagename) {
    global $RecentChangesFmt, $IsPagePosted, $EnableDrawingRecentChanges;

    if ( $EnableDrawingRecentChanges == true && isset($_GET['image']) ){ 
      $imageModified = $_GET['image']; 
      $RecentChangesFmt = array(
       'Main.AllRecentChanges' => 
       '* [[$Group/$Name]]  Drawing - '.$imageModified.' modified . . . $CurrentTime',
       '$Group.RecentChanges' =>
       '* [[$Group/$Name]]  Drawing - '.$imageModified.' modified . . . $CurrentTime');   	 
      $IsPagePosted = true;
	$x = "";
	$y="";
      PostRecentChanges($pagename, $x,$y);
      $IsPagePosted = false;
   }
   HandlePostEditImage($pagename);
}


function HandlePostDrawing($pagename) {
  global $UploadVerifyFunction,$UploadFileFmt,$LastModFile, $Now;
  global $RecentChangesFmt, $IsPagePosted, $EnableDrawingRecentChanges;

  $page = RetrieveAuthPage($pagename,'upload');
  if (!$page) Abort("?cannot upload to $pagename");
  $uploadImage = $_FILES['uploadImage'];
  $uploadDrawing = $_FILES['uploadDrawing'];
  $uploadMap = $_FILES['uploadMap'];

  $drawingBaseTime = $_POST['drawingbasetime'];  // The time the user began editing this drawing.
  $imageupname=$uploadImage['name'];
  $drawingupname=$uploadDrawing['name'];
  $mapupname=$uploadMap['name'];

  $imageupname = MakeUploadName($pagename,$imageupname);
  $drawingupname = MakeUploadName($pagename,$drawingupname);
  $mapupname = MakeUploadName($pagename,$mapupname);
  $imageFilePath = FmtPageName("$UploadFileFmt/$imageupname",$pagename);
  $drawingFilePath = FmtPageName("$UploadFileFmt/$drawingupname",$pagename);
  $mapFilePath = FmtPageName("$UploadFileFmt/$mapupname",$pagename);

  if( file_exists($drawingFilePath) ) {
	// Only worth checking timestamps if a drawing actually currently exists!
    if ( filemtime( $drawingFilePath ) > $drawingBaseTime ) {
		// Assign a new timestamp to the client... hopefully this time they'll be ok... 
		header("PmWikiDraw-DrawingChanged: $Now");
		exit;
    }
  } 

  // If we've got to here then we can assume its safe to overwrite the current file
  // Note: we should do the history archival/recent changes stuff here.
    if ( $EnableDrawingRecentChanges == true && isset($_POST['drawingname']) ){ 
      $imageModified = $_POST['drawingname']; 
      $RecentChangesFmt = array(
       'Main.AllRecentChanges' => 
       '* [[$Group/$Name]]  Drawing - '.$imageModified.' modified . . . $CurrentTime',
       '$Group.RecentChanges' =>
       '* [[$Group/$Name]]  Drawing - '.$imageModified.' modified . . . $CurrentTime');   	 
      $IsPagePosted = true;
	$x = "";
	$y="";
      PostRecentChanges($pagename, $x,$y);
      $IsPagePosted = false;
   }
    
  $filedir = preg_replace('#/[^/]*$#','',$imageFilePath);
  mkdirp($filedir);
  if (!move_uploaded_file($uploadImage['tmp_name'],$imageFilePath))
    { Abort("?cannot move uploaded image to $imageFilePath"); return; }
  fixperms($imageFilePath,0444);
  if ($LastModFile) { touch($LastModFile); fixperms($LastModFile); }

  $filedir = preg_replace('#/[^/]*$#','',$drawingFilePath);
  mkdirp($filedir);
  if (!move_uploaded_file($uploadDrawing['tmp_name'],$drawingFilePath))
    { Abort("?cannot move uploaded drawing to $drawingFilePath"); return; }
  fixperms($drawingFilePath,0444);
  if ($LastModFile) { touch($LastModFile); fixperms($LastModFile); }

  $filedir = preg_replace('#/[^/]*$#','',$mapFilePath);
  mkdirp($filedir);
  if (!move_uploaded_file($uploadMap['tmp_name'],$mapFilePath))
    { Abort("?cannot move uploaded map to $mapFilePath"); return; }
  fixperms($mapFilePath,0444);
  if ($LastModFile) { touch($LastModFile); fixperms($LastModFile); }

  // Sets the drawingBaseTime header for incremental save support.
  header( "PmWikiDraw-DrawingBaseTime: ".filemtime( $drawingFilePath ) );
  
  exit();
}
?>
