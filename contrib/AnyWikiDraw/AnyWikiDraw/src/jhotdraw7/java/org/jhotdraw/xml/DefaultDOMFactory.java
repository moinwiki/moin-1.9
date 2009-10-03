/*
 * @(#)DefaultDOMFactory.java
 *
 * Copyright (c) 1996-2006 by the original authors of JHotDraw
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

import java.util.*;
/**
 * {@code DefaultDOMFactory} can be used to serialize DOMStorable objects
 * in a DOM with the use of a mapping between Java class names and DOM element
 * names.
 *
 * @author Werner Randelshofer.
 * @version $Id: DefaultDOMFactory.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class DefaultDOMFactory implements DOMFactory {
    private final static HashMap<Class,String> classToNameMap = new HashMap<Class,String>();
    private final static HashMap<String,Object> nameToPrototypeMap = new HashMap<String,Object>();
    private final static HashMap<Class,String> enumClassToNameMap = new HashMap<Class,String>();
    private final static HashMap<String,Class> nameToEnumClassMap = new HashMap<String,Class>();
    private final static HashMap<Enum,String> enumToValueMap = new HashMap<Enum,String>();
    private final static HashMap<String,Set<Enum>> valueToEnumMap = new HashMap<String,Set<Enum>>();
    
    /** Creates a new instance. */
    public DefaultDOMFactory() {
    }
    
    /**
     * Adds a DOMStorable class to the DOMFactory.
     */
    public void addStorableClass(String name, Class c) {
        nameToPrototypeMap.put(name, c);
        classToNameMap.put(c, name);
    }
    /**
     * Adds a DOMStorable prototype to the DOMFactory.
     */
    public void addStorable(String name, DOMStorable prototype) {
        nameToPrototypeMap.put(name, prototype);
        classToNameMap.put(prototype.getClass(), name);
    }
    
    /**
     * Adds an Enum class to the DOMFactory.
     */
    public void addEnumClass(String name, Class c) {
        enumClassToNameMap.put(c, name);
        nameToEnumClassMap.put(name, c);
    }
    /**
     * Adds an Enum value to the DOMFactory.
     */
    public void addEnum(String value, Enum e) {
        enumToValueMap.put(e, value);
        Set<Enum> enums;
        if (valueToEnumMap.containsKey(value)) {
            enums = valueToEnumMap.get(value);
        } else {
            enums = new HashSet<Enum>();
            valueToEnumMap.put(value, enums);
        }
        enums.add(e);
    }
    
    /**
     * Creates a DOMStorable object.
     */
    public Object create(String name) {
        Object o = nameToPrototypeMap.get(name);
        if (o == null) {
            throw new IllegalArgumentException("Storable name not known to factory: "+name);
        }
        if (o instanceof Class) {
            try {
                return ((Class) o).newInstance();
            } catch (Exception e) {
                IllegalArgumentException error = new IllegalArgumentException("Storable class not instantiable by factory: "+name);
                error.initCause(e);
                throw error;
            }
        } else {
            try {
                return o.getClass().getMethod("clone", (Class[]) null).
                        invoke(o, (Object[]) null);
            } catch (Exception e) {
                IllegalArgumentException error =  new IllegalArgumentException("Storable prototype not cloneable by factory. Name: "+name);
                error.initCause(e);
                throw error;
            }
        }
    }
    
    public String getName(DOMStorable o) {
        String name = classToNameMap.get(o.getClass());
        if (name == null) {
            throw new IllegalArgumentException("Storable class not known to factory. Storable:"+o+" Factory:"+this.getClass());
        }
        return name;
    }
    
    public String getEnumName(Enum e) {
        String name = enumClassToNameMap.get(e.getClass());
        if (name == null) {
            throw new IllegalArgumentException("Enum class not known to factory:"+e.getClass());
        }
        return name;
    }
    
    public String getEnumValue(Enum e) {
        return (enumToValueMap.containsKey(e)) ? enumToValueMap.get(e) : e.toString();
    }
    
    @SuppressWarnings("unchecked")
    public Enum createEnum(String name, String value) {
        Class enumClass = nameToEnumClassMap.get(name);
        if (enumClass == null) {
            throw new IllegalArgumentException("Enum name not known to factory:"+name);
        }
        Set<Enum> enums = valueToEnumMap.get(value);
        if (enums == null) {
            return Enum.valueOf(enumClass, value);
        }
        for (Enum e : enums) {
            if (e.getClass() == enumClass) {
                return e;
            }
        }
        throw new IllegalArgumentException("Enum value not known to factory:"+value);
    }
}
