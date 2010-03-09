<?php
/*
 * @(#)AnyWikiDraw_body.php 
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
 * This file contains the AnyWikiDraw special page.
 *
 * The special page displays a description of AnyWikiDraw, and it is
 * used by the applet to download and upload an image to the Wiki.
 *
 * @author Werner Randelshofer
 * @version $Id: AnyWikiDraw_body.php 120 2009-06-28 08:05:06Z rawcoder $
 */

include 'SpecialUpload.php';

class AnyWikiDraw extends SpecialPage {
	/**#@+
	 * @access private
	 */
	var $mUploadDescription, $mLicense, $mUploadOldVersion;
	var $mUploadCopyStatus, $mUploadSource, $mWatchthis;
	
	function AnyWikiDraw() {
		SpecialPage::SpecialPage("AnyWikiDraw");
		self::loadMessages();

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
				
			# Show information about AnyWikiDraw
            global $wgAnyWikiDrawVersion;
			$wgOut->addWikiText(
				wfMsg('anywikidraw_about', $wgAnyWikiDrawVersion)
			);

            # Check uploading enabled
            global $wgEnableUploads, $wgSitename;
        	if( !$wgEnableUploads ) {
    			$wgOut->addWikiText(
        			wfMsg('anywikidraw_upload_disabled', $wgSitename)
                );
            } 

            # Check file extensions enabled
            global $wgFileExtensions;
            $requiredExtensions = array("svg","png","jpg");
            $missingExtensions = array();
            foreach ($requiredExtensions as $ext) {
                if (! in_array($ext, $wgFileExtensions)) {
                    $missingExtensions[] = $ext;
                }
            }
            if (count($missingExtensions) == 1) {
    			$wgOut->addWikiText(
        			wfMsg('anywikidraw_extension_disabled', $wgSitename, ".".implode(", .", $missingExtensions) )
                );
            } else if (count($missingExtensions) > 1) {
    			$wgOut->addWikiText(
        			wfMsg('anywikidraw_extensions_disabled', $wgSitename, ".".implode(", .", $missingExtensions) )
                );
            }
		

		
			// Output
			// $wgOut->addHTML( $output );
		}
	}
	
	/** I BORROWED THIS FUNCTION FROM SpecialUpload.php!! CHECK FOR EACH VERSION OF MEDIAWIKI, IF
	 *  THIS FUNCTION STILL MAKES SENSE!
	 *
	 */
	function processUpload() {
		global $wgUser, $wgUploadDirectory, $wgRequest;
		
		$fname= "AnyWikiDraw_body::processUpload";

		// Retrieve form fields
		$drawingName = $wgRequest->getText('DrawingName');
		$drawingWidth = $wgRequest->getText('DrawingWidth');
		$drawingHeight = $wgRequest->getText('DrawingHeight');
		$drawingTempFile =  $wgRequest->getFileTempName('DrawingData');
		$drawingFileSize = $wgRequest->getFileSize( 'DrawingData' );
		$drawingUploadError = $wgRequest->getUploadError('DrawingData');
		$renderedTempFile =  $wgRequest->getFileTempName('RenderedImageData');
		$renderedFileSize = $wgRequest->getFileSize( 'RenderedImageData' );
		$renderedUploadError = $wgRequest->getUploadError('RenderedImageData');
		$imageMapTempFile =  $wgRequest->getFileTempName('ImageMapData');
		$imageMapFileSize = $wgRequest->getFileSize( 'ImageMapData' );
		$imageMapUploadError = $wgRequest->getUploadError('ImageMapData');
		$uploadSummary = $wgRequest->getText('UploadSummary');
		
		// validate image dimension
		if (! is_numeric($drawingWidth) || $drawingWidth < 1) {
			$drawingWidth = null;
		}
		if (! is_numeric($drawingHeight) || $drawingHeight < 1) {
			$drawingHeight = null;
		}

		# If there was no filename or no image data, give up quickly.
		if (strlen($drawingName) == 0 || $drawingFileSize == 0) {
			wfDebug('[client '.$_SERVER["REMOTE_ADDR"].']'.
					'[user '.$wgUser->getName().'] '.
					$fname.' received bad request [DrawingName='.$drawingName.']'.
					'[fileSize(DrawingData)='.$drawingFileSize.']'
			);
			header('HTTP/1.0 400 Bad Request');
			exit("\n\n"+'<html><body>DrawingName and DrawingData must be supplied.</body></html>');
		}

		// Verify filename
		# Chop off any directories in the given filename.
		$drawingName = wfBaseName($drawingName);
		$imageExtension = substr(strrchr($drawingName, '.'), 1);
		
		# Only allow filenames with known extensions
		$allowedExtensions = array('svg', 'svgz', 'png', 'jpg');
		if (! in_array($imageExtension, $allowedExtensions)) {
			wfDebug('[client '.$_SERVER["REMOTE_ADDR"].']'.
					'[user '.$wgUser->getName().'] '.
					$fname.' Received bad image extension [DrawingName='.$drawingName.']');
			header('HTTP/1.0 400 Bad Request');
			exit("\n\n"+'<html><body>DrawingName must have one of the following extensions: '.
					implode(',', $allowedExtensions).
				'.</body></html>');
		}

		/**
		 * Filter out illegal characters, and try to make a legible name
		 * out of it. We'll strip some silently that Title would die on.
		 */
		$filtered = preg_replace ( "/[^".Title::legalChars()."]|:/", '-', $drawingName );
		$nt = Title::newFromText( $filtered );
		if( is_null( $nt ) ) {
			wfDebug('[client '.$_SERVER["REMOTE_ADDR"].']'.
					'[user '.$wgUser->getName().'] '.
					$fname.' Received bad image name [DrawingName='.$drawingName.']');
			header('HTTP/1.0 400 Bad Request');
			exit("\n\n"+'<html><body>DrawingName must contain legible characters only.</body></html>');
		}
		$nt =& Title::makeTitle( NS_IMAGE, $nt->getDBkey() );
		$uploadSaveName = $nt->getDBkey();
		
		
		/**
		 * If the image is protected, non-sysop users won't be able
		 * to modify it by uploading a new revision.
		 */
		if( !$nt->userCanEdit() ) {
			wfDebug('[client '.$_SERVER["REMOTE_ADDR"].']'.
					'[user '.$wgUser->getName().'] '.
					$fname.' image is protected [DrawingName='.$drawingName.']');
			header('HTTP/1.0 403 Forbidden');
			exit("\n\n"+'<html><body>You are not allowed to edit this image.</body></html>');
		}

		/**
		 * In some cases we may forbid overwriting of existing files.
		 */
		if( !$this->userCanOverwrite($uploadSaveName) ) {
			wfDebug('[client '.$_SERVER["REMOTE_ADDR"].']'.
					'[user '.$wgUser->getName().'] '.
					$fname.' image may not be overwritten [DrawingName='.$drawingName.']');
			header('HTTP/1.0 403 Forbidden');
			exit("\n\n"+'<html><body>You are not allowed to overwrite this image.</body></html>');
		}
		
		/** Check if the image directory is writeable, this is a common mistake */
		if( !is_writeable( $wgUploadDirectory ) ) {
			header('HTTP/1.0 403 Forbidden');
			exit("\n\n"+'<html><body>The upload directory on the server is read only.</body></html>');
		}
		
		/**
		 * Upload the file into the temp directory, so that we can scrutinize its content
		 */
		$archive = wfImageArchiveDir( $uploadSaveName, 'temp' );
		
		/**
		 * Look at the contents of the file; if we can recognize the
		 * type but it's corrupt or data of the wrong type, we should
		 * probably not accept it.
		 */
		$veri = $this->verify( $drawingTempFile, $imageExtension );
		if( $veri !== true ) { 
			wfDebug('[client '.$_SERVER["REMOTE_ADDR"].']'.
					'[user '.$wgUser->getName().'] '.
					$fname.' image failed verification [DrawingName='.$drawingName.'][DrawingTempFile='.$drawingTempFile.']');
			unlink($drawingTempFile);
			header('HTTP/1.0 400 Bad Request');
			exit("\n\n"+'<html><body>The image data is corrupt.</body></html>');
		}

		/**
		 * Provide an opportunity for extensions to add further checks
		 */
		$error = '';
		if( !wfRunHooks( 'UploadVerification',
				array( $uploadSaveName, $drawingTempFile, &$error ) ) ) {
			wfDebug('[client '.$_SERVER["REMOTE_ADDR"].']'.
					'[user '.$wgUser->getName().'] '.
					$fname.' image failed extended verification [DrawingName='.$drawingName.']');
			unlink($drawingTempFile);
			header('HTTP/1.0 400 Bad Request');
			exit("\n\n"+'<html><body>The image data does not match the image name extension.</body></html>');
		}

	
		/**
		 * Try actually saving the thing...
		 * It will show an error form on failure.
		 */
		if( $this->saveUploadedFile( $uploadSaveName,
		                             $drawingTempFile,
		                             true ) ) {
			/**
			 * Update the upload log and create the description page
			 * if it's a new file.
			 */
			$img = Image::newFromName( $uploadSaveName );
			if ($drawingWidth != null) {
				$img->width = $drawingWidth;
			}
			if ($drawingHeight != null) {
				$img->height = $drawingHeight;
			}
			$this->mUploadDescription = $uploadSummary;

			$success = $img->recordUpload( $this->mUploadOldVersion,
			                                $this->mUploadDescription,
			                                $this->mLicense,
			                                $this->mUploadCopyStatus,
			                                $this->mUploadSource,
			                                $this->mWatchthis );
			                                
			/**
			 * Save the rendered image, if one was provided
			 */
			 if ($renderedTempFile != null && $drawingWidth != null)
			 {
				$thumbName = $img->thumbName($drawingWidth, $img->fromSharedDirectory );
				$thumbDir = wfImageThumbDir( $img->name, $img->fromSharedDirectory );
				$thumbPath = $thumbDir.'/'.$thumbName;
				wfDebug("we have a rendered image: ".$renderedTempFile.' width='.$drawingWidth.' height='.$drawingHeight.' thumbName='.$thumbPath );
				if (!file_exists(dirname($thumbPath))) {
					mkdir(dirname($thumbPath), 0777, true);
				}
				// Look at the contents of the file; if we can recognize the
				// type but it's corrupt or data of the wrong type, we should
				// probably not accept it.
				$veri = $this->verify( $renderedTempFile, 'png' );
				if( $veri !== true ) { 
					wfDebug('[client '.$_SERVER["REMOTE_ADDR"].']'.
						'[user '.$wgUser->getName().'] '.
						$fname.' rendered image failed verification [DrawingName='.$drawingName.'][RenderedTempFile='.$renderedTempFile.']');
					unlink($renderedTempFile);
				} else {
					move_uploaded_file($renderedTempFile, $thumbPath);
				}
			 } else {
			 	if ($renderedTempFile!= null) {
			 		unlink($renderedTempFile);
			 	}
			 }

			/**
			 * Save the image map, if one was provided
			 */
			 if ($imageMapTempFile != null && $drawingWidth != null)
			 {
				$thumbName = $img->thumbName($drawingWidth, $img->fromSharedDirectory );
				$thumbDir = wfImageThumbDir( $img->name, $img->fromSharedDirectory );
				$imageMapPath = $thumbDir.'/'.$thumbName.'.map';
				wfDebug("we have an image map: ".$imageMapTempFile);
				if (!file_exists(dirname($imageMapPath))) {
					mkdir(dirname($imageMapPath), 0777, true);
				}
				// Look at the contents of the file; if we can recognize the
				// type but it's corrupt or data of the wrong type, we should
				// probably not accept it.
				$hasScript = $this->detectScript( $imageMapTempFile, 'text/html', 'html' );
				if( $hasScript !== false ) { 
					wfDebug('[client '.$_SERVER["REMOTE_ADDR"].']'.
						'[user '.$wgUser->getName().'] '.
						$fname.' image map failed verification [DrawingName='.$drawingName.'][ImageMapTempFile='.$imageMapTempFile.']');
					unlink($imageMapTempFile);
				} else {
					move_uploaded_file($imageMapTempFile, $imageMapPath);
				}
			 } else {
			 	if ($imageMapTempFile!= null) {
			 		unlink($imageMapTempFile);
			 	}
			 }


			if ( $success ) {
				$this->showSuccess();
				wfRunHooks( 'UploadComplete', array( &$img ) );
			} else {
				// Image::recordUpload() fails if the image went missing, which is
				// unlikely, hence the lack of a specialised message
				$wgOut->showFileNotFoundError( $this->mUploadSaveName );
			}
		}
		if ($renderedTempFile!= null) {
			unlink($renderedTempFile);
	 	}
		if ($imageMapTempFile!= null) {
			unlink($imageMapTempFile);
	 	}
	}
	
	/** Downloads the specified image to the applet, and disallows caching by the browser.
	 * We need this function, because if we retrieve an image using the MediaWiki
	 * image URL, the image gets cached by the browser. This is very bad for editing,
	 * because we wan't to edit the newest version of the image only.
	 */
	function processDownload() {
		global $wgRequest;
	
		$name = $wgRequest->getVal("image","");
		$image = Image::newFromName($name);
		$imagePath = $image->getImagePath();
		if ($imagePath != null && file_exists($imagePath) && $filehandle=fopen($imagePath,'r')) {
			header('Last-Modified: '.date(DATE_RFC822, filectime($imagePath)));
			header('Cache-Control: no-cache');
			if ($image->getMimeType() == 'image/svg') {
				header('Content-Type: image/svg+xml');
			} else {
				header('Content-Type: '.$image->getMimeType());
			}
			header('Content-Length: '.filesize($imagePath));
			fpassthru($filehandle);
			fclose($filehandle);
			exit;
		} else {
			header('HTTP/1.0 404 Not Found');
			echo 'image '.$name.' not found'; // do we need to i18n this? It's never displayed to a user.
			exit;
		}
	}
	/**
	 * Show some text and linkage on successful upload.
	 * @access private
	 */
	function showSuccess() {
		header('HTTP/1.0 200 OK');
		exit;
	}

	/** I BORROWED THIS FUNCTION FROM SpecialUpload.php!! CHECK FOR EACH VERSION OF MEDIAWIKI, IF
	 *  THIS FUNCTION STILL MAKES SENSE!
	 *
	 * Move the uploaded file from its temporary location to the final
	 * destination. If a previous version of the file exists, move
	 * it into the archive subdirectory.
	 *
	 * @todo If the later save fails, we may have disappeared the original file.
	 *
	 * @param string $saveName
	 * @param string $tempName full path to the temporary file
	 * @param bool $useRename if true, doesn't check that the source file
	 *                        is a PHP-managed upload temporary
	 */
	function saveUploadedFile( $saveName, $tempName, $useRename = false ) {
		global $wgOut, $wgAllowCopyUploads;
		
		$fname= "SpecialUpload::saveUploadedFile";
		
		if ( !$useRename && $wgAllowCopyUploads && $this->mSourceType == 'web' ) {
			$useRename = true;
		}

		$dest = wfImageDir( $saveName );
		$archive = wfImageArchiveDir( $saveName );
		if ( !is_dir( $dest ) ) wfMkdirParents( $dest );
		if ( !is_dir( $archive ) ) wfMkdirParents( $archive );
		
		$this->mSavedFile = "{$dest}/{$saveName}";

		if( is_file( $this->mSavedFile ) ) {
			$this->mUploadOldVersion = gmdate( 'YmdHis' ) . "!{$saveName}";
			wfSuppressWarnings();
			$success = rename( $this->mSavedFile, "${archive}/{$this->mUploadOldVersion}" );
			wfRestoreWarnings();

			if( ! $success ) {
				$wgOut->showFileRenameError( $this->mSavedFile,
				  "${archive}/{$this->mUploadOldVersion}" );
				return false;
			}
			else wfDebug("$fname: moved file ".$this->mSavedFile." to ${archive}/{$this->mUploadOldVersion}\n");
		}
		else {
			$this->mUploadOldVersion = '';
		}

		wfSuppressWarnings();
		$success = $useRename
			? rename( $tempName, $this->mSavedFile )
			: move_uploaded_file( $tempName, $this->mSavedFile );
		wfRestoreWarnings();

		if( ! $success ) {
			$wgOut->showFileCopyError( $tempName, $this->mSavedFile );
			return false;
		} else {
			wfDebug("$fname: wrote tempfile $tempName to ".$this->mSavedFile."\n");
		}

		chmod( $this->mSavedFile, 0644 );
		return true;
	}
	
	function loadMessages() {
		static $messagesLoaded = false;
		global $wgMessageCache;
		if ( $messagesLoaded ) return;
		$messagesLoaded = true;

		require( dirname( __FILE__ ) . '/AnyWikiDraw.i18n.php' );
		foreach ( $messages as $lang => $msgs ) {
				$wgMessageCache->addMessages( $msgs, $lang );
		}
        return true;
	}

	/** I BORROWED THIS FUNCTION FROM SpecialUpload.php!! CHECK FOR EACH VERSION OF MEDIAWIKI, IF
	 *  THIS FUNCTION STILL MAKES SENSE!
	 *
	 * Check if there's an overwrite conflict and, if so, if restrictions
	 * forbid this user from performing the upload.
	 *
	 * @return true on success, false on failure
	 * @access private
	 */
	function userCanOverwrite( $name ) {
		$img = Image::newFromName( $name );
		if( is_null( $img ) ) {
			// Uh... this shouldn't happen ;)
			// But if it does, fall through to previous behavior
			return false;
		}

		if( $img->exists() ) {
			global $wgUser, $wgOut;
			if( $img->isLocal() ) {
				if( !$wgUser->isAllowed( 'reupload' ) ) {
					return false;
				}
			} else {
				if( !$wgUser->isAllowed( 'reupload' ) ||
				    !$wgUser->isAllowed( 'reupload-shared' ) ) {
				    return false;
				}
			}
		}

		// Rockin', go ahead and upload
		return true;
	}
	
	/**
	 * Verifies that it's ok to include the uploaded file
	 *
	 * @param string $tmpfile the full path of the temporary file to verify
	 * @param string $extension The filename extension that the file is to be served with
	 * @return mixed true of the file is verified, a WikiError object otherwise.
	 */
	function verify( $tmpfile, $extension ) {
		$fname= "AnyWikiDraw_body::verify";
		
		#magically determine mime type
		// BEGIN PATCH MediaWiki 1.7.1
		//$magic=& MimeMagic::singleton();
		//$mime= $magic->guessMimeType($tmpfile,false);
		$magic=& wfGetMimeMagic();
		$mime= $magic->guessMimeType($tmpfile,false);
		// END PATCH MediaWiki 1.7.1

		#check mime type, if desired
		global $wgVerifyMimeType;
		if ($wgVerifyMimeType) {

			#check mime type against file extension
			if( !$this->verifyExtension( $mime, $extension ) ) {
				//return new WikiErrorMsg( 'uploadcorrupt' );
				return false;
			}
			/*
			#check mime type blacklist
			global $wgMimeTypeBlacklist;
			if( isset($wgMimeTypeBlacklist) && !is_null($wgMimeTypeBlacklist)
				&& $this->checkFileExtension( $mime, $wgMimeTypeBlacklist ) ) {
				//return new WikiErrorMsg( 'badfiletype', htmlspecialchars( $mime ) );
				wfDebug($fname.' badfiletype');
				return false;
			}*/
		}

		#check for htmlish code and javascript
		if( $this->detectScript ( $tmpfile, $mime, $extension ) ) {
			//return new WikiErrorMsg( 'uploadscripted' );
				wfDebug($fname.' uploadscripted');
			return false;
		}

		/**
		* Scan the uploaded file for viruses
		*/
		$virus= $this->detectVirus($tmpfile);
		if ( $virus ) {
			//return new WikiErrorMsg( 'uploadvirus', htmlspecialchars($virus) );
				wfDebug($fname.' uploadvirus');
			return false;
		}

		//wfDebug( "$fname: all clear; passing.\n" );
		return true;
	}
	/** 
	 * Checks if the mime type of the uploaded file matches the file extension.
	 *
	 * @param string $mime the mime type of the uploaded file
	 * @param string $extension The filename extension that the file is to be served with
	 * @return bool
	 */
	function verifyExtension( $mime, $extension ) {
		return UploadForm::verifyExtension($mime, $extension);
	}
	/** Heuristig for detecting files that *could* contain JavaScript instructions or
	* things that may look like HTML to a browser and are thus
	* potentially harmful. The present implementation will produce false positives in some situations.
	*
	* @param string $file Pathname to the temporary upload file
	* @param string $mime The mime type of the file
	* @param string $extension The extension of the file
	* @return bool true if the file contains something looking like embedded scripts
	*/
	function detectScript($file, $mime, $extension) {
		return UploadForm::detectScript($file, $mime, $extension);
	}
	/** Generic wrapper function for a virus scanner program.
	* This relies on the $wgAntivirus and $wgAntivirusSetup variables.
	* $wgAntivirusRequired may be used to deny upload if the scan fails.
	*
	* @param string $file Pathname to the temporary upload file
	* @return mixed false if not virus is found, NULL if the scan fails or is disabled,
	*         or a string containing feedback from the virus scanner if a virus was found.
	*         If textual feedback is missing but a virus was found, this function returns true.
	*/
	function detectVirus($file) {
		return UploadForm::detectVirus($file);
	}
}
?>