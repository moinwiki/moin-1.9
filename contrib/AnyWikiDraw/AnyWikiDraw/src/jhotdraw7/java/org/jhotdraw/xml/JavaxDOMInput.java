/*
 * @(#)JavaxDOMInput.java
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
import javax.xml.XMLConstants;
import javax.xml.parsers.*;
import org.w3c.dom.*;
import java.io.*;
import java.awt.*;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
/**
 * DOMInput.
 * <p>
 * Design pattern:<br>
 * Name: Adapter.<br>
 * Role: Adapter.<br>
 * Partners: {@link org.w3c.dom.Document} as Adaptee.
 *
 * @author  Werner Randelshofer
 * @version $Id: JavaxDOMInput.java 527 2009-06-07 14:28:19Z rawcoder $
 */
public class JavaxDOMInput implements DOMInput {
    /**
     * This map is used to unmarshall references to objects to
     * the XML DOM. A key in this map is a String representing a marshalled
     * reference. A value in this map is an unmarshalled Object.
     */
    private HashMap<String,Object> idobjects = new HashMap<String,Object>();
    
    /**
     * The document used for input.
     */
    private Document document;
    /**
     * The current node used for input.
     */
    private Node current;
    
    /**
     * The factory used to create objects from XML tag names.
     */
    private DOMFactory factory;
    
    
    protected static DocumentBuilder documentBuilder;
    /**
     * Lazily create the document builder and keep a reference to it for
     * performance improvement.
     */
    protected static DocumentBuilder getBuilder() throws IOException {
        if (documentBuilder == null) {
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setNamespaceAware(true);
            factory.setValidating(false);
            factory.setXIncludeAware(false);
            try {
                factory.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
                documentBuilder = factory.newDocumentBuilder();
            } catch (Exception ex) {
                InternalError error = new InternalError("Unable to create DocumentBuilder");
                error.initCause(ex);
                throw error;
            }
        }
        return documentBuilder;
    }
    
    public JavaxDOMInput(DOMFactory factory, InputStream in) throws IOException {
        this.factory = factory;
        try {
            document = getBuilder().parse(in);
            current = document;
        } catch (SAXException ex) {
            IOException e = new IOException(ex.getMessage());
            e.initCause(ex);
            throw e;
        }
    }
    public JavaxDOMInput(DOMFactory factory, Reader in) throws IOException {
        this.factory = factory;
        try {
            document = getBuilder().parse(new InputSource(in));
            current = document;
        } catch (SAXException ex) {
            IOException e = new IOException(ex.getMessage());
            e.initCause(ex);
            throw e;
        }
    }
    
    /**
     * Returns the tag name of the current element.
     */
    public String getTagName() {
        return ((Element) current).getTagName();
    }
    /**
     * Gets an attribute of the current element of the DOM Document.
     */
    public String getAttribute(String name, String defaultValue) {
        String value = ((Element) current).getAttribute(name);
        return (value.length() == 0) ? defaultValue : value;
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
        if (current.getChildNodes().getLength() == 0) return defaultValue;
        
        StringBuilder buf = new StringBuilder();
        getText(current, buf);
        
        return buf.toString();
    }
    private static void getText(Node n, StringBuilder buf) {
        if (n.getNodeValue() != null) buf.append(n.getNodeValue());
        NodeList children = n.getChildNodes();
        for (int i=0; i < children.getLength(); i++) {
            getText(children.item(i), buf);
        }
    }
    /**
     * Gets an attribute of the current element of the DOM Document and of
     * all parent DOM elements.
     */
    public java.util.List<String> getInheritedAttribute(String name) {
        LinkedList<String> values = new LinkedList<String>();
        Node node = current;
        while (node != null) {
            String value = (String) ((Element) node).getAttribute(name);
            values.addFirst(value);
            node = node.getParentNode();
        }
        return values;
    }
    /**
     * Gets an attribute of the current element of the DOM Document.
     */
    public int getAttribute(String name, int defaultValue) {
        String value = ((Element) current).getAttribute(name);
        return (value.length() == 0) ? defaultValue : (int) Long.decode(value).intValue();
    }
    /**
     * Gets an attribute of the current element of the DOM Document.
     */
    public double getAttribute(String name, double defaultValue) {
        String value = ((Element) current).getAttribute(name);
        return (value.length() == 0) ? defaultValue : Double.parseDouble(value);
    }
    /**
     * Gets an attribute of the current element of the DOM Document.
     */
    public boolean getAttribute(String name, boolean defaultValue) {
        String value = ((Element) current).getAttribute(name);
        return (value.length() == 0) ? defaultValue : Boolean.valueOf(value).booleanValue();
    }
    
    
    /**
     * Returns the number of child elements of the current element.
     */
    public int getElementCount() {
        int count = 0;
        NodeList list = current.getChildNodes();
        for (int i=0; i < list.getLength(); i++) {
            Node node = list.item(i);
            if ((node instanceof Element)) {
                count++;
            }
        }
        return count;
    }
    /**
     * Returns the number of child elements with the specified tag name
     * of the current element.
     */
    public int getElementCount(String tagName) {
        int count = 0;
        NodeList list = current.getChildNodes();
        for (int i=0; i < list.getLength(); i++) {
            Node node = list.item(i);
            if ((node instanceof Element)
            && ((Element) node).getTagName().equals(tagName)) {
                count++;
            }
        }
        return count;
    }
    
    /**
     * Opens the element with the specified index and makes it the current node.
     */
    public void openElement(int index) {
        int count = 0;
        NodeList list = current.getChildNodes();
        int len = list.getLength();
        for (int i=0; i < len; i++) {
            Node node = list.item(i);
            if ((node instanceof Element)) {
                if (count++ == index) {
                    current = node;
                    return;
                }
            }
        }
    }
    
    /**
     * Opens the last element with the specified name and makes it the current node.
     */
    public void openElement(String tagName) {
        int count = 0;
        NodeList list = current.getChildNodes();
        int len = list.getLength();
        for (int i=0; i < len; i++) {
            Node node = list.item(i);
            if ((node instanceof Element)
            && ((Element) node).getTagName().equals(tagName)) {
                current = node;
                return;
            }
        }
        throw new IllegalArgumentException("element not found:"+tagName);
    }
    /**
     * Opens the element with the specified name and index and makes it the
     * current node.
     */
    public void openElement(String tagName, int index) {
        int count = 0;
        NodeList list = current.getChildNodes();
        int len = list.getLength();
        for (int i=0; i < len; i++) {
            Node node = list.item(i);
            if ((node instanceof Element)
            && ((Element) node).getTagName().equals(tagName)) {
                if (count++ == index) {
                    current = node;
                    return;
                }
            }
        }
        throw new IllegalArgumentException("no such child "+tagName+"["+index+"]");
    }
    
    /**
     * Closes the current element of the DOM Document.
     * The parent of the current element becomes the current element.
     * @exception IllegalArgumentException if the provided tagName does
     * not match the tag name of the element.
     */
    public void closeElement() {
        /*
        if (! ((Element) current).getTagName().equals(tagName)) {
            throw new IllegalArgumentException("Attempt to close wrong element:"+tagName +"!="+((Element) current).getTagName());
        }*/
        current = current.getParentNode();
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
}
