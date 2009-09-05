/*
 * Created on 14-Nov-2004
 *
 * TODO To change the template for this generated file go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
package com.wombatinvasion.pmwikidraw;

import java.io.UnsupportedEncodingException;
import java.net.URLDecoder;
import java.net.URLEncoder;

/**
 * @author Ciaran Jessup
 *
 * TODO To change the template for this generated type comment go to
 * Window - Preferences - Java - Code Style - Code Templates
 */
public class PmWikiDrawURLEncoder {

	/**
	 * @param arg0
	 * @return
	 */
	public static String decode(String url) {
		String decodedUrl = URLDecoder.decode(url);
		//when reading map add $ScriptUrl to map-hrefs if they not start wih "$", "/" or "http:"
		if(decodedUrl.charAt(0)!='$' && decodedUrl.charAt(0)!='/' && ( !decodedUrl.toUpperCase().startsWith("HTTP://") ) ) {
			decodedUrl = "$scripturl?pagename="+decodedUrl;
		}
		return decodedUrl;
	}

}
