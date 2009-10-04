/*
 * @(#)NanoXMLDOMInput.java
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

package org.jhotdraw.xml;

import java.util.*;
import java.io.*;
import java.awt.*;
import net.n3.nanoxml.*;
import org.jhotdraw.beans.Disposable;
/**
 * NanoXMLDOMInput.
 * <p>
 * Design pattern:<br>
 * Name: Adapter.<br>
 * Role: Adapter.<br>
 * Partners: {@link net.n3.nanoxml.XMLElement} as Adaptee.
 *
 * @author  Werner Randelshofer
 * @version $Id: NanoXMLDOMInput.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class NanoXMLDOMInput implements DOMInput, Disposable {
    /**
     * This map is used to unmarshall references to objects to
     * the XML DOM. A key in this map is a String representing a marshalled
     * reference. A value in this map is an unmarshalled Object.
     */
    private HashMap<String,Object> idobjects = new HashMap<String,Object>();
    
    /**
     * The document used for input.
     */
    private XMLElement document;
    /**
     * The current node used for input.
     */
    private XMLElement current;
    
    /**
     * The factory used to create objects from XML tag names.
     */
    private DOMFactory factory;
    
    /**
     * The stack.
     */
    private Stack<XMLElement> stack = new Stack<XMLElement>();
    
    public NanoXMLDOMInput(DOMFactory factory, InputStream in) throws IOException {
        this(factory, new InputStreamReader(in, "UTF8"));
    }
    public NanoXMLDOMInput(DOMFactory factory, Reader in) throws IOException {
        this.factory = factory;
        
        try {
            
            IXMLParser parser = XMLParserFactory.createDefaultXMLParser();
            IXMLReader reader = new StdXMLReader(in);
            parser.setReader(reader);
            document = new XMLElement();
            current = (XMLElement) parser.parse();
            if (current != null) {
            document.addChild(current);
            }
            current = document;
        } catch (Exception e) {
            IOException error = new IOException(e.getMessage());
            error.initCause(e);
            throw error;
        }
    }
    
    /**
     * Returns the tag name of the current element.
     */
    public String getTagName() {
        return current.getName();
    }
    /**
     * Gets an attribute of the current element of the DOM Document.
     */
    public String getAttribute(String name, String defaultValue) {
        String value = (String) current.getAttribute(name);
        return (value == null || value.length() == 0) ? defaultValue : value;
    }
    /**
     * Gets an attribute of the current element of the DOM Document and of
     * all parent DOM elements.
     */
    public java.util.List<String> getInheritedAttribute(String name) {
        LinkedList<String> values = new LinkedList<String>();
        for (XMLElement node: stack) {
            String value = (String) node.getAttribute(name);
            values.add(value);
        }
        String value = (String) current.getAttribute(name);
        values.add(value);
        return values;
    }
    /**
     * Gets the text of the current element of the DOM Document.
     */
    public String getText() {
        return getText(null);
    }
    /**
     * Gets the text of the current element of the DOM Document.
     */
    public String getText(String defaultValue) {
        String value = current.getContent();
        return (value == null) ? defaultValue : value;
    }
    /**
     * Gets an attribute of the current element of the DOM Document.
     */
    public int getAttribute(String name, int defaultValue) {
        String value = (String) current.getAttribute(name);
        return (value == null || value.length() == 0) ? defaultValue : (int) Long.decode(value).intValue();
    }
    /**
     * Gets an attribute of the current element of the DOM Document.
     */
    public double getAttribute(String name, double defaultValue) {
        String value = (String) current.getAttribute(name);
        return (value == null || value.length() == 0) ? defaultValue : Double.parseDouble(value);
    }
    /**
     * Gets an attribute of the current element of the DOM Document.
     */
    public boolean getAttribute(String name, boolean defaultValue) {
        String value = (String) current.getAttribute(name);
        return (value == null || value.length() == 0) ? defaultValue : Boolean.valueOf(value).booleanValue();
    }
    
    
    /**
     * Returns the number of child elements of the current element.
     */
    public int getElementCount() {
        return current.getChildrenCount();
    }
    /**
     * Returns the number of child elements with the specified tag name
     * of the current element.
     */
    public int getElementCount(String tagName) {
        int count = 0;
        ArrayList list = current.getChildren();
        for (int i=0; i < list.size(); i++) {
            XMLElement node = (XMLElement) list.get(i);
            if (node.getName().equals(tagName)) {
                count++;
            }
        }
        return count;
    }
    
    /**
     * Opens the element with the specified index and makes it the current node.
     */
    public void openElement(int index) {
        stack.push(current);
        ArrayList list = current.getChildren();
        current = (XMLElement) list.get(index);
    }
    
    /**
     * Opens the last element with the specified name and makes it the current node.
     */
    public void openElement(String tagName) throws IOException {
        ArrayList list = current.getChildren();
        for (int i=0; i < list.size(); i++) {
            XMLElement node = (XMLElement) list.get(i);
            if (node.getName().equals(tagName)) {
                stack.push(current);
                current = node;
                return;
            }
        }
        throw new IOException("no such element:"+tagName);
    }
    /**
     * Opens the element with the specified name and index and makes it the
     * current node.
     */
    public void openElement(String tagName, int index) throws IOException {
        int count = 0;
        ArrayList list = current.getChildren();
        for (int i=0; i < list.size(); i++) {
            XMLElement node = (XMLElement) list.get(i);
            if (node.getName().equals(tagName)) {
                if (count++ == index) {
                    stack.push(current);
                    current = node;
                    return;
                }
            }
        }
        throw new IOException("no such element:"+tagName+" at index:"+index);
    }
    
    /**
     * Closes the current element of the DOM Document.
     * The parent of the current element becomes the current element.
     * @exception IllegalArgumentException if the provided tagName does
     * not match the tag name of the element.
     */
    public void closeElement() {
        current = (XMLElement) stack.pop();
    }
    
    /**
     * Reads an object from the current element.
     */
    public Object readObject() throws IOException {
        return readObject(0);
    }
    /**
     * Reads an object from the current element.
     */
    public Object readObject(int index) throws IOException {
        openElement(index);
        Object o;
        
        String tagName = getTagName();
        if (tagName.equals("null")) {
            o =  null;
        } else if (tagName.equals("string")) {
            o = getText();
        } else if (tagName.equals("int")) {
            o = Integer.decode(getText());
        } else if (tagName.equals("long")) {
            o = Long.decode(getText());
        } else if (tagName.equals("float")) {
            o = new Float(Float.parseFloat(getText()));
        } else if (tagName.equals("double")) {
            o = new Double(Double.parseDouble(getText()));
        } else if (tagName.equals("boolean")) {
            o = Boolean.valueOf(getText());
        } else if (tagName.equals("color")) {
            o = new Color(getAttribute("rgba",0xff));
        } else if (tagName.equals("intArray")) {
            int[] a = new int[getElementCount()];
            for (int i=0; i < a.length; i++) {
                a[i] = ((Integer) readObject(i)).intValue();
            }
            o = a;
        } else if (tagName.equals("floatArray")) {
            float[] a = new float[getElementCount()];
            for (int i=0; i < a.length; i++) {
                a[i] = ((Float) readObject(i)).floatValue();
            }
            o = a;
        } else if (tagName.equals("doubleArray")) {
            double[] a = new double[getElementCount()];
            for (int i=0; i < a.length; i++) {
                a[i] = ((Double) readObject(i)).doubleValue();
            }
            o = a;
        } else if (tagName.equals("font")) {
            o = new Font(getAttribute("name", "Dialog"), getAttribute("style", 0), getAttribute("size", 0));
        } else if (tagName.equals("enum")) {
            o = factory.createEnum(getAttribute("type",(String)null), getText());
        } else {
            String ref = getAttribute("ref", null);
            String id = getAttribute("id", ref);
            
            // Keep track of objects which have an ID
            if (id == null) {
                o = factory.create(getTagName());
            } else if (idobjects.containsKey(id)) {
                o = idobjects.get(id);
            } else {
                o = factory.create(getTagName());
                idobjects.put(id, o);
            }
            
            if (ref == null) {
                if (o instanceof DOMStorable) {
                    ((DOMStorable) o).read(this);
                }
            }
        }
        
        closeElement();
        return o;
    }

    public void dispose() {
        if (document != null) {
            document.dispose();
            document = null;
        }
    }
}
