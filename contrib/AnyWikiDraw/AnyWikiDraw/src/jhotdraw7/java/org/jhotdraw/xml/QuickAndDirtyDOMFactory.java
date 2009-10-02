/*
 * @(#)QuickAndDirtyDOMFactory.java
 * 
 * Copyright (c) 2009 by the original authors of JHotDraw
 * and all its contributors.
 * All rights reserved.
 * 
 * The copyright of this software is owned by the authors and  
 * contributors of the JHotDraw project ("the copyright holders").  
 * You may not use, copy or modify this software, except in  
 * accordance with the license agreement you entered into with  
 * the copyright holders. For details see accompanying license terms. 
 */
package org.jhotdraw.xml;

import java.util.regex.Matcher;

/**
 * {@code QuickAndDirtyDOMFactory} can be used to serialize DOMStorable
 * objects in a DOM with the unmapped use of Java class names as DOM element
 * names.
 * <p>
 * For example, if a DOMStorable object has the class name com.example.MyClass,
 * then the DOM element has the same name, that is: &lt;com.example.MyClass&gt;.
 * <p>
 * Since no mapping between DOM element names and Java class names is performed,
 * DOM's generated with QuickAndDirtyDOMFactory are not suited for long-term
 * storage of objects. A DOM element can not be read back into DOMStorable
 * object, if the class name of a DOMStorable object has changed.
 *
 * @author Werner Randelshofer
 * @version $Id: QuickAndDirtyDOMFactory.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class QuickAndDirtyDOMFactory implements DOMFactory {

    private String escape(String name) {
        // Escape dollar characters by two full-stop characters
        name = name.replaceAll("\\$", "..");
        return name;

    }

    private String unescape(String name) {
        // Unescape dollar characters from two full-stop characters
        name = name.replaceAll("\\.\\.", Matcher.quoteReplacement("$"));
        return name;
    }

    public String getName(DOMStorable o) {
        return escape(o.getClass().getName());
    }

    public Object create(String name) {
        name = unescape(name);

        try {
            return Class.forName(name).newInstance();
        } catch (InstantiationException ex) {
            IllegalArgumentException e = new IllegalArgumentException("Class " + name + " can not instantiate an object");
            e.initCause(ex);
            throw e;
        } catch (IllegalAccessException ex) {
            IllegalArgumentException e = new IllegalArgumentException("Class " + name + " is not public");
            e.initCause(ex);
            throw e;
        } catch (ClassNotFoundException ex) {
            IllegalArgumentException e = new IllegalArgumentException("Class " + name + " does not exist");
            e.initCause(ex);
            throw e;
        }
    }

    public String getEnumName(Enum o) {
        return escape(o.getClass().getName());
    }

    public String getEnumValue(Enum o) {
        return o.name();
    }

    @SuppressWarnings("unchecked")
    public Enum createEnum(String name, String value) {
        name = unescape(name);

        Class enumClass;
        try {
            enumClass = Class.forName(name);
        } catch (ClassNotFoundException ex) {
            throw new IllegalArgumentException("Enum name not known to factory:" + name);
        }
        if (enumClass == null) {
            throw new IllegalArgumentException("Enum name not known to factory:" + name);
        }
        return Enum.valueOf(enumClass, value);
//        throw new IllegalArgumentException("Enum value not known to factory:"+value);
    }
}
