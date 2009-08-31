/*
 * @(#)StyleManager.java
 *
 * Copyright (c) 1996-2007 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 *
 * Original code taken from article "Swing and CSS" by Joshua Marinacci 10/14/2003
 * http://today.java.net/pub/a/today/2003/10/14/swingcss.html
 */

package org.jhotdraw.xml.css;

import java.util.*;
import net.n3.nanoxml.*;
import org.jhotdraw.util.ReversedList;
import org.w3c.dom.Element;
/**
 * StyleManager applies styling Rules to an XML DOM.
 * This class supports net.n3.nanoxml as well as org.w3c.dom.
 * 
 * @author Werner Randelshofer
 * @version $Id: StyleManager.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class StyleManager {
    private java.util.List<CSSRule> rules;
    
    public StyleManager() {
        rules = new ArrayList<CSSRule>();
    }
    
    public void add(CSSRule rule) {
        rules.add(rule);
    }
    
    public void applyStylesTo(Element elem) {
        for (CSSRule rule : rules) {
            if(rule.matches(elem)) {
                rule.apply(elem);
            }
        }
    }
    public void applyStylesTo(IXMLElement elem) {
        for (CSSRule rule : new ReversedList<CSSRule>(rules)) {
            if(rule.matches(elem)) {
                //System.out.println("StyleManager applying "+rule+" to "+elem);
                rule.apply(elem);
            }
        }
    }

    public void clear() {
        rules.clear();
    }
}
