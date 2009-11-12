<?php
/*
 * @(#)AnyWikiDraw_body.php  
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
 * This file contains the AnyWikiDraw special page.
 *
 * The special page displays a description of AnyWikiDraw, and it is
 * used by the applet to download and upload an image to the Wiki.
 *
 * @author Werner Randelshofer
 * @version $Id: AnyWikiDraw.body.php 131 2009-07-08 20:24:04Z rawcoder $
 */

class AnyWikiDraw extends SpecialPage {
	/**#@+
	 * @access private
	 */
	var $mUploadDescription, $mLicense, $mUploadOldVersion;
	var $mUploadCopyStatus, $mUploadSource, $mWatchthis;
	
	static $version = "0.13";
	
	function AnyWikiDraw() {
		SpecialPage::SpecialPage("AnyWikiDraw");
		wfLoadExtensionMessages('AnyWikiDraw');

		$this->mUploadDescription = '';
		$this->mLicense = '';
		$this->mUploadCopyStatus = '';
		$this->mUploadSource = '';
		$this->mWatchthis = false;
	}
	
	function execute( $par ) {
		global $wgRequest, $wgOut;
		
		if ($wgRequest->wasPosted()) {
			$this->processUpload();
			
		} else if (strlen($wgRequest->getVal("image","")) > 0) {
			$this->processDownload();
		} else {
			$this->setHeaders();
		
			# Get request data from, e.g.
			# $param = $wgRequest->getText('param');
			$hasErrors = false;
				
            # Check uploading enabled
            global $wgEnableUploads, $wgSitename;
        	if( !$wgEnableUploads ) {
				$hasErrors = true;
    			$wgOut->addWikiText(
        			wfMsg('anywikidraw_upload_disabled', $wgSitename)
                );
            } 

            # Check cookies available to Java
            global $wgCookieHttpOnly;
        	if( $wgCookieHttpOnly ) {
				$hasErrors = true;
	   			$wgOut->addWikiText(
        			wfMsg('anywikidraw_cookie_http_only', $wgSitename)
                );
            } 


            # Check file extensions enabled
            global $wgFileExtensions;
            $requiredExtensions = array("svg",/*"svgz",*/"png","jpg");
            $missingExtensions = array();
            foreach ($requiredExtensions as $ext) {
                if (! in_array($ext, $wgFileExtensions)) {
                    $missingExtensions[] = $ext;
                }
            }
            if (count($missingExtensions) == 1) {
				$hasErrors = true;
    			$wgOut->addWikiText(
        			wfMsg('anywikidraw_extension_disabled', $wgSitename, ".".implode(", .", $missingExtensions) )
                );
            } else if (count($missingExtensions) > 1) {
				$hasErrors = true;
    			$wgOut->addWikiText(
        			wfMsg('anywikidraw_extensions_disabled', $wgSitename, ".".implode(", .", $missingExtensions) )
                );
            }
		
			# Show information about AnyWikiDraw
			if (! $hasErrors) {
    	        global $wgAnyWikiDrawVersion;
				$wgOut->addWikiText(
					wfMsg('anywikidraw_about', AnyWikiDraw::$version)
				);
			}
			// Output
			// $wgOut->addHTML( $output );
		}
	}
	
	function processUpload() {
		global $wgRequest, $wgOut;
		
		// Fill in the form data as needed by the upload form
		$wgRequest->data['wpDestFile'] = $wgRequest->data['DrawingName'];
		$wgRequest->data['wpIgnoreWarning'] = '1';
		$wgRequest->data['wpDestFileWarningAck'] ='1';
		$wgRequest->data['wpUploadDescription'] = $wgRequest->data['UploadSummary'];
		$wgRequest->data['wpUploadFile'] = $wgRequest->data['DrawingData'];
		$_FILES['wpUploadFile'] = $_FILES['DrawingData'];
		$wgRequest->data['action'] = $wgRequest->data['Action'];

		// Upload the drawing		
		$form = new UploadForm($wgRequest);
		$details = null;
		$outcome = $form->internalProcessUpload($details);
		

		$drawingTempFile = $wgRequest->getFileTempName('DrawingData');
		$renderedTempFile = $wgRequest->getFileTempName('RenderedImageData');
		$imageMapTempFile =  $wgRequest->getFileTempName('ImageMapData');
	
		// If we were successful so far, look whether a rendered image of the
		// drawing has been uploaded as well.
		if ($outcome == UploadForm::SUCCESS && $renderedTempFile != null) {
		
			$img = $form->mLocalFile; 
			$thumbDir = $img->getThumbPath();
			$params = array( 'width' => $img->getWidth() );
			$thumbName = $img->thumbName($params);
			
			if ($thumbName) {
				// Look at the contents of the file; if we can recognize the
				// type but it's corrupt or data of the wrong type, we should
				// probably not accept it.
				$veri = $form->verify( $renderedTempFile, 'png' );
				if ($veri) {
					// Provide an opportunity for extensions to add further checks
					$error = '';
					if( !wfRunHooks( 'UploadVerification',
						array( $thumbName, $renderedTempFile, &$error ) ) ) {
						
						$veri = false;
					}
				}
				
				
				if ($veri) {
					if (!file_exists($thumbDir)) {
						$thumbDirExists = wfMkdirParents($thumbDir);
					} else {
                        $thumbDirExists = true;
                    }
                    if ($thumbDirExists) {
                        move_uploaded_file($renderedTempFile, $thumbDir.'/'.$thumbName);
                    }
				}
			}				
		}
		
		// Get rid of uploaded files
		if (file_exists($drawingTempFile)) { unlink($drawingTempFile); }
		if (file_exists($renderedTempFile)) { unlink($renderedTempFile); }
		if (file_exists($imageMapTempFile)) { unlink($imageMapTempFile); }
				
	
		// Return outcome along with an appropriate error message to the client	
		switch ($outcome) {
			case  UploadForm::SUCCESS :
				header('HTTP/1.0 200 OK');
				echo('<html><body>Success.</body></html>');
				break;
				
			case  UploadForm::BEFORE_PROCESSING :
				header('HTTP/1.0 500 Internal Server Error');
				echo('<html><body>Hook UploadForm:BeforeProcessing broke processing the file.</body></html>');
				break;
				
			case  UploadForm::LARGE_FILE_SERVER :
				header('HTTP/1.0 500 Internal Server Error');
				echo('<html><body>'.wfMsgHtml( 'largefileserver' ).'</body></html>');
				break;
				
			case  UploadForm::EMPTY_FILE :
				header('HTTP/1.0 400 Bad Request');
				echo('<html><body>'.wfMsgHtml( 'emptyfile' ).'</body></html>');
				break;
				
			case  UploadForm::MIN_LENGTH_PARTNAME :
				header('HTTP/1.0 400 Bad Request');
				echo('<html><body>'.wfMsgHtml( 'minlength1' ).'</body></html>');
				break;
				
			case  UploadForm::ILLEGAL_FILENAME :
				header('HTTP/1.0 400 Bad Request');
				echo('<html><body>'.wfMsgHtml( 'illegalfilename', htmlspecialchars($wgRequest->data('DrawingName'))).'</body></html>');
				break;
				
			case  UploadForm::PROTECTED_PAGE :
				header('HTTP/1.0 403 Forbidden');
				echo('<html><body>');
				echo('<p>You are not allowed to change this drawing:</p>');
				$this->echoDetails($details['permissionserrors']);
				echo('</body></html>');
				break;
				
			case  UploadForm::OVERWRITE_EXISTING_FILE :
				header('HTTP/1.0 403 Forbidden');
				echo('<html><body>You may not overwrite the existing drawing.</body></html>');
				break;
				
			case  UploadForm::FILETYPE_MISSING :
				header('HTTP/1.0 400 Bad Request');
				echo('<html><body>The type of the uploaded file is not explicitly allowed.</body></html>');
				break;
				
			case  UploadForm::FILETYPE_BADTYPE :
				header('HTTP/1.0 400 Bad Request');
				echo('<html><body>The type of the uploaded file is explicitly disallowed.</body></html>');
				break;
				
			case  UploadForm::VERIFICATION_ERROR :
				header('HTTP/1.0 400 Bad Request');
				echo('<html><body>');
				echo('<p>The uploaded file did not pass server verification.</p>');
				echo('</body></html>');
				break;
				
			case  UploadForm::UPLOAD_VERIFICATION_ERROR :
				header('HTTP/1.0 403 Bad Request');
				echo('<html><body>');
				echo('<p>The uploaded file did not pass server verification:</p>');
				$this->echoDetails($details['error']);
				echo('</body></html>');
				break;
				
			case  UploadForm::UPLOAD_WARNING :
				header('HTTP/1.0 400 Bad Request');
				echo('<html><body>');
				echo('<p>The server issued a warning for this file:</p>');
				$this->echoDetails($details['warning']);
				echo('</body></html>');
				break;
				
			case  UploadForm::INTERNAL_ERROR :
				header('HTTP/1.0 500 Internal Server Error');
				echo('<html><body>');
				echo('<p>Function UploadForm:internalProcessUpload encountered an internal error.</p>');
				echo('<p>'.$details['internal'].'</p>');
				echo('</body></html>');
				break;
				
			default :
				header('HTTP/1.0 500 Internal Server Error');
				echo('<html><body>Function UploadForm:internalProcessUpload returned an unknown code: '.$outcome.'.</body></html>');
				break;
		}
		exit();
	}
	
	function echoDetails($msg) {
		if (is_array($msg)) {
			foreach ($msg as $submsg) {
				$this->echoDetails($submsg);
			}
		} else {
			echo('</p>'.$msg.'</p>');
		}
	}
}
?>