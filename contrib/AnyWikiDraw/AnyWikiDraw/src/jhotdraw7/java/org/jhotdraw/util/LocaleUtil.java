/*
 * @(#)LocaleUtil.java
 *
 * Copyright (c) 1996-2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 *
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */

package org.jhotdraw.util;

import java.util.*;
/**
 * LocaleUtil provides a setDefault()/getDefault() wrapper to java.util.Locale
 * in order to overcome the security restriction preventing Applets from using
 * their own locale.
 *
 * @author Werner Randelshofer
 * @version $Id: LocaleUtil.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class LocaleUtil {
    private static Locale defaultLocale;
    
    /** Creates a new instance. */
    public LocaleUtil() {
    }
    
    public static void setDefault(Locale newValue) {
        defaultLocale = newValue;
    }
    public static Locale getDefault() {
        return (defaultLocale == null) ? Locale.getDefault() : defaultLocale;
    }
}
