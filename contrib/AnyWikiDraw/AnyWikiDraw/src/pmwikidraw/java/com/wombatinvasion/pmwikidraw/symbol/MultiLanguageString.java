/*
 * Created on 30-Dec-2004
 */
package com.wombatinvasion.pmwikidraw.symbol;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Locale;

/**
 * @author bob
 */
public class MultiLanguageString {

	private HashMap strings = new HashMap();
	/**
	 * 
	 */
	public MultiLanguageString(String defaultValue) {
		strings.put(null, defaultValue);
	}
	
	/**
	 * 
	 */
	public MultiLanguageString() {
	}

	public void addString(String language, String value) {
		strings.put(language, value);
	}
	
	public String toString() {
		return getLocaleString();
	}
	
	public String toStringDebug() {
		StringBuffer result = new StringBuffer();
		Iterator it = strings.keySet().iterator();
		while(it.hasNext()) {
			String language = (String) it.next();
			String value = (String)strings.get(language);
			result.append(language+": "+value+"\n");
		}
		return result.toString();
	}

	//TODO: This is quite breakable, we should either a) ensure there will always be a null entry
	// or if no null entry just return something and ensure there is *always* something even
	// if it is 'undefined'
	public String getLocaleString(String localeLanguage) {
		if(strings.containsKey(localeLanguage)) { // If we can find the default locale language then use it.
			return (String)strings.get(localeLanguage);
		}
		else { 
			if(strings.containsKey(null)) {// Otherwise return the default...hopefully there will be one :)
				return (String)strings.get(null); 
			} else if(strings.size()==0){
				return ""; 
			} else { // Last fallover point, return something, whatever there is.
				Iterator it = strings.keySet().iterator();
				return (String)strings.get(it.next());
			}
		}
		
	}
	public String getLocaleString() {
		return getLocaleString(Locale.getDefault().getLanguage());
	}
	
}
